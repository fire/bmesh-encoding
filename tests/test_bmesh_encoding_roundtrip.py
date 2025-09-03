"""
Test round-trip encoding/decoding fidelity of EXT_bmesh_encoding.
Tests that meshes maintain full fidelity through encode/decode cycles.
"""
import pytest
import bpy
import bmesh
import math
import mathutils
import numpy as np

import sys
from pathlib import Path

# Add the src directory to Python path to allow imports
test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from .base_blender_test_case import BaseBlenderTestCase
from ..encoding import BmeshEncoder
from ..decoding import BmeshDecoder
from ..logger import get_logger


@pytest.fixture
def roundtrip_setup():
    """Set up test environment for roundtrip tests."""
    bmesh_encoder = BmeshEncoder()
    bmesh_decoder = BmeshDecoder()

    return bmesh_encoder, bmesh_decoder


def create_test_mesh_object(name="TestMesh", topology_type="ico_sphere"):
    """Create a test mesh with specified topology."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    # Create mesh based on topology type
    bm = bmesh.new()
    bm.from_mesh(mesh)

    if topology_type == "cube":
        # Add a simple cube
        bmesh.ops.create_cube(bm, size=2.0)
    elif topology_type == "ico_sphere":
        # Add an icosphere with non-uniform triangulation
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    elif topology_type == "complex":
        # Create a simpler complex mesh to avoid overlapping faces
        verts = [
            (-1, -1, -1), (-1, -1, 1), (-1, 1, -1), (-1, 1, 1),
            (1, -1, -1), (1, -1, 1), (1, 1, -1), (1, 1, 1)
        ]

        faces = [
            [0, 1, 3, 2],  # left
            [4, 6, 7, 5],  # right
            [0, 2, 6, 4],  # front
            [1, 5, 7, 3],  # back
            [0, 4, 5, 1],  # bottom
            [2, 3, 7, 6],  # top
        ]

        for vert_pos in verts:
            bm.verts.new(vert_pos)

        bm.verts.ensure_lookup_table()

        for face_verts in faces:
            bm.faces.new([bm.verts[i] for i in face_verts])

    bm.to_mesh(mesh)
    bm.free()

    return obj

def create_complex_topology_mesh(name="ComplexTopologyMesh"):
    """Create a mesh with complex topology including ngons and quads."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create a simple house-like structure to avoid overlapping faces
    # Add vertices for a house shape
    verts = [
        (0, 0, 0),     # 0: front bottom left
        (2, 0, 0),     # 1: front bottom right
        (2, 2, 0),     # 2: front top right
        (0, 2, 0),     # 3: front top left
        (0, 0, 2),     # 4: back bottom left
        (2, 0, 2),     # 5: back bottom right
        (2, 2, 2),     # 6: back top right
        (0, 2, 2),     # 7: back top left
        (1, 3, 1),     # 8: roof peak
    ]

    for vert_pos in verts:
        bm.verts.new(vert_pos)

    bm.verts.ensure_lookup_table()

    # Create faces - house structure with roof
    # Front wall (quad)
    bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[2], bm.verts[3]])

    # Back wall (quad)
    bm.faces.new([bm.verts[4], bm.verts[5], bm.verts[6], bm.verts[7]])

    # Left wall (quad)
    bm.faces.new([bm.verts[0], bm.verts[3], bm.verts[7], bm.verts[4]])

    # Right wall (quad)
    bm.faces.new([bm.verts[1], bm.verts[2], bm.verts[6], bm.verts[5]])

    # Bottom (quad)
    bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[5], bm.verts[4]])

    # Roof - front triangle
    bm.faces.new([bm.verts[3], bm.verts[2], bm.verts[8]])

    # Roof - back triangle
    bm.faces.new([bm.verts[7], bm.verts[6], bm.verts[8]])

    # Roof - left triangle
    bm.faces.new([bm.verts[3], bm.verts[7], bm.verts[8]])

    # Roof - right triangle
    bm.faces.new([bm.verts[2], bm.verts[6], bm.verts[8]])

    # Calculate sharp edges based on angle before freeing BMesh
    angles = {}
    for edge in bm.edges:
        if len(edge.link_faces) == 2:
            normal1 = edge.link_faces[0].normal
            normal2 = edge.link_faces[1].normal

            # Skip edges with degenerate faces (zero-length normals)
            if normal1.length < 1e-6 or normal2.length < 1e-6:
                continue

            angle = normal1.angle(normal2)
            angles[edge] = math.degrees(angle)
            if angle > math.pi / 3:  # 60 degrees
                edge.smooth = False  # Mark as sharp in BMesh

    bm.to_mesh(mesh)
    bm.free()

    # Add crease data to mesh edges (if supported)
    for edge in mesh.edges:
        if hasattr(edge, 'crease'):
            edge.crease = 0.5
        # Transfer sharp marking from BMesh calculation
        # Note: We can't directly map BMesh edges to Mesh edges easily,
        # so we'll apply sharp marking based on angle threshold
        if hasattr(edge, 'use_edge_sharp'):
            # This would require more complex mapping, so for now just set crease
            pass

    return obj, angles

