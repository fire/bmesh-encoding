#!/usr/bin/env python3
"""
Test EXT_bmesh_encoding with quad topology preservation.
Creates a quad-based 3D shape, exports to glTF, imports back, and verifies quad preservation.
"""

import bpy
import sys
import os
import json
import math


def create_quad_test_mesh():
    """Create a test mesh with quad faces to verify topology preservation."""
    print("🔧 Creating quad test mesh...")

    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create a cube (6 quad faces by default)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object

    # Modify the cube to create some ngon faces for more comprehensive testing
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Extrude one face to create an ngon
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, 1)}
    )

    # Select the top face and subdivide it to create more complex topology
    bpy.ops.mesh.select_all(action='DESELECT')
    # Switch to face select mode
    bpy.ops.mesh.select_mode(type='FACE')
    # Select the top face (this is approximate - in practice we'd need more precise selection)

    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"✅ Created test mesh: {cube.name}")

    # Analyze the mesh topology
    mesh = cube.data
    print(f"   Vertices: {len(mesh.vertices)}")
    print(f"   Edges: {len(mesh.edges)}")
    print(f"   Faces: {len(mesh.polygons)}")

    # Count face types
    tri_count = sum(1 for p in mesh.polygons if len(p.vertices) == 3)
    quad_count = sum(1 for p in mesh.polygons if len(p.vertices) == 4)
    ngon_count = sum(1 for p in mesh.polygons if len(p.vertices) > 4)

    print(f"   Triangles: {tri_count}")
    print(f"   Quads: {quad_count}")
    print(f"   Ngons: {ngon_count}")

    # Store original topology for comparison
    original_topology = {
        'vertices': len(mesh.vertices),
        'edges': len(mesh.edges),
        'faces': len(mesh.polygons),
        'triangles': tri_count,
        'quads': quad_count,
        'ngons': ngon_count
    }

    # Store topology data on the object for later comparison
    cube['original_topology'] = original_topology

    return cube, original_topology


def export_gltf_with_extension(mesh_obj, export_path):
    """Export the mesh to glTF with EXT_bmesh_encoding enabled."""
    print(f"\n📤 Exporting to glTF: {export_path}")

    try:
        # Ensure EXT_bmesh_encoding is enabled
        if hasattr(bpy.context.scene, 'enable_ext_bmesh_encoding'):
            bpy.context.scene.enable_ext_bmesh_encoding = True
            print("✅ EXT_bmesh_encoding enabled for export")
        else:
            print("⚠️ EXT_bmesh_encoding property not found in scene")

        # Configure export settings
        export_settings = {
            'filepath': export_path,
            'export_format': 'GLTF_SEPARATE',
            'export_yup': True,
            'export_apply': True,
            'export_extras': True,
            'export_extensions': True,
            'use_selection': True,  # Only export selected object
        }

        # Select only our test mesh
        bpy.ops.object.select_all(action='DESELECT')
        mesh_obj.select_set(True)
        bpy.context.view_layer.objects.active = mesh_obj

        # Perform export
        bpy.ops.export_scene.gltf(**export_settings)

        print("✅ glTF export completed")

        # Verify the exported file
        if os.path.exists(export_path):
            print(f"✅ Export file created: {export_path}")

            # Check file size
            file_size = os.path.getsize(export_path)
            print(f"   File size: {file_size} bytes")

            # Quick validation of glTF structure
            with open(export_path, 'r', encoding='utf-8') as f:
                gltf_data = json.load(f)

            if 'extensions' in gltf_data and 'EXT_bmesh_encoding' in gltf_data['extensions']:
                print("🎉 EXT_bmesh_encoding found in exported glTF!")
                return True
            else:
                print("❌ EXT_bmesh_encoding NOT found in exported glTF")
                return False
        else:
            print(f"❌ Export file not created: {export_path}")
            return False

    except Exception as e:
        print(f"❌ Error during glTF export: {e}")
        import traceback
        traceback.print_exc()
        return False


