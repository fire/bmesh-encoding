#!/usr/bin/env python3
"""
Test EXT_bmesh_encoding integration within Blender environment.
This script should be run from within Blender's Python console.
"""

import bpy
import sys
import os
import json


def setup_test_scene():
    """Set up a test scene with a mesh that has quads/ngons."""
    print("🔧 Setting up test scene...")

    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create a cube (has quads by default)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object

    # Add some ngon faces by extruding
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, 1)}
    )
    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"✅ Created test mesh: {cube.name}")
    print(f"   Vertices: {len(cube.data.vertices)}")
    print(f"   Faces: {len(cube.data.polygons)}")

    # Check face types
    quad_count = sum(1 for p in cube.data.polygons if len(p.vertices) == 4)
    ngon_count = sum(1 for p in cube.data.polygons if len(p.vertices) > 4)
    tri_count = sum(1 for p in cube.data.polygons if len(p.vertices) == 3)

    print(f"   Quads: {quad_count}, Ngons: {ngon_count}, Tris: {tri_count}")

    return cube


def test_addon_registration():
    """Test if EXT_bmesh_encoding addon is properly registered."""
    print("\n🔍 Testing addon registration...")

    # Check if addon is loaded
    addon_name = "ext_bmesh_encoding"

    if addon_name in bpy.context.preferences.addons:
        print("✅ EXT_bmesh_encoding addon is loaded")
        addon = bpy.context.preferences.addons[addon_name]
        print(f"   Module: {addon.module}")
        return True
    else:
        print("❌ EXT_bmesh_encoding addon is not loaded")
        print("   Please install and enable the addon first")
        return False


def test_gltf_exporter_availability():
    """Test if glTF exporter is available."""
    print("\n🔍 Testing glTF exporter availability...")

    try:
        # Check if glTF exporter operator exists
        if hasattr(bpy.ops, 'export_scene') and hasattr(bpy.ops.export_scene, 'gltf'):
            print("✅ glTF exporter is available")
            return True
        else:
            print("❌ glTF exporter not found")
            return False
    except Exception as e:
        print(f"❌ Error checking glTF exporter: {e}")
        return False


def test_extension_hook_discovery():
    """Test if EXT_bmesh_encoding extension hooks are discoverable."""
    print("\n🔍 Testing extension hook discovery...")

    try:
        # Try to import the extension module
        import ext_bmesh_encoding.gltf_extension as gltf_ext
        print("✅ Successfully imported gltf_extension module")

        # Check for extension classes
        has_import_ext = hasattr(gltf_ext, 'glTF2ImportUserExtension')
        has_export_ext = hasattr(gltf_ext, 'glTF2ExportUserExtension')

        print(f"   glTF2ImportUserExtension: {'✅' if has_import_ext else '❌'}")
        print(f"   glTF2ExportUserExtension: {'✅' if has_export_ext else '❌'}")

        if has_export_ext:
            # Test instantiation
            export_ext = gltf_ext.glTF2ExportUserExtension()
            print("✅ Successfully instantiated glTF2ExportUserExtension")

            # Check for hook method
            has_hook = hasattr(export_ext, 'gather_gltf_hook')
            print(f"   gather_gltf_hook method: {'✅' if has_hook else '❌'}")

            if has_hook:
                # Get method signature
                import inspect
                sig = inspect.signature(export_ext.gather_gltf_hook)
                print(f"   Hook signature: {sig}")
                return True

        return False

    except ImportError as e:
        print(f"❌ Failed to import gltf_extension: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing extension hooks: {e}")
        return False


