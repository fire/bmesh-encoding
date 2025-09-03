"""
Test EXT_bmesh_encoding support for VRM 0.x export.
Tests encoding/decoding fidelity and proper integration with VRM 0.x exporter.
"""
import pytest
import tempfile
import json
import bpy
from pathlib import Path
import bmesh
import mathutils

import sys
from pathlib import Path

# Add the src directory to Python path to allow imports
test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# Import mock VRM module first to set up sys.modules
from .mock_vrm import mock_vrm

from .base_blender_test_case import BaseBlenderTestCase
from ..encoding import BmeshEncoder
from ..decoding import BmeshDecoder
from ..logger import get_logger

# Import mock VRM classes after sys.modules setup
from .mock_vrm import MockVrm0Exporter as Vrm0Exporter
from .mock_vrm import mock_parse_glb as parse_glb

# Replace mock placeholders with real implementations
mock_vrm.editor.bmesh_encoding.BmeshEncoder = BmeshEncoder
mock_vrm.editor.bmesh_encoding.BmeshDecoder = BmeshDecoder
mock_vrm.common.logger.get_logger = get_logger

logger = get_logger(__name__)


@pytest.fixture
def vrm0_test_setup():
    """Set up test environment for VRM 0.x tests."""
    # Create test armature fixture
    armature_data = bpy.data.armatures.new("TestArmature")
    armature = bpy.data.objects.new("TestArmature", armature_data)
    bpy.context.collection.objects.link(armature)
    bpy.context.view_layer.objects.active = armature

    encoder = BmeshEncoder()
    decoder = BmeshDecoder()

    yield armature, encoder, decoder

    # Cleanup
    bpy.data.objects.remove(armature)
    bpy.data.armatures.remove(armature_data)

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
        # Create a simpler complex mesh to avoid duplicate face issues
        # Use a 2x2x2 grid of vertices (8 vertices total)
        verts = [
            (-1, -1, -1),  # 0
            (1, -1, -1),   # 1
            (1, 1, -1),    # 2
            (-1, 1, -1),   # 3
            (-1, -1, 1),   # 4
            (1, -1, 1),    # 5
            (1, 1, 1),     # 6
            (-1, 1, 1),    # 7
        ]

        # Define faces for a cube (6 faces, each with 4 vertices)
        faces = [
            [0, 1, 2, 3],  # front
            [4, 5, 6, 7],  # back
            [0, 1, 5, 4],  # bottom
            [2, 3, 7, 6],  # top
            [0, 3, 7, 4],  # left
            [1, 2, 6, 5],  # right
        ]

        for vert_pos in verts:
            bm.verts.new(vert_pos)
        bm.verts.ensure_lookup_table()
        for face_verts in faces:
            bm.faces.new([bm.verts[i] for i in face_verts])

    bm.to_mesh(mesh)
    bm.free()

    return obj

def test_export_ext_bmesh_encoding_parameter(vrm0_test_setup):
    """Test that VRM 0.x exporter accepts and uses export_ext_bmesh_encoding parameter."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object()

    # Test with EXT_bmesh_encoding enabled
    exporter_enabled = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=True
    )

    # Test with EXT_bmesh_encoding disabled
    exporter_disabled = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=False
    )

    assert exporter_enabled.export_ext_bmesh_encoding is True
    assert exporter_disabled.export_ext_bmesh_encoding is False

    # Cleanup
    try:
        bpy.data.objects.remove(obj)
    except ReferenceError:
        pass  # Object already removed
    try:
        bpy.data.meshes.remove(obj.data)
    except ReferenceError:
        pass  # Mesh already removed

def test_ext_bmesh_encoding_extension_in_output(vrm0_test_setup):
    """Test that EXT_bmesh_encoding extension appears in glTF output when enabled."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("TestMesh", "ico_sphere")

    # Export with EXT_bmesh_encoding enabled
    exporter = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=True
    )

    result = exporter.export_vrm()
    assert result is not None, "Export should succeed"

    # Parse the glb result using existing parse_glb function
    gltf_data, _ = parse_glb(result)

    # Check that EXT_bmesh_encoding is in extensionsUsed
    assert "EXT_bmesh_encoding" in gltf_data.get("extensionsUsed", []), \
        "EXT_bmesh_encoding should be in extensionsUsed when enabled"

    # Find the mesh and check for extension
    meshes = gltf_data.get("meshes", [])
    found_extension = False
    for mesh in meshes:
        if mesh.get("name") == obj.data.name or mesh.get("name") == obj.name:
            primitives = mesh.get("primitives", [])
            for primitive in primitives:
                extensions = primitive.get("extensions", {})
                if "EXT_bmesh_encoding" in extensions:
                    found_extension = True
                    break
            break

    assert found_extension, "EXT_bmesh_encoding should be present in mesh primitives"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)