def import_gltf_and_compare(import_path, original_topology):
    """Import the glTF file and compare topology with original."""
    print(f"\n📥 Importing glTF: {import_path}")

    try:
        # Clear existing objects except for our reference
        bpy.ops.object.select_all(action='DESELECT')

        # Import the glTF file
        import_settings = {
            'filepath': import_path,
            'import_pack_images': True,
            'import_shading': 'NORMALS',
        }

        bpy.ops.import_scene.gltf(**import_settings)

        print("✅ glTF import completed")

        # Find the imported mesh
        imported_objects = [obj for obj in bpy.context.scene.objects
                          if obj.type == 'MESH' and obj != bpy.context.active_object]

        if not imported_objects:
            print("❌ No mesh objects found after import")
            return False

        imported_obj = imported_objects[0]  # Take the first imported mesh
        print(f"✅ Found imported mesh: {imported_obj.name}")

        # Analyze imported mesh topology
        imported_mesh = imported_obj.data
        print(f"   Vertices: {len(imported_mesh.vertices)}")
        print(f"   Edges: {len(imported_mesh.edges)}")
        print(f"   Faces: {len(imported_mesh.polygons)}")

        # Count face types in imported mesh
        imported_tri_count = sum(1 for p in imported_mesh.polygons if len(p.vertices) == 3)
        imported_quad_count = sum(1 for p in imported_mesh.polygons if len(p.vertices) == 4)
        imported_ngon_count = sum(1 for p in imported_mesh.polygons if len(p.vertices) > 4)

        print(f"   Triangles: {imported_tri_count}")
        print(f"   Quads: {imported_quad_count}")
        print(f"   Ngons: {imported_ngon_count}")

        imported_topology = {
            'vertices': len(imported_mesh.vertices),
            'edges': len(imported_mesh.edges),
            'faces': len(imported_mesh.polygons),
            'triangles': imported_tri_count,
            'quads': imported_quad_count,
            'ngons': imported_ngon_count
        }

        # Compare topologies
        print("\n🔍 Comparing mesh topologies:")
        print("Original → Imported")
        print(f"Vertices: {original_topology['vertices']} → {imported_topology['vertices']}")
        print(f"Edges: {original_topology['edges']} → {imported_topology['edges']}")
        print(f"Faces: {original_topology['faces']} → {imported_topology['faces']}")
        print(f"Triangles: {original_topology['triangles']} → {imported_topology['triangles']}")
        print(f"Quads: {original_topology['quads']} → {imported_topology['quads']}")
        print(f"Ngons: {original_topology['ngons']} → {imported_topology['ngons']}")

        # Check if quad topology is preserved
        quad_preserved = imported_topology['quads'] == original_topology['quads']
        ngon_preserved = imported_topology['ngons'] == original_topology['ngons']

        print(f"\n📊 Topology Preservation Results:")
        print(f"Quad faces preserved: {'✅ YES' if quad_preserved else '❌ NO'}")
        print(f"Ngon faces preserved: {'✅ YES' if ngon_preserved else '❌ NO'}")

        if quad_preserved and ngon_preserved:
            print("\n🎉 SUCCESS! EXT_bmesh_encoding preserved mesh topology!")
            print("   The quad/ngon structure survived the glTF roundtrip.")
            return True
        else:
            print("\n❌ FAILURE! EXT_bmesh_encoding did not preserve mesh topology.")
            print("   The mesh was triangulated during export/import.")
            return False

    except Exception as e:
        print(f"❌ Error during glTF import: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_addon_status():
    """Check if EXT_bmesh_encoding addon is properly loaded."""
    print("🔍 Checking addon status...")

    addon_name = "ext_bmesh_encoding"

    if addon_name in bpy.context.preferences.addons:
        print("✅ EXT_bmesh_encoding addon is loaded")
        return True
    else:
        print("❌ EXT_bmesh_encoding addon is not loaded")
        print("   Please install and enable the addon first")
        return False


def main():
    """Run the quad topology preservation test."""
    print("EXT_bmesh_encoding Quad Topology Preservation Test")
    print("=" * 55)
    print("This test creates a quad-based 3D shape, exports it to glTF,")
    print("imports it back, and verifies that quad topology is preserved.")
    print("=" * 55)

    # Check addon status
    if not test_addon_status():
        print("\n❌ Cannot proceed without EXT_bmesh_encoding addon")
        return False

    # Create test mesh
    test_mesh, original_topology = create_quad_test_mesh()

    # Set up file paths
    export_path = os.path.join(os.getcwd(), "quad_test_export.gltf")
    import_path = export_path  # Same file for roundtrip test

    # Export to glTF
    export_success = export_gltf_with_extension(test_mesh, export_path)

    if not export_success:
        print("\n❌ Export failed - cannot proceed with roundtrip test")
        return False

    # Import and compare
    roundtrip_success = import_gltf_and_compare(import_path, original_topology)

    print("\n" + "=" * 55)
    print("QUAD ROUNDTRIP TEST SUMMARY:")
    print(f"Export: {'✅ SUCCESS' if export_success else '❌ FAILED'}")
    print(f"Roundtrip: {'✅ SUCCESS' if roundtrip_success else '❌ FAILED'}")

    if export_success and roundtrip_success:
        print("\n🎉 EXT_bmesh_encoding is working correctly!")
        print("   Quad topology is preserved during glTF export/import roundtrip.")
        print("   The extension successfully prevents triangulation of quad faces.")
    else:
        print("\n❌ EXT_bmesh_encoding is not working as expected.")
        if not export_success:
            print("   • Extension data was not added during export")
        if not roundtrip_success:
            print("   • Quad topology was not preserved during import")

        print("\n🔧 Troubleshooting:")
        print("   1. Check Blender console for extension-related errors")
        print("   2. Verify glTF-Blender-IO addon is enabled and compatible")
        print("   3. Ensure EXT_bmesh_encoding addon is properly loaded")
        print("   4. Check that extension hooks are being called")

    return export_success and roundtrip_success


if __name__ == "__main__":
    print("This script should be run from within Blender.")
    print("Copy the contents to Blender's Text Editor and run it there.")
    print("\nOr save as a .py file and run with:")
    print("blender --background --python quad_roundtrip_test.py")

    success = main()
    sys.exit(0 if success else 1)
