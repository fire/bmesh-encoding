#!/usr/bin/env python3
"""
Complete roundtrip test for EXT_bmesh_encoding: Export → Import → Validate
"""

import bpy
import os
import sys
import tempfile
import json
from pathlib import Path

def create_test_mesh():
    """Create a test mesh with complex topology for EXT_bmesh_encoding testing."""
    print("🎨 Creating test mesh with complex topology...")

    # Clear existing mesh objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create a new mesh with mixed topology (quads, triangles, ngon)
    mesh = bpy.data.meshes.new("EXT_bmesh_test")
    obj = bpy.data.objects.new("EXT_bmesh_test", mesh)

    # Create vertices for a complex shape
    vertices = [
        (-1, -1, 0),  # 0
        (1, -1, 0),   # 1
        (1, 1, 0),    # 2
        (-1, 1, 0),   # 3
        (0, 0, 1),    # 4 - peak
        (-0.5, -0.5, 0.5),  # 5
        (0.5, -0.5, 0.5),   # 6
    ]

    # Create faces with mixed topology
    faces = [
        (0, 1, 2, 3),     # quad base
        (0, 1, 6, 5),     # quad side 1
        (1, 2, 4, 6),     # quad side 2
        (2, 3, 4),        # triangle side 3
        (3, 0, 5, 4),     # quad side 4
        (5, 6, 4),        # triangle top
    ]

    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)

    # Set smooth shading for some faces
    for i, poly in enumerate(mesh.polygons):
        if i % 2 == 0:  # Alternate smooth/flat
            poly.use_smooth = True

    # Add the object to the scene
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    print(f"✅ Created test mesh: {len(mesh.vertices)} vertices, {len(mesh.polygons)} faces")
    print(f"   Topology: {sum(1 for p in mesh.polygons if len(p.vertices) == 3)} tris, "
          f"{sum(1 for p in mesh.polygons if len(p.vertices) == 4)} quads, "
          f"{sum(1 for p in mesh.polygons if len(p.vertices) > 4)} ngons")

    return obj

def enable_ext_bmesh_encoding():
    """Enable the EXT_bmesh_encoding extension."""
    print("🔧 Enabling EXT_bmesh_encoding extension...")

    # Enable via scene property
    bpy.context.scene.enable_ext_bmesh_encoding = True
    print("✅ EXT_bmesh_encoding enabled via scene property")

def export_gltf_test(output_path):
    """Export the current scene to glTF with EXT_bmesh_encoding."""
    print(f"📤 Exporting to glTF: {output_path}")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Export to glTF
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLTF_SEPARATE',  # Separate .gltf + .bin
        use_selection=True,
        export_extras=True,
        export_yup=True,
        export_apply=True,
    )

    print(f"✅ Exported glTF to: {output_path}")
    return output_path

def validate_exported_gltf(gltf_path):
    """Validate that the exported glTF contains EXT_bmesh_encoding data."""
    print(f"🔍 Validating exported glTF: {gltf_path}")

    try:
        with open(gltf_path, 'r', encoding='utf-8') as f:
            gltf_data = json.load(f)

        # Check for extensions
        if 'extensions' not in gltf_data:
            print("❌ No extensions found in glTF")
            return False

        extensions = gltf_data['extensions']
        print(f"ℹ️  Found extensions: {list(extensions.keys())}")

        if 'EXT_bmesh_encoding' not in extensions:
            print("❌ EXT_bmesh_encoding not found in exported glTF")
            return False

        print("✅ EXT_bmesh_encoding found in exported glTF!")

        # Validate extension structure
        ext_data = extensions['EXT_bmesh_encoding']
        if not isinstance(ext_data, dict):
            print(f"❌ EXT_bmesh_encoding should be dict, got {type(ext_data)}")
            return False

        print(f"ℹ️  Extension data keys: {list(ext_data.keys())}")

        # Check for required components
        required = ['vertices', 'edges', 'loops', 'faces']
        found = [comp for comp in required if comp in ext_data]

        if not found:
            print("❌ No BMesh components found in extension data")
            return False

        print(f"✅ Found BMesh components: {', '.join(found)}")

        # Check extensionsUsed and extensionsRequired
        if 'extensionsUsed' in gltf_data and 'EXT_bmesh_encoding' in gltf_data['extensionsUsed']:
            print("✅ EXT_bmesh_encoding listed in extensionsUsed")
        else:
            print("⚠️  EXT_bmesh_encoding not in extensionsUsed")

        if 'extensionsRequired' in gltf_data and 'EXT_bmesh_encoding' in gltf_data['extensionsRequired']:
            print("✅ EXT_bmesh_encoding listed in extensionsRequired")
        else:
            print("⚠️  EXT_bmesh_encoding not in extensionsRequired")

        return True

    except Exception as e:
        print(f"❌ Error validating glTF: {e}")
        return False