def test_ext_bmesh_encoding_disabled_behavior(vrm0_test_setup):
    """Test that EXT_bmesh_encoding extension does not appear when disabled."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("TestMesh", "complex")

    # Export with EXT_bmesh_encoding disabled
    exporter = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=False
    )

    result = exporter.export_vrm()
    assert result is not None, "Export should succeed"

    # Parse the glb result using existing parse_glb function
    gltf_data, _ = parse_glb(result)

    # Check that EXT_bmesh_encoding is NOT in extensionsUsed
    extensions_used = gltf_data.get("extensionsUsed", [])
    assert "EXT_bmesh_encoding" not in extensions_used, \
        "EXT_bmesh_encoding should not be in extensionsUsed when disabled"

    # Verify no mesh primitives have the extension
    meshes = gltf_data.get("meshes", [])
    for mesh in meshes:
        if mesh.get("name") == obj.data.name or mesh.get("name") == obj.name:
            primitives = mesh.get("primitives", [])
            for primitive in primitives:
                extensions = primitive.get("extensions", {})
                assert "EXT_bmesh_encoding" not in extensions, \
                    "EXT_bmesh_encoding should not be in primitive extensions when disabled"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)

def test_bmesh_encoding_fidelity_cube(vrm0_test_setup):
    """Test encoding/decoding fidelity for a simple cube mesh."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("CubeMesh", "cube")

    # Encode the mesh
    encoded_data = encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed"

    # Test that encoded data contains expected structures
    assert "vertices" in encoded_data, "Encoded data should contain vertex information"
    assert "faces" in encoded_data, "Encoded data should contain face information"
    assert "loops" in encoded_data, "Encoded data should contain loop information"

    # Decode and compare
    decoded_bmesh = decoder.decode_gltf_extension_to_bmesh(encoded_data, None)
    assert decoded_bmesh is not None, "Decoding should succeed"

    # Convert BMesh to Blender mesh for comparison
    decoded_mesh = bpy.data.meshes.new("DecodedMesh")
    decoder.apply_bmesh_to_blender_mesh(decoded_bmesh, decoded_mesh)

    # Compare basic properties
    original_mesh = obj.data
    assert len(original_mesh.vertices) == len(decoded_mesh.vertices), \
        "Number of vertices should match"
    assert len(original_mesh.polygons) == len(decoded_mesh.polygons), \
        "Number of faces should match"

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
        bpy.data.meshes.remove(decoded_mesh)
    except ReferenceError:
        pass  # Mesh already removed

def test_bmesh_encoding_fidelity_sphere(vrm0_test_setup):
    """Test encoding/decoding fidelity for an icosphere with complex topology."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("SphereMesh", "ico_sphere")

    # Encode the mesh
    encoded_data = encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed for complex topology"

    # Decode and compare
    decoded_bmesh = decoder.decode_gltf_extension_to_bmesh(encoded_data, None)
    assert decoded_bmesh is not None, "Decoding should succeed for complex topology"

    # Convert BMesh to Blender mesh for comparison
    decoded_mesh = bpy.data.meshes.new("DecodedSphereMesh")
    decoder.apply_bmesh_to_blender_mesh(decoded_bmesh, decoded_mesh)

    original_mesh = obj.data
    # For an icosphere, we expect the same number of vertices and faces
    assert len(original_mesh.vertices) == len(decoded_mesh.vertices), \
        "Vertex count should match for sphere"
    assert len(original_mesh.polygons) == len(decoded_mesh.polygons), \
        "Face count should match for sphere"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)
    bpy.data.meshes.remove(decoded_mesh)

def test_bmesh_encoding_fidelity_complex_mesh(vrm0_test_setup):
    """Test encoding/decoding fidelity for a complex mesh with mixed topology."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("ComplexMesh", "complex")

    # Encode the mesh
    encoded_data = encoder.encode_object_native(obj)
    assert encoded_data is not None, "Encoding should succeed for mixed topology"

    # Decode and compare
    decoded_bmesh = decoder.decode_gltf_extension_to_bmesh(encoded_data, None)
    assert decoded_bmesh is not None, "Decoding should succeed for mixed topology"

    # Convert BMesh to Blender mesh for comparison
    decoded_mesh = bpy.data.meshes.new("DecodedComplexMesh")
    decoder.apply_bmesh_to_blender_mesh(decoded_bmesh, decoded_mesh)

    original_mesh = obj.data
    assert len(original_mesh.vertices) == len(decoded_mesh.vertices), \
        "Vertex count should match for complex mesh"
    assert len(original_mesh.polygons) == len(decoded_mesh.polygons), \
        "Face count should match for complex mesh"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)
    bpy.data.meshes.remove(decoded_mesh)

