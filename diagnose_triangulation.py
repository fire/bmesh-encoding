#!/usr/bin/env python3
"""
Diagnostic script to identify why tests aren't detecting triangulation issues.
This script checks the addon state and runs targeted tests.
"""

import bpy
import os
import sys
import json
import tempfile
from pathlib import Path


def diagnose_addon_state():
    """Diagnose the current state of the EXT_bmesh_encoding addon."""
    print("🔍 Diagnosing EXT_bmesh_encoding addon state...")
    print("=" * 50)

    # Check if addon is loaded
    addon_name = "ext_bmesh_encoding"
    addon_loaded = addon_name in bpy.context.preferences.addons

    print(f"📦 Addon loaded: {'✅' if addon_loaded else '❌'} {addon_name}")

    if addon_loaded:
        addon = bpy.context.preferences.addons[addon_name]
        print(f"   Module: {addon.module}")
        print(f"   Path: {addon.module_path if hasattr(addon, 'module_path') else 'Unknown'}")

    # Check for extension classes
    try:
        import ext_bmesh_encoding.gltf_extension as gltf_ext
        print("✅ gltf_extension module imported successfully")

        has_import_ext = hasattr(gltf_ext, 'glTF2ImportUserExtension')
        has_export_ext = hasattr(gltf_ext, 'glTF2ExportUserExtension')

        print(f"   glTF2ImportUserExtension: {'✅' if has_import_ext else '❌'}")
        print(f"   glTF2ExportUserExtension: {'✅' if has_export_ext else '❌'}")

        if has_export_ext:
            export_ext = gltf_ext.glTF2ExportUserExtension()
            has_hook = hasattr(export_ext, 'gather_gltf_hook')
            print(f"   gather_gltf_hook method: {'✅' if has_hook else '❌'}")

    except ImportError as e:
        print(f"❌ Failed to import gltf_extension: {e}")
        return False

    # Check UI property
    has_ui_prop = hasattr(bpy.context.scene, 'enable_ext_bmesh_encoding')
    print(f"🎛️  UI property (enable_ext_bmesh_encoding): {'✅' if has_ui_prop else '❌'}")

    if has_ui_prop:
        current_value = bpy.context.scene.enable_ext_bmesh_encoding
        print(f"   Current value: {current_value}")

    return addon_loaded


def create_minimal_test_mesh():
    """Create a minimal test mesh with known quad topology."""
    print("\n🔧 Creating minimal test mesh...")

    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create a simple quad plane
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    plane = bpy.context.active_object

    # Analyze topology
    mesh = plane.data
    tri_count = sum(1 for poly in mesh.polygons if len(poly.vertices) == 3)
    quad_count = sum(1 for poly in mesh.polygons if len(poly.vertices) == 4)
    ngon_count = sum(1 for poly in mesh.polygons if len(poly.vertices) > 4)

    print("📊 Minimal test mesh topology:")
    print(f"   Triangles: {tri_count}")
    print(f"   Quads: {quad_count}")
    print(f"   Ngons: {ngon_count}")
    print(f"   Total faces: {len(mesh.polygons)}")

    expected_quads = 1
    if quad_count != expected_quads:
        print(f"⚠️  Expected {expected_quads} quad, got {quad_count}")
        return None

    print("✅ Minimal test mesh created successfully")
    return plane