def import_gltf_test(gltf_path):
    """Import the glTF file back into Blender."""
    print(f"📥 Importing glTF: {gltf_path}")

    # Clear existing objects except the test mesh
    test_obj = bpy.context.active_object
    bpy.ops.object.select_all(action='SELECT')
    for obj in bpy.context.selected_objects:
        if obj != test_obj:
            obj.select_set(False)
    bpy.ops.object.delete()

    # Import the glTF
    bpy.ops.import_scene.gltf(filepath=gltf_path)

    # Find the imported object
    imported_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and obj != test_obj]
    if not imported_objects:
        print("❌ No mesh objects found after import")
        return None

    imported_obj = imported_objects[0]
    print(f"✅ Imported object: {imported_obj.name}")

    return imported_obj

def compare_meshes(original_obj, imported_obj):
    """Compare the original and imported meshes for topology preservation."""
    print("🔄 Comparing original and imported meshes...")

    orig_mesh = original_obj.data
    import_mesh = imported_obj.data

    print(f"📊 Original mesh: {len(orig_mesh.vertices)} verts, {len(orig_mesh.polygons)} faces")
    print(f"📊 Imported mesh: {len(import_mesh.vertices)} verts, {len(import_mesh.polygons)} faces")

    # Compare topology
    orig_tris = sum(1 for p in orig_mesh.polygons if len(p.vertices) == 3)
    orig_quads = sum(1 for p in orig_mesh.polygons if len(p.vertices) == 4)
    orig_ngons = sum(1 for p in orig_mesh.polygons if len(p.vertices) > 4)

    import_tris = sum(1 for p in import_mesh.polygons if len(p.vertices) == 3)
    import_quads = sum(1 for p in import_mesh.polygons if len(p.vertices) == 4)
    import_ngons = sum(1 for p in import_mesh.polygons if len(p.vertices) > 4)

    print(f"📊 Original topology: {orig_tris} tris, {orig_quads} quads, {orig_ngons} ngons")
    print(f"📊 Imported topology: {import_tris} tris, {import_quads} quads, {import_ngons} ngons")

    # Check if topology is preserved
    if orig_tris == import_tris and orig_quads == import_quads and orig_ngons == import_ngons:
        print("✅ Topology preservation: PERFECT!")
        return True
    else:
        print("❌ Topology preservation: FAILED")
        print("   Original and imported meshes have different topology")
        return False

def main():
    """Main test function."""
    print("🚀 EXT_bmesh_encoding Complete Roundtrip Test")
    print("=" * 60)

    try:
        # Create test mesh
        original_obj = create_test_mesh()
        if not original_obj:
            print("❌ Failed to create test mesh")
            return False

        # Enable EXT_bmesh_encoding
        enable_ext_bmesh_encoding()

        # Create temporary file for export
        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp:
            gltf_path = tmp.name

        try:
            # Export to glTF
            export_gltf_test(gltf_path)

            # Validate exported glTF
            export_valid = validate_exported_gltf(gltf_path)
            if not export_valid:
                print("❌ Export validation failed")
                return False

            # Import glTF back
            imported_obj = import_gltf_test(gltf_path)
            if not imported_obj:
                print("❌ Import failed")
                return False

            # Compare meshes
            topology_preserved = compare_meshes(original_obj, imported_obj)

            print("\n" + "=" * 60)
            if topology_preserved:
                print("🎉 COMPLETE ROUNDTRIP TEST: PASSED!")
                print("   EXT_bmesh_encoding is working correctly")
                print("   • Extension data exported to glTF ✅")
                print("   • Extension data imported from glTF ✅")
                print("   • Mesh topology preserved ✅")
                return True
            else:
                print("❌ COMPLETE ROUNDTRIP TEST: FAILED!")
                print("   Topology was not preserved during roundtrip")
                return False

        finally:
            # Clean up temporary file
            if os.path.exists(gltf_path):
                os.unlink(gltf_path)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