def test_ext_bmesh_encoding_buffer_view_creation(vrm0_test_setup):
    """Test that buffer views are properly created for EXT_bmesh_encoding data."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("BufferTestMesh", "ico_sphere")

    # Export with EXT_bmesh_encoding enabled
    exporter = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=True
    )

    result = exporter.export_vrm()
    assert result is not None, "Export should succeed"

    # Parse the glb result using existing parse_glb function
    gltf_data, _ = parse_glb(result)

    # Find EXT_bmesh_encoding data in mesh primitives
    meshes = gltf_data.get("meshes", [])
    ext_bmesh_data = None
    for mesh in meshes:
        primitives = mesh.get("primitives", [])
        for primitive in primitives:
            extensions = primitive.get("extensions", {})
            if "EXT_bmesh_encoding" in extensions:
                ext_bmesh_data = extensions["EXT_bmesh_encoding"]
                break
        if ext_bmesh_data:
            break

    assert ext_bmesh_data is not None, "Should find EXT_bmesh_encoding data"

    # Verify buffer views are referenced
    buffer_views = gltf_data.get("bufferViews", [])
    if ext_bmesh_data:
        # Check that all referenced buffer views exist
        for key, accessor_index in ext_bmesh_data.items():
            if isinstance(accessor_index, int):
                if key.endswith("Accessor"):
                    accessor = gltf_data.get("accessors", [])[accessor_index]
                    buffer_view_index = accessor.get("bufferView")
                    assert buffer_view_index is not None, f"Accessor {accessor_index} should have bufferView"
                    assert buffer_view_index < len(buffer_views), \
                        f"Buffer view index {buffer_view_index} should exist"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)

def test_ext_bmesh_encoding_multiple_meshes(vrm0_test_setup):
    """Test EXT_bmesh_encoding with multiple meshes in the same export."""
    armature, encoder, decoder = vrm0_test_setup
    # Create multiple mesh objects
    obj1 = create_test_mesh_object("Mesh1", "cube")
    obj2 = create_test_mesh_object("Mesh2", "ico_sphere")
    obj3 = create_test_mesh_object("Mesh3", "complex")

    # Export with EXT_bmesh_encoding enabled
    exporter = Vrm0Exporter(
        bpy.context,
        [obj1, obj2, obj3],
        armature,
        export_ext_bmesh_encoding=True
    )

    result = exporter.export_vrm()
    assert result is not None, "Export should succeed with multiple meshes"

    # Parse the glb result using existing parse_glb function
    gltf_data, _ = parse_glb(result)

    # Verify EXT_bmesh_encoding extension is present
    assert "EXT_bmesh_encoding" in gltf_data.get("extensionsUsed", [])

    # Count meshes with EXT_bmesh_encoding
    meshes = gltf_data.get("meshes", [])
    ext_bmesh_count = 0
    for mesh in meshes:
        primitives = mesh.get("primitives", [])
        for primitive in primitives:
            if "EXT_bmesh_encoding" in primitive.get("extensions", {}):
                ext_bmesh_count += 1
                break

    # Should have extensions in all 3 meshes
    assert ext_bmesh_count == 3, "All meshes should have EXT_bmesh_encoding when enabled"

    # Cleanup
    mesh_data1 = obj1.data  # Store references before removing objects
    mesh_data2 = obj2.data
    mesh_data3 = obj3.data
    bpy.data.objects.remove(obj1)
    bpy.data.objects.remove(obj2)
    bpy.data.objects.remove(obj3)
    bpy.data.meshes.remove(mesh_data1)
    bpy.data.meshes.remove(mesh_data2)
    bpy.data.meshes.remove(mesh_data3)

def test_ext_bmesh_encoding_backwards_compatibility(vrm0_test_setup):
    """Test that exporting without EXT_bmesh_encoding produces compatible output."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("CompatMesh", "ico_sphere")

    # Export with EXT_bmesh_encoding disabled
    exporter_disabled = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=False
    )

    result_disabled = exporter_disabled.export_vrm()
    assert result_disabled is not None, "Export should succeed without EXT_bmesh_encoding"

    # Parse and verify valid glTF using existing parse_glb function
    gltf_data, _ = parse_glb(result_disabled)

    # Verify no EXT_bmesh_encoding
    assert "EXT_bmesh_encoding" not in gltf_data.get("extensionsUsed", [])

    # Verify standard VRM 0.x structure is present
    assert "extensions" in gltf_data
    assert "VRM" in gltf_data["extensions"]
    assert gltf_data["extensions"]["VRM"]["specVersion"] == "0.0"

    # Verify meshes exist and are valid
    meshes = gltf_data.get("meshes", [])
    assert len(meshes) > 0, "Should have at least one mesh"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)

