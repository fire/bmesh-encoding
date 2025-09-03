#!/usr/bin/env python3
"""
Test EXT_bmesh_encoding topology preservation.
This test verifies that quads and ngons are preserved during glTF roundtrip.
"""

import bpy
import os
import json
import tempfile
import sys
from pathlib import Path


def create_test_mesh_with_known_topology():
    """Create a test mesh with specific topology for validation."""
    print("🔧 Creating test mesh with known topology...")

    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create a cube (6 quads by default)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object

    # Add some ngon faces by extruding and creating complex geometry
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Create an ngon by subdividing and removing edges
    bpy.ops.mesh.subdivide(number_cuts=1)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.inset(faces=True, thickness=0.1)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, 0.5)}
    )

    bpy.ops.object.mode_set(mode='OBJECT')

    # Analyze the created topology
    mesh = cube.data
    tri_count = sum(1 for poly in mesh.polygons if len(poly.vertices) == 3)
    quad_count = sum(1 for poly in mesh.polygons if len(poly.vertices) == 4)
    ngon_count = sum(1 for poly in mesh.polygons if len(poly.vertices) > 4)

    print("📊 Original mesh topology:")
    print(f"   Triangles: {tri_count}")
    print(f"   Quads: {quad_count}")
    print(f"   Ngons: {ngon_count}")
    print(f"   Total faces: {len(mesh.polygons)}")

    return cube, {
        'triangles': tri_count,
        'quads': quad_count,
        'ngons': ngon_count,
        'total_faces': len(mesh.polygons)
    }


def export_mesh_to_gltf(mesh_object, export_path):
    """Export mesh to glTF format."""
    print(f"📤 Exporting mesh to: {export_path}")

    # Select only the target object
    bpy.ops.object.select_all(action='DESELECT')
    mesh_object.select_set(True)
    bpy.context.view_layer.objects.active = mesh_object

    # Configure export settings
    export_settings = {
        'filepath': export_path,
        'export_format': 'GLTF_SEPARATE',
        'export_yup': True,
        'export_apply': True,
        'export_extras': True,
        'export_extensions': True,
        'use_selection': True,
    }

    # Perform export
    bpy.ops.export_scene.gltf(**export_settings)

    if os.path.exists(export_path):
        print("✅ glTF export completed successfully")
        return True
    else:
        print("❌ glTF export failed - file not created")
        return False


def import_gltf_file(import_path):
    """Import glTF file and return the imported object."""
    print(f"📥 Importing glTF from: {import_path}")

    # Clear existing objects except the original
    original_objects = set(bpy.data.objects)

    # Import glTF
    bpy.ops.import_scene.gltf(filepath=import_path)

    # Find the newly imported object
    new_objects = set(bpy.data.objects) - original_objects
    if new_objects:
        imported_object = list(new_objects)[0]
        print(f"✅ glTF import completed: {imported_object.name}")
        return imported_object
    else:
        print("❌ glTF import failed - no new objects created")
        return None


def analyze_mesh_topology(mesh_object):
    """Analyze the topology of a mesh object."""
    mesh = mesh_object.data

    tri_count = sum(1 for poly in mesh.polygons if len(poly.vertices) == 3)
    quad_count = sum(1 for poly in mesh.polygons if len(poly.vertices) == 4)
    ngon_count = sum(1 for poly in mesh.polygons if len(poly.vertices) > 4)

    topology = {
        'triangles': tri_count,
        'quads': quad_count,
        'ngons': ngon_count,
        'total_faces': len(mesh.polygons)
    }

    print("📊 Mesh topology analysis:")
    print(f"   Triangles: {tri_count}")
    print(f"   Quads: {quad_count}")
    print(f"   Ngons: {ngon_count}")
    print(f"   Total faces: {len(mesh.polygons)}")

    return topology


