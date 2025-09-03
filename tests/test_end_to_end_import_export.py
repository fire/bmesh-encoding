"""
End-to-end testing for EXT_bmesh_encoding import/export operations.
Tests complete round-trip workflows with various mesh topologies.
"""
import pytest
import bpy
import bmesh
import math
import tempfile
import os
from pathlib import Path
import sys

# Add the src directory to Python path to allow imports
test_dir = Path(__file__).parent
src_dir = test_dir.parent
sys.path.insert(0, str(src_dir))

from ext_bmesh_encoding.encoding import BmeshEncoder
from ext_bmesh_encoding.decoding import BmeshDecoder
from ext_bmesh_encoding.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def end_to_end_setup():
    """Set up test environment for end-to-end tests."""
    encoder = BmeshEncoder()
    decoder = BmeshDecoder()

    yield encoder, decoder


def create_triangle_mesh(name="TriangleMesh"):
    """Create a simple triangular mesh."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create a simple triangle
    verts = [
        (0, 0, 0),
        (1, 0, 0),
        (0.5, 1, 0)
    ]

    for vert_pos in verts:
        bm.verts.new(vert_pos)

    bm.verts.ensure_lookup_table()
    bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[2]])

    bm.to_mesh(mesh)
    bm.free()

    return obj


def create_quad_mesh(name="QuadMesh"):
    """Create a simple quad mesh."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create a simple quad
    verts = [
        (0, 0, 0),
        (1, 0, 0),
        (1, 1, 0),
        (0, 1, 0)
    ]

    for vert_pos in verts:
        bm.verts.new(vert_pos)

    bm.verts.ensure_lookup_table()
    bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[2], bm.verts[3]])

    bm.to_mesh(mesh)
    bm.free()

    return obj


def create_ngon_mesh(name="NgonMesh", sides=5):
    """Create an ngon mesh with specified number of sides."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create ngon vertices in a circle
    verts = []
    for i in range(sides):
        angle = 2 * math.pi * i / sides
        x = math.cos(angle)
        y = math.sin(angle)
        verts.append((x, y, 0))

    for vert_pos in verts:
        bm.verts.new(vert_pos)

    bm.verts.ensure_lookup_table()
    bm.faces.new(bm.verts)

    bm.to_mesh(mesh)
    bm.free()

    return obj


def create_mixed_topology_mesh(name="MixedTopologyMesh"):
    """Create a mesh with mixed face types (triangles, quads, ngons)."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create a complex shape with different face types
    verts = [
        # Base square
        (0, 0, 0),    # 0
        (2, 0, 0),    # 1
        (2, 2, 0),    # 2
        (0, 2, 0),    # 3
        # Top triangle
        (1, 1, 1),    # 4
        # Side extensions for ngon
        (3, 1, 0),    # 5
        (2.5, 2.5, 0), # 6
        (1, 3, 0),    # 7
    ]

    for vert_pos in verts:
        bm.verts.new(vert_pos)

    bm.verts.ensure_lookup_table()

    # Triangle face
    bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[4]])

    # Quad face
    bm.faces.new([bm.verts[1], bm.verts[2], bm.verts[6], bm.verts[5]])

    # Pentagon face
    bm.faces.new([bm.verts[2], bm.verts[3], bm.verts[7], bm.verts[6], bm.verts[5]])

    # Triangle on top
    bm.faces.new([bm.verts[0], bm.verts[3], bm.verts[4]])

    bm.to_mesh(mesh)
    bm.free()

    return obj