def test_gltf_roundtrip():
    """Test a complete glTF export/import roundtrip."""
    print("\n🔄 Testing glTF roundtrip...")
    print("-" * 30)

    # Create test mesh
    original_obj = create_minimal_test_mesh()
    if not original_obj:
        print("❌ Failed to create test mesh")
        return False

    # Analyze original topology
    orig_mesh = original_obj.data
    orig_quads = sum(1 for poly in orig_mesh.polygons if len(poly.vertices) == 4)
    orig_tris = sum(1 for poly in orig_mesh.polygons if len(poly.vertices) == 3)

    print(f"📊 Original: {orig_tris} tris, {orig_quads} quads")

    # Export to glTF
    with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as temp_file:
        export_path = temp_file.name

    print(f"📤 Exporting to: {export_path}")

    try:
        # Select and export
        bpy.ops.object.select_all(action='DESELECT')
        original_obj.select_set(True)
        bpy.context.view_layer.objects.active = original_obj

        bpy.ops.export_scene.gltf(
            filepath=export_path,
            export_format='GLTF_SEPARATE',
            export_yup=True,
            export_apply=True,
            export_extras=True,
            use_selection=True
        )

        if not os.path.exists(export_path):
            print("❌ Export failed - file not created")
            return False

        print("✅ Export completed")

        # Check for EXT_bmesh_encoding in exported file
        with open(export_path, 'r', encoding='utf-8') as f:
            gltf_data = json.load(f)

        has_extensions = 'extensions' in gltf_data
        has_ext_bmesh = has_extensions and 'EXT_bmesh_encoding' in gltf_data['extensions']

        print(f"📋 EXT_bmesh_encoding in export: {'✅' if has_ext_bmesh else '❌'}")

        if has_ext_bmesh:
            ext_data = gltf_data['extensions']['EXT_bmesh_encoding']
            components = list(ext_data.keys())
            print(f"   Components: {components}")

        # Import back
        print("📥 Importing glTF back...")

        # Track existing objects
        before_import = set(bpy.data.objects)

        bpy.ops.import_scene.gltf(filepath=export_path)

        # Find imported object
        after_import = set(bpy.data.objects)
        new_objects = after_import - before_import

        if not new_objects:
            print("❌ Import failed - no new objects")
            return False

        imported_obj = list(new_objects)[0]
        print(f"✅ Import completed: {imported_obj.name}")

        # Analyze imported topology
        imp_mesh = imported_obj.data
        imp_quads = sum(1 for poly in imp_mesh.polygons if len(poly.vertices) == 4)
        imp_tris = sum(1 for poly in imp_mesh.polygons if len(poly.vertices) == 3)

        print(f"📊 Imported: {imp_tris} tris, {imp_quads} quads")

        # Compare topologies
        topology_preserved = (orig_quads == imp_quads and orig_tris == imp_tris)

        print(f"🎯 Topology preserved: {'✅' if topology_preserved else '❌'}")

        if not topology_preserved:
            print("   ❌ TRIANGULATION DETECTED!")
            print(f"   Original: {orig_tris} tris, {orig_quads} quads")
            print(f"   Imported: {imp_tris} tris, {imp_quads} quads")

            if imp_quads < orig_quads:
                lost_quads = orig_quads - imp_quads
                print(f"   📉 Lost {lost_quads} quad(s) - triangulated to {imp_tris} tris")

        # Cleanup
        os.unlink(export_path)

        return topology_preserved

    except Exception as e:
        print(f"❌ Roundtrip test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def diagnose_extension_hooks():
    """Diagnose if extension hooks are being called."""
    print("\n🔍 Diagnosing extension hooks...")
    print("-" * 30)

    try:
        # Try to access glTF operators
        if hasattr(bpy.ops, 'export_scene') and hasattr(bpy.ops.export_scene, 'gltf'):
            print("✅ glTF export operator available")
        else:
            print("❌ glTF export operator not found")
            return False

        if hasattr(bpy.ops, 'import_scene') and hasattr(bpy.ops.import_scene, 'gltf'):
            print("✅ glTF import operator available")
        else:
            print("❌ glTF import operator not found")
            return False

        # Check glTF-Blender-IO extension discovery
        print("\n🔍 Checking glTF-Blender-IO extension discovery...")

        # Check loaded addons for extension attributes
        preferences = bpy.context.preferences
        print(f"📦 Total addons loaded: {len(preferences.addons)}")

        found_export_ext = False
        found_import_ext = False

        for addon_name in preferences.addons.keys():
            try:
                # Use the global sys module that was imported at the top
                if addon_name in sys.modules:
                    module = sys.modules[addon_name]
                    print(f"🔍 Checking addon: {addon_name}")

                    # Check for export extension
                    if hasattr(module, 'glTF2ExportUserExtension'):
                        print(f"   ✅ Found glTF2ExportUserExtension in {addon_name}")
                        found_export_ext = True
                    else:
                        print(f"   ❌ No glTF2ExportUserExtension in {addon_name}")

                    # Check for import extension
                    if hasattr(module, 'glTF2ImportUserExtension'):
                        print(f"   ✅ Found glTF2ImportUserExtension in {addon_name}")
                        found_import_ext = True
                    else:
                        print(f"   ❌ No glTF2ImportUserExtension in {addon_name}")
                else:
                    print(f"   ⚠️  Addon {addon_name} not in sys.modules")

            except Exception as e:
                print(f"   ❌ Error checking addon {addon_name}: {e}")

        print("\n🎯 Extension Discovery Results:")
        print(f"   Export extension found: {'✅' if found_export_ext else '❌'}")
        print(f"   Import extension found: {'✅' if found_import_ext else '❌'}")

        # Check if our extension is registered
        # This is harder to check directly, but we can try to see if the module is loaded
        ext_modules = [m for m in sys.modules.keys() if 'ext_bmesh_encoding' in m]
        print(f"\n📦 EXT_bmesh_encoding modules loaded: {len(ext_modules)}")
        for mod in ext_modules:
            print(f"   • {mod}")

        return found_export_ext and found_import_ext

    except Exception as e:
        print(f"❌ Extension hook diagnosis failed: {e}")
        return False


def main():
    """Run the triangulation diagnosis."""
    print("EXT_bmesh_encoding Triangulation Diagnosis")
    print("=" * 50)
    print("This script diagnoses why tests aren't detecting triangulation issues.")
    print("=" * 50)

    # Run diagnostics
    addon_ok = diagnose_addon_state()
    hooks_ok = diagnose_extension_hooks()
    roundtrip_ok = test_gltf_roundtrip()

    print("\n" + "=" * 50)
    print("DIAGNOSIS SUMMARY:")
    print(f"Addon State:     {'✅ GOOD' if addon_ok else '❌ BAD'}")
    print(f"Extension Hooks: {'✅ GOOD' if hooks_ok else '❌ BAD'}")
    print(f"Roundtrip Test:  {'✅ PASS' if roundtrip_ok else '❌ FAIL'}")

    all_good = addon_ok and hooks_ok and roundtrip_ok

    if all_good:
        print("\n🎉 ALL DIAGNOSTICS PASSED!")
        print("   EXT_bmesh_encoding is working correctly")
        print("   No triangulation issues detected")
    else:
        print("\n❌ DIAGNOSTICS FOUND ISSUES!")

        if not addon_ok:
            print("🔧 Addon Issues:")
            print("   • Addon not properly loaded/installed")
            print("   • Extension classes not discoverable")
            print("   • UI properties not registered")

        if not hooks_ok:
            print("🔧 Hook Issues:")
            print("   • glTF operators not available")
            print("   • Extension modules not loaded")

        if not roundtrip_ok:
            print("🔧 Triangulation Issues:")
            print("   • EXT_bmesh_encoding hooks not being called")
            print("   • BMesh reconstruction failing")
            print("   • Topology not preserved during roundtrip")

        print("\n🔧 Recommended Fixes:")
        print("   1. Ensure addon is installed via blender_manifest.toml")
        print("   2. Restart Blender after addon installation")
        print("   3. Check Blender console for error messages")
        print("   4. Verify glTF-Blender-IO addon is enabled")
        print("   5. Test with minimal mesh (single quad)")

    return all_good


if __name__ == "__main__":
    print("This script should be run from within Blender's Python console.")
    print("Copy and paste the contents into Blender's Text Editor and run it there.")
    print("\nAlternatively:")
    print("blender --background --python diagnose_triangulation.py")

    success = main()
    sys.exit(0 if success else 1)