def validate_gltf_extension_data(gltf_path):
    """Validate that EXT_bmesh_encoding data is present and valid."""
    print(f"🔍 Validating EXT_bmesh_encoding in: {gltf_path}")

    try:
        with open(gltf_path, 'r', encoding='utf-8') as f:
            gltf_data = json.load(f)

        # Check for extensions
        if 'extensions' not in gltf_data:
            print("❌ No extensions found in glTF")
            return False

        if 'EXT_bmesh_encoding' not in gltf_data['extensions']:
            print("❌ EXT_bmesh_encoding not found in glTF")
            return False

        ext_data = gltf_data['extensions']['EXT_bmesh_encoding']
        print("✅ EXT_bmesh_encoding found")

        # Check for required components
        required = ['vertices', 'edges', 'loops', 'faces']
        found = [comp for comp in required if comp in ext_data]

        print(f"📋 BMesh components found: {found}")

        if len(found) == len(required):
            print("✅ All required EXT_bmesh_encoding components present")
            return True
        else:
            missing = [comp for comp in required if comp not in ext_data]
            print(f"❌ Missing components: {missing}")
            return False

    except Exception as e:
        print(f"❌ Error validating glTF: {e}")
        return False


def compare_topologies(original_topo, imported_topo):
    """Compare two topology dictionaries."""
    print("🔍 Comparing mesh topologies...")

    differences = []
    all_match = True

    for key in ['triangles', 'quads', 'ngons', 'total_faces']:
        orig = original_topo.get(key, 0)
        imp = imported_topo.get(key, 0)

        if orig != imp:
            differences.append(f"{key}: {orig} → {imp}")
            all_match = False
        else:
            print(f"✅ {key}: {orig} (matches)")

    if differences:
        print("❌ Topology differences found:")
        for diff in differences:
            print(f"   {diff}")
    else:
        print("✅ All topology counts match perfectly!")

    return all_match


def test_topology_preservation():
    """Main test function for topology preservation."""
    print("EXT_bmesh_encoding Topology Preservation Test")
    print("=" * 55)

    try:
        # Step 1: Create test mesh with known topology
        print("\n1️⃣ Creating test mesh...")
        test_object, original_topology = create_test_mesh_with_known_topology()

        # Step 2: Export to glTF
        print("\n2️⃣ Exporting to glTF...")
        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as temp_file:
            export_path = temp_file.name

        success = export_mesh_to_gltf(test_object, export_path)
        if not success:
            print("❌ Export failed - cannot continue test")
            return False

        # Step 3: Validate EXT_bmesh_encoding data
        print("\n3️⃣ Validating EXT_bmesh_encoding data...")
        ext_valid = validate_gltf_extension_data(export_path)
        if not ext_valid:
            print("❌ EXT_bmesh_encoding validation failed")
            return False

        # Step 4: Import glTF back
        print("\n4️⃣ Importing glTF back...")
        imported_object = import_gltf_file(export_path)
        if not imported_object:
            print("❌ Import failed - cannot continue test")
            return False

        # Step 5: Analyze imported mesh topology
        print("\n5️⃣ Analyzing imported mesh topology...")
        imported_topology = analyze_mesh_topology(imported_object)

        # Step 6: Compare topologies
        print("\n6️⃣ Comparing topologies...")
        topologies_match = compare_topologies(original_topology, imported_topology)

        # Cleanup
        os.unlink(export_path)

        # Final result
        print("\n" + "=" * 55)
        if topologies_match:
            print("🎉 TOPOLOGY PRESERVATION TEST PASSED!")
            print("   EXT_bmesh_encoding is working correctly")
            print("   Quads and ngons are preserved during glTF roundtrip")
            return True
        else:
            print("❌ TOPOLOGY PRESERVATION TEST FAILED!")
            print("   EXT_bmesh_encoding is not preserving mesh topology")
            print("   Quads/ngons are being triangulated")
            print("\n🔧 This indicates:")
            print("   • EXT_bmesh_encoding extension hooks are not being called")
            print("   • The addon is not properly integrated with glTF-Blender-IO")
            print("   • BMesh reconstruction is failing")
            return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the topology preservation test."""
    print("This test should be run from within Blender's Python console.")
    print("It verifies that EXT_bmesh_encoding preserves quad/ngon topology.")
    print("\nTo run this test:")
    print("1. Open Blender")
    print("2. Go to Scripting workspace")
    print("3. Load this script")
    print("4. Run the script")
    print("\nAlternatively:")
    print("blender --background --python test_topology_validation.py")

    success = test_topology_preservation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