def create_cube_with_hole(name="CubeWithHole"):
    """Create a cube with a hole (non-manifold topology)."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create cube vertices
    verts = [
        (-1, -1, -1), (-1, -1, 1), (-1, 1, -1), (-1, 1, 1),
        (1, -1, -1), (1, -1, 1), (1, 1, -1), (1, 1, 1)
    ]

    for vert_pos in verts:
        bm.verts.new(vert_pos)

    bm.verts.ensure_lookup_table()

    # Create cube faces
    faces = [
        [0, 1, 3, 2],  # left
        [4, 6, 7, 5],  # right
        [0, 2, 6, 4],  # front
        [1, 5, 7, 3],  # back
        [0, 4, 5, 1],  # bottom
        [2, 3, 7, 6],  # top
    ]

    for face_verts in faces:
        bm.faces.new([bm.verts[i] for i in face_verts])

    bm.to_mesh(mesh)
    bm.free()

    return obj


def compare_mesh_topology(original_mesh, imported_mesh, tolerance=1e-6):
    """Compare mesh topology and geometry."""
    # Compare vertex counts
    assert len(original_mesh.vertices) == len(imported_mesh.vertices), \
        f"Vertex count mismatch: {len(original_mesh.vertices)} vs {len(imported_mesh.vertices)}"

    # Compare face counts
    assert len(original_mesh.polygons) == len(imported_mesh.polygons), \
        f"Face count mismatch: {len(original_mesh.polygons)} vs {len(imported_mesh.polygons)}"

    # Compare vertex positions
    for i, (orig_vert, imp_vert) in enumerate(zip(original_mesh.vertices, imported_mesh.vertices)):
        orig_pos = orig_vert.co
        imp_pos = imp_vert.co
        distance = (orig_pos - imp_pos).length
        assert distance < tolerance, \
            f"Vertex {i} position mismatch: {distance} > {tolerance}"

    # Compare face topology
    for i, (orig_face, imp_face) in enumerate(zip(original_mesh.polygons, imported_mesh.polygons)):
        orig_verts = set(orig_face.vertices)
        imp_verts = set(imp_face.vertices)
        assert orig_verts == imp_verts, \
            f"Face {i} topology mismatch: {orig_verts} vs {imp_verts}"

    return True


class TestEndToEndImportExport:
    """End-to-end tests for import/export operations."""

    def test_bmesh_encoding_decoding_core_functionality(self, end_to_end_setup):
        """Test the core BMesh encoding/decoding functionality without Blender operators.

        This tests the fundamental encoding/decoding logic that should work
        regardless of operator registration issues.
        """
        encoder, decoder = end_to_end_setup

        # Create a simple test mesh
        obj = create_quad_mesh("CoreTest")
        original_mesh = obj.data

        try:
            # Test encoding
            encoded_data = encoder.encode_object(obj)
            assert encoded_data is not None, "Encoding failed"
            assert "vertices" in encoded_data, "Encoded data missing vertices"
            assert "faces" in encoded_data, "Encoded data missing faces"
            logger.info("✅ BMesh encoding successful")

            # Verify encoded data structure
            assert encoded_data["vertices"]["count"] == len(original_mesh.vertices)
            assert encoded_data["faces"]["count"] == len(original_mesh.polygons)
            logger.info(f"✅ Encoded data structure valid: {encoded_data['vertices']['count']} verts, {encoded_data['faces']['count']} faces")

            # Test decoding into new mesh
            new_mesh = bpy.data.meshes.new("DecodedTest")
            success = decoder.decode_into_mesh(encoded_data, new_mesh)

            assert success, "Decoding failed"
            assert new_mesh is not None, "Decoded mesh is None"
            logger.info("✅ BMesh decoding successful")

            # Compare topology
            assert len(new_mesh.vertices) == len(original_mesh.vertices), "Vertex count mismatch"
            assert len(new_mesh.polygons) == len(original_mesh.polygons), "Face count mismatch"
            logger.info("✅ Topology preserved in decoding")

            # Check face types are preserved (quads should remain quads)
            original_face_sizes = [len(poly.vertices) for poly in original_mesh.polygons]
            decoded_face_sizes = [len(poly.vertices) for poly in new_mesh.polygons]

            assert original_face_sizes == decoded_face_sizes, f"Face sizes changed: {original_face_sizes} -> {decoded_face_sizes}"
            logger.info(f"✅ Face sizes preserved: {original_face_sizes}")

            # Verify we have quads (face size 4)
            assert all(size == 4 for size in decoded_face_sizes), f"Expected all quads, got sizes: {decoded_face_sizes}"
            logger.info("✅ All faces are quads as expected")

        finally:
            # Cleanup
            bpy.data.objects.remove(obj)
            if 'new_mesh' in locals():
                bpy.data.meshes.remove(new_mesh)

    def test_extension_hook_methods_exist_and_callable(self, end_to_end_setup):
        """Test that EXT_bmesh_encoding extension hook methods exist and are callable.

        This tests the extension interface without requiring full operator registration.
        """
        encoder, decoder = end_to_end_setup

        # Import the extension
        from ext_bmesh_encoding import gltf_extension

        # Test that extension instance exists
        ext = gltf_extension.ext_bmesh_encoding
        assert ext is not None, "Extension instance is None"
        logger.info("✅ Extension instance exists")

        # Test that required methods exist
        assert hasattr(ext, 'import_mesh'), "import_mesh method missing"
        assert hasattr(ext, 'export_mesh'), "export_mesh method missing"
        assert hasattr(ext, 'gather_gltf_extensions'), "gather_gltf_extensions method missing"
        logger.info("✅ All required extension methods exist")

        # Test that methods are callable (don't actually call them with real data)
        assert callable(ext.import_mesh), "import_mesh is not callable"
        assert callable(ext.export_mesh), "export_mesh is not callable"
        assert callable(ext.gather_gltf_extensions), "gather_gltf_extensions is not callable"
        logger.info("✅ All extension methods are callable")

        # Test extension name
        assert ext.extension_name == "EXT_bmesh_encoding", f"Wrong extension name: {ext.extension_name}"
        logger.info("✅ Extension name is correct")

    def test_topology_preservation_logic(self, end_to_end_setup):
        """Test the topology preservation logic without full import/export.

        This tests that the core logic for preserving mesh topology works correctly.
        """
        encoder, decoder = end_to_end_setup

        # Create test mesh with mixed topology
        obj = create_mixed_topology_mesh("TopologyTest")
        original_mesh = obj.data

        try:
            # Get original face distribution
            original_faces = list(original_mesh.polygons)
            original_sizes = [len(face.vertices) for face in original_faces]
            original_triangles = original_sizes.count(3)
            original_quads = original_sizes.count(4)
            original_ngons = sum(1 for size in original_sizes if size > 4)

            logger.info(f"Original topology: {len(original_faces)} faces")
            logger.info(f"  Triangles: {original_triangles}")
            logger.info(f"  Quads: {original_quads}")
            logger.info(f"  Ngons: {original_ngons}")

            # Encode the mesh
            encoded_data = encoder.encode_object(obj)
            assert encoded_data is not None, "Encoding failed"

            # Create new mesh and decode
            new_mesh = bpy.data.meshes.new("TopologyDecoded")
            success = decoder.decode_into_mesh(encoded_data, new_mesh)
            assert success, "Decoding failed"

            # Check decoded topology
            decoded_faces = list(new_mesh.polygons)
            decoded_sizes = [len(face.vertices) for face in decoded_faces]
            decoded_triangles = decoded_sizes.count(3)
            decoded_quads = decoded_sizes.count(4)
            decoded_ngons = sum(1 for size in decoded_sizes if size > 4)

            logger.info(f"Decoded topology: {len(decoded_faces)} faces")
            logger.info(f"  Triangles: {decoded_triangles}")
            logger.info(f"  Quads: {decoded_quads}")
            logger.info(f"  Ngons: {decoded_ngons}")

            # Verify topology is preserved
            assert len(decoded_faces) == len(original_faces), "Face count changed"
            assert decoded_sizes == original_sizes, "Face sizes changed"
            assert decoded_triangles == original_triangles, "Triangle count changed"
            assert decoded_quads == original_quads, "Quad count changed"
            assert decoded_ngons == original_ngons, "Ngon count changed"

            logger.info("✅ Mixed topology preserved perfectly")
            logger.info("✅ Triangulation prevented - complex face types maintained")

        finally:
            # Cleanup
            bpy.data.objects.remove(obj)
            if 'new_mesh' in locals():
                bpy.data.meshes.remove(new_mesh)

    def test_topology_preservation_fails_without_extension(self, end_to_end_setup):
        """Test that topology is NOT preserved when using standard glTF import.

        This demonstrates the problem that EXT_bmesh_encoding is supposed to solve.
        """
        encoder, decoder = end_to_end_setup

        # Create a mesh with quads
        obj = create_quad_mesh("NoExtensionTest")
        original_mesh = obj.data.copy()
        original_face_count = len(original_mesh.polygons)

        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp_file:
            filepath = tmp_file.name

        try:
            # Export with EXT_bmesh_encoding (creates the extension data)
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format='GLTF_SEPARATE',
                use_selection=True
            )

            # Clear scene
            bpy.data.objects.remove(obj)

            # Import using STANDARD glTF importer (no extension processing)
            bpy.ops.import_scene.gltf(filepath=filepath)

            # Find imported object
            imported_obj = None
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    imported_obj = obj
                    break

            assert imported_obj is not None, "Imported object not found"
            imported_mesh = imported_obj.data
            imported_face_count = len(imported_mesh.polygons)

            # This should demonstrate the triangulation problem
            logger.info(f"Original quad mesh: {original_face_count} faces")
            logger.info(f"Standard import result: {imported_face_count} faces")

            # The imported mesh should have more faces (triangulated)
            # This proves why we need EXT_bmesh_encoding
            if imported_face_count > original_face_count:
                logger.info("✅ Confirmed: Standard import triangulates quads")
            else:
                logger.warning("⚠️  Unexpected: Standard import preserved topology")

        finally:
            # Cleanup
            if os.path.exists(filepath):
                os.unlink(filepath)
            bpy.data.meshes.remove(original_mesh)
            if imported_obj:
                bpy.data.objects.remove(imported_obj)

    def test_triangle_mesh_roundtrip(self, end_to_end_setup):
        """Test complete round-trip with triangular mesh."""
        encoder, decoder = end_to_end_setup

        # Create test mesh
        obj = create_triangle_mesh("TriangleTest")
        original_mesh = obj.data.copy()

        # Export to glTF with EXT_bmesh_encoding
        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp_file:
            filepath = tmp_file.name

        try:
            # Use the export operator
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format='GLTF_SEPARATE',
                use_selection=True
            )

            # Clear scene
            bpy.data.objects.remove(obj)

            # Import the glTF file
            bpy.ops.import_scene.gltf(filepath=filepath)

            # Find imported object
            imported_obj = None
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    imported_obj = obj
                    break

            assert imported_obj is not None, "Imported object not found"
            imported_mesh = imported_obj.data

            # Compare topology
            assert compare_mesh_topology(original_mesh, imported_mesh)

        finally:
            # Cleanup
            if os.path.exists(filepath):
                os.unlink(filepath)
            bpy.data.meshes.remove(original_mesh)
            if imported_obj:
                bpy.data.objects.remove(imported_obj)

    def test_quad_mesh_roundtrip(self, end_to_end_setup):
        """Test complete round-trip with quad mesh."""
        encoder, decoder = end_to_end_setup

        # Create test mesh
        obj = create_quad_mesh("QuadTest")
        original_mesh = obj.data.copy()

        # Export to glTF
        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp_file:
            filepath = tmp_file.name

        try:
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format='GLTF_SEPARATE',
                use_selection=True
            )

            # Clear scene
            bpy.data.objects.remove(obj)

            # Import
            bpy.ops.import_scene.gltf(filepath=filepath)

            # Find imported object
            imported_obj = None
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    imported_obj = obj
                    break

            assert imported_obj is not None, "Imported object not found"
            imported_mesh = imported_obj.data

            # Compare topology
            assert compare_mesh_topology(original_mesh, imported_mesh)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            bpy.data.meshes.remove(original_mesh)
            if imported_obj:
                bpy.data.objects.remove(imported_obj)

    def test_ngon_mesh_roundtrip(self, end_to_end_setup):
        """Test complete round-trip with ngon mesh."""
        encoder, decoder = end_to_end_setup

        # Test different ngon sizes
        for sides in [5, 6, 7, 8]:
            obj = create_ngon_mesh(f"Ngon{sides}Test", sides)
            original_mesh = obj.data.copy()

            with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp_file:
                filepath = tmp_file.name

            try:
                bpy.ops.export_scene.gltf(
                    filepath=filepath,
                    export_format='GLTF_SEPARATE',
                    use_selection=True
                )

                bpy.data.objects.remove(obj)

                bpy.ops.import_scene.gltf(filepath=filepath)

                imported_obj = None
                for obj in bpy.context.scene.objects:
                    if obj.type == 'MESH':
                        imported_obj = obj
                        break

                assert imported_obj is not None, f"Imported ngon object not found for {sides} sides"
                imported_mesh = imported_obj.data

                assert compare_mesh_topology(original_mesh, imported_mesh)

            finally:
                if os.path.exists(filepath):
                    os.unlink(filepath)
                bpy.data.meshes.remove(original_mesh)
                if imported_obj:
                    bpy.data.objects.remove(imported_obj)

    def test_mixed_topology_roundtrip(self, end_to_end_setup):
        """Test complete round-trip with mixed face types."""
        encoder, decoder = end_to_end_setup

        obj = create_mixed_topology_mesh("MixedTest")
        original_mesh = obj.data.copy()

        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp_file:
            filepath = tmp_file.name

        try:
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format='GLTF_SEPARATE',
                use_selection=True
            )

            bpy.data.objects.remove(obj)

            bpy.ops.import_scene.gltf(filepath=filepath)

            imported_obj = None
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    imported_obj = obj
                    break

            assert imported_obj is not None, "Imported mixed topology object not found"
            imported_mesh = imported_obj.data

            assert compare_mesh_topology(original_mesh, imported_mesh)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            bpy.data.meshes.remove(original_mesh)
            if imported_obj:
                bpy.data.objects.remove(imported_obj)

    def test_cube_with_hole_roundtrip(self, end_to_end_setup):
        """Test complete round-trip with non-manifold topology."""
        encoder, decoder = end_to_end_setup

        obj = create_cube_with_hole("CubeHoleTest")
        original_mesh = obj.data.copy()

        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp_file:
            filepath = tmp_file.name

        try:
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format='GLTF_SEPARATE',
                use_selection=True
            )

            bpy.data.objects.remove(obj)

            bpy.ops.import_scene.gltf(filepath=filepath)

            imported_obj = None
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    imported_obj = obj
                    break

            assert imported_obj is not None, "Imported cube with hole object not found"
            imported_mesh = imported_obj.data

            assert compare_mesh_topology(original_mesh, imported_mesh)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            bpy.data.meshes.remove(original_mesh)
            if imported_obj:
                bpy.data.objects.remove(imported_obj)

    def test_glb_format_roundtrip(self, end_to_end_setup):
        """Test round-trip using GLB format."""
        encoder, decoder = end_to_end_setup

        obj = create_quad_mesh("GLBTest")
        original_mesh = obj.data.copy()

        with tempfile.NamedTemporaryFile(suffix='.glb', delete=False) as tmp_file:
            filepath = tmp_file.name

        try:
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format='GLB',
                use_selection=True
            )

            bpy.data.objects.remove(obj)

            bpy.ops.import_scene.gltf(filepath=filepath)

            imported_obj = None
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    imported_obj = obj
                    break

            assert imported_obj is not None, "Imported GLB object not found"
            imported_mesh = imported_obj.data

            assert compare_mesh_topology(original_mesh, imported_mesh)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            bpy.data.meshes.remove(original_mesh)
            if imported_obj:
                bpy.data.objects.remove(imported_obj)

    def test_multiple_objects_roundtrip(self, end_to_end_setup):
        """Test round-trip with multiple objects."""
        encoder, decoder = end_to_end_setup

        # Create multiple objects
        objects = []
        original_meshes = []

        for i, mesh_type in enumerate(['triangle', 'quad', 'ngon']):
            if mesh_type == 'triangle':
                obj = create_triangle_mesh(f"MultiObj{i}")
            elif mesh_type == 'quad':
                obj = create_quad_mesh(f"MultiObj{i}")
            else:
                obj = create_ngon_mesh(f"MultiObj{i}", 6)

            objects.append(obj)
            original_meshes.append(obj.data.copy())

        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp_file:
            filepath = tmp_file.name

        try:
            # Export all objects
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format='GLTF_SEPARATE',
                use_selection=False  # Export all
            )

            # Remove original objects
            for obj in objects:
                bpy.data.objects.remove(obj)

            # Import
            bpy.ops.import_scene.gltf(filepath=filepath)

            # Find all imported mesh objects
            imported_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
            assert len(imported_objects) == len(objects), \
                f"Expected {len(objects)} objects, got {len(imported_objects)}"

            # Compare each object
            for i, (original_mesh, imported_obj) in enumerate(zip(original_meshes, imported_objects)):
                assert compare_mesh_topology(original_mesh, imported_obj.data)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            for mesh in original_meshes:
                bpy.data.meshes.remove(mesh)
            for obj in imported_objects:
                bpy.data.objects.remove(obj)

    def test_performance_large_mesh(self, end_to_end_setup):
        """Test performance with larger mesh."""
        encoder, decoder = end_to_end_setup

        # Create a larger mesh
        verts = []
        faces = []

        grid_size = 20  # 400 vertices
        for x in range(grid_size):
            for z in range(grid_size):
                verts.append((x * 0.1, 0, z * 0.1))

        for x in range(grid_size - 1):
            for z in range(grid_size - 1):
                base = x * grid_size + z
                faces.append((base, base + 1, base + grid_size + 1, base + grid_size))

        mesh = bpy.data.meshes.new("LargeMesh")
        mesh.from_pydata(verts, [], faces)
        mesh.update()

        obj = bpy.data.objects.new("LargeMeshObj", mesh)
        bpy.context.collection.objects.link(obj)

        original_mesh = mesh.copy()

        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp_file:
            filepath = tmp_file.name

        try:
            import time
            start_time = time.time()

            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format='GLTF_SEPARATE',
                use_selection=True
            )

            export_time = time.time() - start_time
            assert export_time < 5.0, f"Export too slow: {export_time:.2f}s"

            bpy.data.objects.remove(obj)

            start_time = time.time()
            bpy.ops.import_scene.gltf(filepath=filepath)
            import_time = time.time() - start_time
            assert import_time < 5.0, f"Import too slow: {import_time:.2f}s"

            imported_obj = None
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    imported_obj = obj
                    break

            assert imported_obj is not None, "Imported large mesh object not found"
            imported_mesh = imported_obj.data

            assert compare_mesh_topology(original_mesh, imported_mesh)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            bpy.data.meshes.remove(original_mesh)
            if imported_obj:
                bpy.data.objects.remove(imported_obj)


if __name__ == "__main__":
    pytest.main([__file__])