def test_ext_bmesh_encoding_edge_case_empty_mesh(vrm0_test_setup):
    """Test EXT_bmesh_encoding handling of edge cases like empty meshes."""
    armature, encoder, decoder = vrm0_test_setup
    # Add an empty mesh object (no geometry)
    obj = bpy.data.objects.new("EmptyMesh", bpy.data.meshes.new("EmptyMesh"))
    bpy.context.collection.objects.link(obj)

    # Export with EXT_bmesh_encoding enabled
    exporter = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=True
    )

    # This should not fail even with empty mesh
    result = exporter.export_vrm()
    assert result is not None, "Export should succeed even with empty mesh"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)

def test_ext_bmesh_encoding_edge_case_multiple_materials(vrm0_test_setup):
    """Test EXT_bmesh_encoding with meshes having multiple materials."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("MultiMatMesh", "cube")

    # Add a second material
    mat2 = bpy.data.materials.new("Material2")
    obj.data.materials.append(mat2)

    # Split faces between materials
    for i, face in enumerate(obj.data.polygons):
        face.material_index = i % 2

    # Export with EXT_bmesh_encoding enabled
    exporter = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=True
    )

    result = exporter.export_vrm()
    assert result is not None, "Export should succeed with multiple materials"

    # Parse and verify using existing parse_glb function
    gltf_data, _ = parse_glb(result)

    # Verify EXT_bmesh_encoding is present
    assert "EXT_bmesh_encoding" in gltf_data.get("extensionsUsed", [])

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)
    bpy.data.materials.remove(mat2)

def test_ext_bmesh_encoding_mesh_with_shape_keys(vrm0_test_setup):
    """Test EXT_bmesh_encoding with meshes that have shape keys."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("ShapeMesh", "cube")

    # Add a shape key
    shape_key = obj.shape_key_add(name="Deformed")
    shape_key.keyframe_insert("value", frame=1)

    # Modify the shape key
    for i, vert in enumerate(shape_key.data):
        vert.co = vert.co + mathutils.Vector((0.1 * i, 0.1 * i, 0.1 * i))

    # Export with EXT_bmesh_encoding enabled
    exporter = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=True
    )

    result = exporter.export_vrm()
    assert result is not None, "Export should succeed with shape keys"

    # Parse and verify using existing parse_glb function
    gltf_data, _ = parse_glb(result)

    # Verify EXT_bmesh_encoding with shape keys
    assert "EXT_bmesh_encoding" in gltf_data.get("extensionsUsed", [])

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)