def test_gltf_export_with_extension():
    """Test actual glTF export with EXT_bmesh_encoding."""
    print("\n🔍 Testing glTF export with EXT_bmesh_encoding...")

    try:
        # Set up export path
        export_path = os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd(),
                                 "test_blender_export.gltf")

        print(f"📤 Exporting to: {export_path}")

        # Configure export settings
        export_settings = {
            'filepath': export_path,
            'export_format': 'GLTF_SEPARATE',
            'export_yup': True,
            'export_apply': True,
            'export_extras': True,
            'export_extensions': True,  # This should enable extensions
        }

        # Perform export
        bpy.ops.export_scene.gltf(**export_settings)

        print("✅ glTF export completed")

        # Check if file was created
        if os.path.exists(export_path):
            print(f"✅ Export file created: {export_path}")

            # Read and validate the exported file
            with open(export_path, 'r', encoding='utf-8') as f:
                gltf_data = json.load(f)

            # Check for extensions
            if 'extensions' in gltf_data:
                extensions = gltf_data['extensions']
                print(f"📋 Found extensions in export: {list(extensions.keys())}")

                if 'EXT_bmesh_encoding' in extensions:
                    print("🎉 EXT_bmesh_encoding found in exported glTF!")
                    ext_data = extensions['EXT_bmesh_encoding']
                    components = list(ext_data.keys())
                    print(f"   Components: {components}")

                    # Check for required components
                    required = ['vertices', 'edges', 'loops', 'faces']
                    found = [comp for comp in required if comp in ext_data]
                    print(f"   Required components found: {found}")

                    if len(found) == len(required):
                        print("✅ All required EXT_bmesh_encoding components present!")
                        return True
                    else:
                        missing = [comp for comp in required if comp not in ext_data]
                        print(f"❌ Missing components: {missing}")
                        return False
                else:
                    print("❌ EXT_bmesh_encoding not found in exported glTF")
                    print("   This indicates the extension hooks are not being called")
                    return False
            else:
                print("❌ No extensions found in exported glTF")
                print("   This indicates no extensions were processed during export")
                return False
        else:
            print(f"❌ Export file not created: {export_path}")
            return False

    except Exception as e:
        print(f"❌ Error during glTF export test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_addon_ui():
    """Test if addon UI elements are available."""
    print("\n🔍 Testing addon UI elements...")

    try:
        # Check for addon preferences
        if hasattr(bpy.context.scene, 'enable_ext_bmesh_encoding'):
            current_value = bpy.context.scene.enable_ext_bmesh_encoding
            print(f"✅ Addon UI property found: enable_ext_bmesh_encoding = {current_value}")
            return True
        else:
            print("❌ Addon UI property not found")
            print("   enable_ext_bmesh_encoding property missing from Scene")
            return False
    except Exception as e:
        print(f"❌ Error testing addon UI: {e}")
        return False


def main():
    """Run all integration tests."""
    print("EXT_bmesh_encoding Blender Integration Test")
    print("=" * 50)
    print("This test verifies the complete addon integration within Blender")
    print("=" * 50)

    # Run all tests
    scene_setup = setup_test_scene()
    addon_reg = test_addon_registration()
    exporter_avail = test_gltf_exporter_availability()
    hook_discovery = test_extension_hook_discovery()
    export_test = test_gltf_export_with_extension()
    ui_test = test_addon_ui()

    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY:")
    print(f"Scene Setup:      {'✅ PASS' if scene_setup else '❌ FAIL'}")
    print(f"Addon Registration: {'✅ PASS' if addon_reg else '❌ FAIL'}")
    print(f"Exporter Available: {'✅ PASS' if exporter_avail else '❌ FAIL'}")
    print(f"Hook Discovery:   {'✅ PASS' if hook_discovery else '❌ FAIL'}")
    print(f"Export Test:      {'✅ PASS' if export_test else '❌ FAIL'}")
    print(f"UI Test:          {'✅ PASS' if ui_test else '❌ FAIL'}")

    all_passed = all([scene_setup, addon_reg, exporter_avail, hook_discovery, export_test, ui_test])

    if all_passed:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("   EXT_bmesh_encoding is working correctly in Blender")
        print("   glTF exports should contain EXT_bmesh_encoding data")
    else:
        print("\n❌ SOME INTEGRATION TESTS FAILED")
        print("   EXT_bmesh_encoding integration has issues:")

        if not addon_reg:
            print("   • Addon is not properly installed/enabled")
        if not exporter_avail:
            print("   • glTF exporter is not available")
        if not hook_discovery:
            print("   • Extension hooks are not discoverable")
        if not export_test:
            print("   • Extension hooks are not being called during export")
        if not ui_test:
            print("   • Addon UI is not properly registered")

        print("\n🔧 Troubleshooting steps:")
        print("   1. Ensure addon is installed and enabled in Blender preferences")
        print("   2. Check Blender console for error messages during addon loading")
        print("   3. Verify glTF-Blender-IO addon is enabled")
        print("   4. Try restarting Blender after installing the addon")
        print("   5. Check addon loading order in Blender preferences")

    return all_passed


if __name__ == "__main__":
    # This script is designed to be run from within Blender
    print("This script should be run from within Blender's Python console.")
    print("Copy and paste the contents into Blender's Text Editor and run it there.")
    print("\nAlternatively, save this as a .py file and run:")
    print("blender --background --python /path/to/this/script.py")

    success = main()
    sys.exit(0 if success else 1)