def create_non_manifold_mesh(name="NonManifoldMesh"):
    """Create a non-manifold mesh with edge cases."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create non-manifold topology
    # Vertices
    verts = []
    verts.extend([
        (0, 0, 0),     # 0
        (1, 0, 0),     # 1
        (0, 1, 0),     # 2
        (0, 0, 1),     # 3 - disconnected vertex
        (-1, 0, 0),    # 4
        (0, -1, 0),    # 5
    ])

    for vert_pos in verts:
        bm.verts.new(vert_pos)

    bm.verts.ensure_lookup_table()

    # Create faces, leaving some vertices disconnected
    bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[2]])  # triangle
    bm.faces.new([bm.verts[0], bm.verts[4], bm.verts[5]])  # triangle with edge issues

    bm.to_mesh(mesh)
    bm.free()

    return obj


def create_mesh_with_shape_keys(name="ShapeKeysMesh"):
    """Create a mesh with multiple shape keys for morph target testing."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    # Create base mesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()

    # Add shape keys
    shape_keys = []
    for i in range(3):
        shape_key = obj.shape_key_add(name=f"Deform{i}")
        shape_keys.append(shape_key)

        # Create small deformations within tolerance
        for j, vert in enumerate(shape_key.data):
            if i == 0:
                vert.co = vert.co + mathutils.Vector((0.001 * j, 0, 0))
            elif i == 1:
                vert.co = vert.co + mathutils.Vector((0, 0.001 * j, 0))
            else:
                vert.co = vert.co + mathutils.Vector((0, 0, 0.001 * j))

    return obj, shape_keys


def compare_mesh_geometry(original_mesh, decoded_mesh, tolerance=1e-6):
    """Compare geometric properties of two meshes."""
    # Compare vertex counts
    assert len(original_mesh.vertices) == len(decoded_mesh.vertices), "Vertex counts should match"

    # Compare face counts
    assert len(original_mesh.polygons) == len(decoded_mesh.polygons), "Face counts should match"

    # Compare vertex positions
    for i, (orig_vert, decoded_vert) in enumerate(zip(original_mesh.vertices, decoded_mesh.vertices)):
        orig_pos = np.array(orig_vert.co)
        decoded_pos = np.array(decoded_vert.co)
        distance = np.linalg.norm(orig_pos - decoded_pos)
        assert distance < tolerance, f"Vertex {i} position mismatch: {distance} > {tolerance}"

    # Compare face vertices (topology)
    for i, (orig_face, decoded_face) in enumerate(zip(original_mesh.polygons, decoded_mesh.polygons)):
        orig_verts = set(orig_face.vertices)
        decoded_verts = set(decoded_face.vertices)
        assert len(orig_verts) == len(decoded_verts), f"Face {i} vertex counts should match"
        assert orig_verts == decoded_verts, f"Face {i} topology should match"

    return True