def test_ext_bmesh_encoding_smooth_shading_preservation(vrm0_test_setup):
    """Test that EXT_bmesh_encoding preserves smooth/faceted shading in VRM 0.x export."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("SmoothTestMesh", "ico_sphere")

    # Apply mixed smooth/faceted shading
    for i, face in enumerate(obj.data.polygons):
        face.use_smooth = (i % 2 == 0)  # Alternate smooth/faceted

    # Set edge sharp flags based on face connections (if supported)
    for edge in obj.data.edges:
        if hasattr(edge, 'use_edge_sharp'):
            # Get connected faces through edge (Blender API compatibility)
            connected_faces = []
            for face in obj.data.polygons:
                if edge.index in face.edge_keys:
                    connected_faces.append(face)

            if len(connected_faces) == 2:
                face1_smooth = connected_faces[0].use_smooth
                face2_smooth = connected_faces[1].use_smooth
                edge.use_edge_sharp = (face1_smooth != face2_smooth)

    # Export with EXT_bmesh_encoding enabled
    exporter = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=True
    )

    result = exporter.export_vrm()
    assert result is not None, "Export should succeed with smooth shading"

    # Parse the glb result
    gltf_data, _ = parse_glb(result)

    # Verify EXT_bmesh_encoding extension is present
    assert "EXT_bmesh_encoding" in gltf_data.get("extensionsUsed", [])

    # Find EXT_bmesh_encoding data in mesh primitives
    meshes = gltf_data.get("meshes", [])
    ext_bmesh_data = None
    for mesh in meshes:
        primitives = mesh.get("primitives", [])
        for primitive in primitives:
            extensions = primitive.get("extensions", {})
            if "EXT_bmesh_encoding" in extensions:
                ext_bmesh_data = extensions["EXT_bmesh_encoding"]
                break
        if ext_bmesh_data:
            break

    assert ext_bmesh_data is not None, "Should find EXT_bmesh_encoding data"

    # Verify smooth flags are present in the encoded data
    assert "faces" in ext_bmesh_data, "Should have face data"
    face_data = ext_bmesh_data["faces"]
    assert "smooth" in face_data, "Face data should contain smooth flags"

    # Verify edge smooth flags are present
    assert "edges" in ext_bmesh_data, "Should have edge data"
    edge_data = ext_bmesh_data["edges"]
    assert "attributes" in edge_data, "Edge data should contain attributes"
    assert "_SMOOTH" in edge_data["attributes"], "Edge attributes should contain _SMOOTH flags"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)

def test_ext_bmesh_encoding_pure_smooth_mesh(vrm0_test_setup):
    """Test EXT_bmesh_encoding with a mesh that has all faces set to smooth."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("PureSmoothMesh", "cube")

    # Set all faces to smooth
    for face in obj.data.polygons:
        face.use_smooth = True

    # Set all edges to smooth
    for edge in obj.data.edges:
        if hasattr(edge, 'use_edge_sharp'):
            edge.use_edge_sharp = False

    # Export with EXT_bmesh_encoding enabled
    exporter = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=True
    )

    result = exporter.export_vrm()
    assert result is not None, "Export should succeed with pure smooth mesh"

    # Parse and verify
    gltf_data, _ = parse_glb(result)

    # Verify EXT_bmesh_encoding is present
    assert "EXT_bmesh_encoding" in gltf_data.get("extensionsUsed", [])

    # Find and verify smooth flags
    meshes = gltf_data.get("meshes", [])
    for mesh in meshes:
        primitives = mesh.get("primitives", [])
        for primitive in primitives:
            extensions = primitive.get("extensions", {})
            if "EXT_bmesh_encoding" in extensions:
                ext_data = extensions["EXT_bmesh_encoding"]
                if "faces" in ext_data and "smooth" in ext_data["faces"]:
                    # Verify smooth flags are present (we can't easily verify all are True without decoding)
                    assert ext_data["faces"]["smooth"] is not None
                    break

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)


def test_ext_bmesh_encoding_pure_faceted_mesh(vrm0_test_setup):
    """Test EXT_bmesh_encoding with a mesh that has all faces set to faceted."""
    armature, encoder, decoder = vrm0_test_setup
    obj = create_test_mesh_object("PureFacetedMesh", "ico_sphere")

    # Set all faces to faceted
    for face in obj.data.polygons:
        face.use_smooth = False

    # Set all edges to sharp
    for edge in obj.data.edges:
        if hasattr(edge, 'use_edge_sharp'):
            edge.use_edge_sharp = True

    # Export with EXT_bmesh_encoding enabled
    exporter = Vrm0Exporter(
        bpy.context,
        [obj],
        armature,
        export_ext_bmesh_encoding=True
    )

    result = exporter.export_vrm()
    assert result is not None, "Export should succeed with pure faceted mesh"

    # Parse and verify
    gltf_data, _ = parse_glb(result)

    # Verify EXT_bmesh_encoding is present
    assert "EXT_bmesh_encoding" in gltf_data.get("extensionsUsed", [])

    # Find and verify smooth flags are present (even if all False)
    meshes = gltf_data.get("meshes", [])
    for mesh in meshes:
        primitives = mesh.get("primitives", [])
        for primitive in primitives:
            extensions = primitive.get("extensions", {})
            if "EXT_bmesh_encoding" in extensions:
                ext_data = extensions["EXT_bmesh_encoding"]
                if "faces" in ext_data and "smooth" in ext_data["faces"]:
                    assert ext_data["faces"]["smooth"] is not None
                    break

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)
