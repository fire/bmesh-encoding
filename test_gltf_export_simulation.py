#!/usr/bin/env python3
"""
Test to simulate glTF export process and verify EXT_bmesh_encoding integration.
"""

import sys
import os
import bpy
import json
from pathlib import Path


def create_test_mesh():
    """Create a simple test mesh in Blender."""
    print("🔧 Creating test mesh...")

    # Clear existing mesh objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create a simple cube mesh
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    mesh_obj = bpy.context.active_object

    print(f"✅ Created mesh: {mesh_obj.name}")
    return mesh_obj


def simulate_gltf_export():
    """Simulate the glTF export process to test EXT_bmesh_encoding integration."""
    print("🔍 Simulating glTF export process...")

    try:
        # Create test mesh
        mesh_obj = create_test_mesh()

        # Import our extension classes
        print("📦 Importing EXT_bmesh_encoding extension...")
        from gltf_extension import glTF2ExportUserExtension

        # Create extension instance
        export_ext = glTF2ExportUserExtension()
        print("✅ Created export extension instance")

        # Simulate glTF object structure that glTF-Blender-IO would create
        gltf2_object = {
            "asset": {"version": "2.0"},
            "meshes": [],
            "nodes": [{"mesh": 0}],
            "scenes": [{"nodes": [0]}],
            "scene": 0
        }

        # Simulate export settings
        export_settings = type('MockExportSettings', (), {
            'export_ext_bmesh_encoding': True,
            'export_format': 'GLTF_SEPARATE',
            'export_yup': True
        })()

        # Simulate glTF exporter
        gltf2_exporter = type('MockExporter', (), {
            'add_extension': lambda ext_name, ext_data: print(f"📤 Added extension: {ext_name}")
        })()

        print("🔄 Calling gather_gltf_hook...")

        # Call the extension hook directly
        export_ext.gather_gltf_hook(
            gltf2_object,
            mesh_obj,
            export_settings,
            gltf2_exporter
        )

        print("✅ Extension hook called successfully")

        # Check if extension data was added
        if 'extensions' in gltf2_object:
            print(f"📋 Extensions found in glTF object: {list(gltf2_object['extensions'].keys())}")

            if 'EXT_bmesh_encoding' in gltf2_object['extensions']:
                ext_data = gltf2_object['extensions']['EXT_bmesh_encoding']
                print("🎉 EXT_bmesh_encoding data found!")
                print(f"   Extension data keys: {list(ext_data.keys()) if isinstance(ext_data, dict) else 'N/A'}")

                # Save the extension data for inspection
                output_file = "test_extension_output.json"
                with open(output_file, 'w') as f:
                    json.dump(ext_data, f, indent=2)
                print(f"💾 Extension data saved to: {output_file}")

                return True
            else:
                print("❌ EXT_bmesh_encoding extension not found in glTF object")
                print(f"   Available extensions: {list(gltf2_object['extensions'].keys())}")
                return False
        else:
            print("❌ No extensions object found in glTF object")
            print("   This indicates the extension hook was not called or failed")
            return False

    except Exception as e:
        print(f"❌ Error during glTF export simulation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_extension_data_structure():
    """Test the structure of generated extension data."""
    print("\n🔍 Testing extension data structure...")

    try:
        # Check if we have saved extension data from previous test
        output_file = "test_extension_output.json"
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                ext_data = json.load(f)

            print("📋 Analyzing extension data structure...")

            # Check for required BMesh components
            required_components = ['vertices', 'edges', 'loops', 'faces']
            found_components = [comp for comp in required_components if comp in ext_data]

            if found_components:
                print(f"✅ Found BMesh components: {', '.join(found_components)}")

                for comp in found_components:
                    comp_data = ext_data[comp]
                    if isinstance(comp_data, dict):
                        if 'count' in comp_data:
                            print(f"   {comp}: {comp_data['count']} items")
                        else:
                            print(f"   {comp}: structure present")
                    else:
                        print(f"   {comp}: {type(comp_data)}")

                missing_components = [comp for comp in required_components if comp not in ext_data]
                if missing_components:
                    print(f"⚠️  Missing components: {', '.join(missing_components)}")

                return len(found_components) > 0
            else:
                print("❌ No BMesh components found in extension data")
                return False
        else:
            print("⚠️  No extension output file found - run export simulation first")
            return False

    except Exception as e:
        print(f"❌ Error analyzing extension data: {e}")
        return False


def main():
    """Run the glTF export simulation test."""
    print("EXT_bmesh_encoding glTF Export Simulation")
    print("=" * 45)

    # Test extension hook execution
    hook_success = simulate_gltf_export()

    # Test extension data structure
    data_success = test_extension_data_structure()

    print("\n" + "=" * 45)
    print("SUMMARY:")
    print(f"Hook Execution: {'✅ PASS' if hook_success else '❌ FAIL'}")
    print(f"Data Structure: {'✅ PASS' if data_success else '❌ FAIL'}")

    if hook_success and data_success:
        print("\n🎉 EXT_bmesh_encoding extension is working correctly!")
        print("   The issue is likely in glTF-Blender-IO integration, not the extension itself.")
        print("\n🔧 Next steps:")
        print("   1. Verify glTF-Blender-IO version compatibility")
        print("   2. Check Blender addon loading order")
        print("   3. Test with actual glTF export in Blender UI")
        print("   4. Check Blender console for extension discovery messages")
    else:
        print("\n❌ EXT_bmesh_encoding extension has issues that need fixing.")
        if not hook_success:
            print("   • Extension hook is not being called or is failing")
        if not data_success:
            print("   • Extension data structure is invalid")

    return hook_success and data_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