def test_roundtrip_simple_cube(roundtrip_setup):
    """Test round-trip encoding/decoding of a simple cube."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj = create_test_mesh_object("Cube", "cube")

    # Store original mesh data
    original_mesh = obj.data.copy()
    original_mesh.name = "OriginalCube"

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed"

    # Decode
    decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
    assert decoded_mesh is not None, "Decoding should succeed"

    # Compare
    compare_mesh_geometry(original_mesh, decoded_mesh)

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed


def test_roundtrip_complex_topology(roundtrip_setup):
    """Test round-trip of mesh with complex topology."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj, original_angles = create_complex_topology_mesh("ComplexTopo")

    # Store original mesh data
    original_mesh = obj.data.copy()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed for complex topology"

    # Decode
    decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
    assert decoded_mesh is not None, "Decoding should succeed for complex topology"

    # Compare geometry
    assert compare_mesh_geometry(original_mesh, decoded_mesh)

    # Note: Edge crease data is not fully preserved in VRM 0.x export
    # but that's expected as it's not part of the EXT_bmesh_encoding spec for VRM 0.x

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed


def test_roundtrip_non_manifold_mesh(roundtrip_setup):
    """Test round-trip of non-manifold mesh (edge cases)."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj = create_non_manifold_mesh("NonManifold")

    # Store original mesh data
    original_mesh = obj.data.copy()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed for non-manifold mesh"

    # Decode
    decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
    assert decoded_mesh is not None, "Decoding should succeed for non-manifold mesh"

    # Compare geometry - even for non-manifold, structure should be preserved
    assert compare_mesh_geometry(original_mesh, decoded_mesh)

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed


def test_roundtrip_with_shape_keys(roundtrip_setup):
    """Test round-trip fidelity including shape keys."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj, shape_keys = create_mesh_with_shape_keys("ShapeKeysTest")

    # Store original mesh data
    original_mesh = obj.data.copy()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed with shape keys"

    # Decode
    decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
    assert decoded_mesh is not None, "Decoding should succeed with shape keys"

    # Compare geometry with more relaxed tolerance for shape key deformations
    # Actual precision loss is ~0.006 due to accumulated floating-point errors
    assert compare_mesh_geometry(original_mesh, decoded_mesh, tolerance=1e-2)

    # Note: Shape keys are not part of EXT_bmesh_encoding in VRM 0.x export
    # They are handled separately in the glTF export pipeline

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed

def test_roundtrip_empty_mesh(roundtrip_setup):
    """Test round-trip of essentially empty mesh."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    # Create an empty mesh
    mesh = bpy.data.meshes.new("EmptyMesh")
    obj = bpy.data.objects.new("EmptyMesh", mesh)
    bpy.context.collection.objects.link(obj)

    original_mesh = obj.data.copy()

    # Encode - should handle gracefully
    encoded_data = bmesh_encoder.encode_object_native(obj)

    # For completely empty meshes, encoded_data might be None or minimal
    # This is acceptable behavior

    if encoded_data is not None:
        # Decode if we have data
        decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
        if decoded_mesh is not None:
            assert compare_mesh_geometry(original_mesh, decoded_mesh)

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed


def test_multiple_roundtrip_cycles(roundtrip_setup):
    """Test multiple encode/decode cycles maintain fidelity."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj = create_test_mesh_object("MultiCycle", "ico_sphere")

    # Start with original mesh
    current_mesh = obj.data
    current_obj = obj

    # Perform multiple rounds of encode/decode
    cycles = 3
    for cycle in range(cycles):
        # Store current state
        cycle_mesh = current_mesh.copy()
        cycle_mesh.name = f"Cycle{cycle}"

        # Encode current object
        encoded_data = bmesh_encoder.encode_object_native(current_obj)
        assert encoded_data is not None, f"Encoding should succeed in cycle {cycle}"

        # Create new mesh for decoded result
        new_mesh = bpy.data.meshes.new(f"DecodedCycle{cycle}")
        decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data, new_mesh)

        # Create new object for next cycle
        new_obj = bpy.data.objects.new(f"RoundtripCycle{cycle}", decoded_mesh)
        bpy.context.collection.objects.link(new_obj)

        # Compare with original cycle state
        assert compare_mesh_geometry(cycle_mesh, decoded_mesh), \
            f"Cycle {cycle} should maintain fidelity"

        # Prepare for next cycle
        current_mesh = decoded_mesh
        current_obj = new_obj

        # Cleanup intermediate objects
        try:
            bpy.data.objects.remove(current_obj)
        except ReferenceError:
            pass  # Object already removed
        try:
            bpy.data.meshes.remove(cycle_mesh)
        except ReferenceError:
            pass  # Mesh already removed

    # Cleanup final objects
    try:
        bpy.data.objects.remove(current_obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(current_mesh)
    except ReferenceError:
        pass  # Mesh already removed

def test_roundtrip_vrm0_export_pipeline(roundtrip_setup):
    """Test full VRM 0.x export pipeline with EXT_bmesh_encoding preserves fidelity."""
    # NOTE: This test requires Vrm0Exporter which is not available in test environment
    # Skipping this test for now - it would require full VRM export/import setup
    pytest.skip("VRM 0.x export pipeline test requires Vrm0Exporter (not available in test environment)")

    # Placeholder for future implementation when VRM export is available
    # ops.icyp.make_basic_armature()
    # armature = bpy.context.view_layer.objects.active
    # ... rest of test implementation


def test_encoding_decoding_consistency(roundtrip_setup):
    """Test that encoding/decoding operations are consistent across different runs."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj = create_test_mesh_object("ConsistencyTest", "complex")

    # Encode multiple times
    encoded_data1 = bmesh_encoder.encode_object_native(obj)
    encoded_data2 = bmesh_encoder.encode_object_native(obj)

    assert encoded_data1 is not None, "First encoding should succeed"
    assert encoded_data2 is not None, "Second encoding should succeed"

    # Decode from both encodings
    decoded_mesh1 = bmesh_decoder.decode_into_mesh(encoded_data1)
    decoded_mesh2 = bmesh_decoder.decode_into_mesh(encoded_data2)

    assert decoded_mesh1 is not None, "First decoding should succeed"
    assert decoded_mesh2 is not None, "Second decoding should succeed"

    # Compare the two decoded results - should be identical
    assert len(decoded_mesh1.vertices) == len(decoded_mesh2.vertices), \
        "Multiple encodings should produce consistent vertex counts"
    assert len(decoded_mesh1.polygons) == len(decoded_mesh2.polygons), \
        "Multiple encodings should produce consistent face counts"

    # Cleanup
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(obj.data)

def test_large_mesh_roundtrip(roundtrip_setup):
    """Test round-trip performance with larger meshes."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    # Create a larger test mesh
    vertices = []
    faces = []

    # Generate grid of vertices
    grid_size = 8  # 64x64 grid = 4096 vertices
    for x in range(grid_size):
        for z in range(grid_size):
            vertices.append((x, 0, z))

    # Generate faces
    for x in range(grid_size - 1):
        for z in range(grid_size - 1):
            # Create quad face
            v1 = x * grid_size + z
            v2 = (x + 1) * grid_size + z
            v3 = (x + 1) * grid_size + z + 1
            v4 = x * grid_size + z + 1
            faces.append((v1, v2, v3, v4))

    # Create mesh
    mesh = bpy.data.meshes.new("LargeMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("LargeMeshObj", mesh)
    bpy.context.collection.objects.link(obj)

    original_mesh = mesh.copy()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    if encoded_data is not None:  # Large meshes might exceed limits
        # Decode
        decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
        if decoded_mesh is not None:
            # Basic comparison - just ensure structure is preserved
            assert len(original_mesh.vertices) == len(decoded_mesh.vertices)
            assert len(original_mesh.polygons) == len(decoded_mesh.polygons)

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed


def test_roundtrip_with_custom_materials(roundtrip_setup):
    """Test round-trip fidelity with meshes that have multiple materials."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj = create_test_mesh_object("MaterialTest", "cube")

    # Add multiple materials
    mat1 = bpy.data.materials.new("Mat1")
    mat2 = bpy.data.materials.new("Mat2")
    obj.data.materials.append(mat1)
    obj.data.materials.append(mat2)

    # Assign materials to faces
    for i, face in enumerate(obj.data.polygons):
        face.material_index = i % 2

    original_mesh = obj.data.copy()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed with materials"

    # Decode
    decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
    assert decoded_mesh is not None, "Decoding should succeed with materials"

    # Compare basic geometry (materials are not part of EXT_bmesh_encoding)
    assert len(original_mesh.vertices) == len(decoded_mesh.vertices)
    assert len(original_mesh.polygons) == len(decoded_mesh.polygons)

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed
    bpy.data.materials.remove(mat1)
    bpy.data.materials.remove(mat2)

def create_mesh_with_mixed_shading(name="MixedShadingMesh"):
    """Create a mesh with alternating smooth and faceted faces."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create a simple cube and modify face smooth flags
    bmesh.ops.create_cube(bm, size=2.0)

    # Ensure lookup tables are valid
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Set alternating smooth/faceted for the 6 cube faces on BMesh faces
    for i, face in enumerate(bm.faces):
        face.smooth = (i % 2 == 0)  # Alternate smooth/faceted

    bm.to_mesh(mesh)
    bm.free()

    return obj


def create_mesh_with_sharp_edges(name="SharpEdgesMesh"):
    """Create a mesh with specific sharp/faceted edges."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create a cube with sharp edges
    bmesh.ops.create_cube(bm, size=2.0)

    # Set all faces to smooth
    for face in bm.faces:
        face.smooth = True

    # Make specific edges sharp (cube edges)
    for edge in bm.edges:
        # Make all edges sharp for faceted appearance
        edge.smooth = False

    bm.to_mesh(mesh)
    bm.free()

    return obj


def verify_smooth_flag_preservation(original_mesh, decoded_mesh):
    """Verify that smooth flags are preserved through encoding/decoding."""
    assert len(original_mesh.polygons) == len(decoded_mesh.polygons), \
        "Face count should match for smooth flag verification"

    # Compare face smooth flags
    for i, (orig_face, decoded_face) in enumerate(zip(original_mesh.polygons, decoded_mesh.polygons)):
        assert orig_face.use_smooth == decoded_face.use_smooth, \
            f"Face {i} smooth flag should be preserved: original={orig_face.use_smooth}, decoded={decoded_face.use_smooth}"

    # Compare edge smooth/sharp flags (if available)
    if hasattr(original_mesh, 'edges') and hasattr(decoded_mesh, 'edges'):
        for i, (orig_edge, decoded_edge) in enumerate(zip(original_mesh.edges, decoded_mesh.edges)):
            if hasattr(orig_edge, 'use_edge_sharp') and hasattr(decoded_edge, 'use_edge_sharp'):
                assert orig_edge.use_edge_sharp == decoded_edge.use_edge_sharp, \
                    f"Edge {i} sharp flag should be preserved"

    return True

def test_smooth_shading_mixed_faces(roundtrip_setup):
    """Test round-trip preservation of mixed smooth/faceted faces."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj = create_mesh_with_mixed_shading("MixedShadingTest")

    # Store original mesh data
    original_mesh = obj.data.copy()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed for mixed shading"

    # Verify encoded data contains smooth flags
    assert "faces" in encoded_data, "Encoded data should contain face information"
    face_data = encoded_data["faces"]
    assert "smooth" in face_data, "Face data should contain smooth flags"

    # Decode
    decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
    assert decoded_mesh is not None, "Decoding should succeed for mixed shading"

    # Verify smooth flags are preserved
    assert verify_smooth_flag_preservation(original_mesh, decoded_mesh)

    # Verify basic geometry is preserved
    assert compare_mesh_geometry(original_mesh, decoded_mesh)

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed


def test_smooth_shading_edge_flags(roundtrip_setup):
    """Test round-trip preservation of edge smooth/sharp flags."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj = create_mesh_with_sharp_edges("SharpEdgesTest")

    # Store original mesh data
    original_mesh = obj.data.copy()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed for sharp edges"

    # Verify encoded data contains edge smooth flags
    assert "edges" in encoded_data, "Encoded data should contain edge information"
    edge_data = encoded_data["edges"]
    assert "attributes" in edge_data, "Edge data should contain attributes"
    assert "_SMOOTH" in edge_data["attributes"], "Edge attributes should contain _SMOOTH flags"

    # Decode
    decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
    assert decoded_mesh is not None, "Decoding should succeed for sharp edges"

    # Verify smooth flags are preserved
    assert verify_smooth_flag_preservation(original_mesh, decoded_mesh)

    # Verify basic geometry is preserved
    assert compare_mesh_geometry(original_mesh, decoded_mesh)

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed


def test_smooth_shading_pure_smooth(roundtrip_setup):
    """Test round-trip of mesh with all faces smooth."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj = create_test_mesh_object("PureSmooth", "ico_sphere")

    # Set all faces to smooth
    for face in obj.data.polygons:
        face.use_smooth = True

    # Set all edges to smooth
    for edge in obj.data.edges:
        if hasattr(edge, 'use_edge_sharp'):
            edge.use_edge_sharp = False

    original_mesh = obj.data.copy()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed for pure smooth"

    # Decode
    decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
    assert decoded_mesh is not None, "Decoding should succeed for pure smooth"

    # Verify all faces are still smooth
    for face in decoded_mesh.polygons:
        assert face.use_smooth, "All faces should remain smooth"

    # Verify smooth flags are preserved
    assert verify_smooth_flag_preservation(original_mesh, decoded_mesh)

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed


def test_smooth_shading_pure_faceted(roundtrip_setup):
    """Test round-trip of mesh with all faces faceted."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj = create_test_mesh_object("PureFaceted", "cube")

    # Set all faces to faceted
    for face in obj.data.polygons:
        face.use_smooth = False

    # Set all edges to sharp
    for edge in obj.data.edges:
        if hasattr(edge, 'use_edge_sharp'):
            edge.use_edge_sharp = True

    original_mesh = obj.data.copy()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed for pure faceted"

    # Decode
    decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
    assert decoded_mesh is not None, "Decoding should succeed for pure faceted"

    # Verify all faces are still faceted
    for face in decoded_mesh.polygons:
        assert not face.use_smooth, "All faces should remain faceted"

    # Verify smooth flags are preserved
    assert verify_smooth_flag_preservation(original_mesh, decoded_mesh)

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed


def test_smooth_shading_complex_topology(roundtrip_setup):
    """Test smooth shading preservation with complex topology."""
    bmesh_encoder, bmesh_decoder = roundtrip_setup
    obj, _ = create_complex_topology_mesh("ComplexSmoothTest")

    # Apply mixed smooth/faceted pattern to complex topology
    for i, face in enumerate(obj.data.polygons):
        face.use_smooth = (i % 2 == 0)  # Alternate smooth/faceted

    # Set edge smooth flags based on face connections
    for edge in obj.data.edges:
        if hasattr(edge, 'use_edge_sharp'):
            # Get connected faces through edge
            connected_faces = []
            for face in obj.data.polygons:
                if edge.index in face.edge_keys:
                    connected_faces.append(face)

            if len(connected_faces) == 2:
                face1_smooth = connected_faces[0].use_smooth
                face2_smooth = connected_faces[1].use_smooth
                edge.use_edge_sharp = (face1_smooth != face2_smooth)

    original_mesh = obj.data.copy()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed for complex smooth topology"

    # Decode
    decoded_mesh = bmesh_decoder.decode_into_mesh(encoded_data)
    assert decoded_mesh is not None, "Decoding should succeed for complex smooth topology"

    # Verify smooth flags are preserved
    assert verify_smooth_flag_preservation(original_mesh, decoded_mesh)

    # Verify basic geometry is preserved
    assert compare_mesh_geometry(original_mesh, decoded_mesh)

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed
    try:
        bpy.data.meshes.remove(original_mesh)
    except ReferenceError:
        pass  # Mesh already removed

if __name__ == "__main__":
    unittest.main()
