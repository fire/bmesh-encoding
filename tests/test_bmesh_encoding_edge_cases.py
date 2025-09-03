"""
Test EXT_bmesh_encoding with complex mesh scenarios and edge cases.
Tests edge cases that may occur in real mesh data.
"""
import pytest
import bpy
import bmesh
import math
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import random

# Add the src directory to Python path to allow imports
test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from ext_bmesh_encoding.encoding import BmeshEncoder
from ext_bmesh_encoding.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def edge_case_setup():
    """Set up test environment for edge case tests."""
    from ext_bmesh_encoding.decoding import BmeshDecoder
    bmesh_encoder = BmeshEncoder()
    bmesh_decoder = BmeshDecoder()

    yield bmesh_encoder

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
        # Create a more complex mesh with various face types
        verts = []
        faces = []

        # Add vertices in a pattern
        for x in range(-2, 3):
            for y in range(-1, 2):
                for z in range(-2, 3):
                    verts.append((x, y, z))

        # Add faces creating different topologies
        for x in range(-2, 2):
            for z in range(-2, 2):
                # Create quad faces (will be triangulated)
                faces.append([
                    ((x+2) * 3 + (z+2)),
                    ((x+2) * 3 + (z+3)),
                    ((x+3) * 3 + (z+3)),
                    ((x+3) * 3 + (z+2))
                ])

        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        for vert_pos in verts:
            bm.verts.new(vert_pos)
        for face_verts in faces:
            bm.faces.new([bm.verts[i] for i in face_verts])

    bm.to_mesh(mesh)
    bm.free()

    return obj

def create_maze_mesh(name="MazeMesh"):
    """Create a complex maze-like mesh with many small faces."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create a simple maze pattern
    wall_thickness = 0.2
    maze = [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 1, 0, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1],
    ]

    height = 1.0
    scale = 0.5

    # Generate walls
    for y in range(len(maze)):
        for x in range(len(maze[0])):
            if maze[y][x] == 1:
                # Create wall block
                x_pos = x * scale
                y_pos = y * scale

                verts = []
                verts.append(bm.verts.new((x_pos, y_pos, 0)))
                verts.append(bm.verts.new((x_pos + scale, y_pos, 0)))
                verts.append(bm.verts.new((x_pos + scale, y_pos + scale, 0)))
                verts.append(bm.verts.new((x_pos, y_pos + scale, 0)))

                verts.append(bm.verts.new((x_pos, y_pos, height)))
                verts.append(bm.verts.new((x_pos + scale, y_pos, height)))
                verts.append(bm.verts.new((x_pos + scale, y_pos + scale, height)))
                verts.append(bm.verts.new((x_pos, y_pos + scale, height)))

                # Create faces
                # Bottom
                bm.faces.new([verts[0], verts[1], verts[2], verts[3]])
                # Top
                bm.faces.new([verts[4], verts[5], verts[6], verts[7]])
                # Front
                bm.faces.new([verts[0], verts[1], verts[5], verts[4]])
                # Back
                bm.faces.new([verts[3], verts[2], verts[6], verts[7]])
                # Left
                bm.faces.new([verts[0], verts[3], verts[7], verts[4]])
                # Right
                bm.faces.new([verts[1], verts[2], verts[6], verts[5]])

    bm.to_mesh(mesh)
    bm.free()

    return obj

def create_degenerate_geometry_mesh(name="DegenerateMesh"):
    """Create mesh with degenerate geometry (zero-area faces, duplicate vertices)."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Add vertices with duplicates
    verts = []
    verts.append(bm.verts.new((0, 0, 0)))      # 0 - duplicated below
    verts.append(bm.verts.new((1, 0, 0)))      # 1
    verts.append(bm.verts.new((0.5, 1, 0)))    # 2
    verts.append(bm.verts.new((0, 0, 0)))      # 3 - duplicate of 0

    # Good triangle
    bm.faces.new([verts[0], verts[1], verts[2]])

    # Degenerate faces (different types)
    # Zero-area triangle (collinear points)
    try:
        bm.faces.new([verts[0], verts[1], verts[3]])  # Points 0, 1, 3 (3 is duplicate of 0)
    except ValueError:
        pass  # Expected to fail with degenerate geometry

    # Very thin triangle - add vertices first
    verts.append(bm.verts.new((2, 0, 0)))        # 4
    verts.append(bm.verts.new((2.0001, 0, 0)))   # 5 - very close to 4
    verts.append(bm.verts.new((2.00005, 0.1, 0))) # 6

    # Now create the very thin triangle
    try:
        bm.faces.new([verts[4], verts[5], verts[6]])  # Very thin triangle
    except ValueError:
        pass  # May fail with very thin geometry

    bm.to_mesh(mesh)
    bm.free()

    return obj

def create_island_mesh(name="IslandMesh"):
    """Create mesh with separate islands of geometry."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # First island - a cube
    bm.verts.new((0, 0, 0))
    bm.verts.new((1, 0, 0))
    bm.verts.new((1, 1, 0))
    bm.verts.new((0, 1, 0))
    bm.verts.new((0, 0, 1))
    bm.verts.new((1, 0, 1))
    bm.verts.new((1, 1, 1))
    bm.verts.new((0, 1, 1))

    # Second island - a separate triangle far away
    bm.verts.new((5, 0, 0))
    bm.verts.new((6, 0, 0))
    bm.verts.new((5.5, 2, 0))

    # Third island - another separate quad
    bm.verts.new((0, 5, 0))
    bm.verts.new((1, 5, 0))
    bm.verts.new((1, 6, 0))
    bm.verts.new((0, 6, 0))

    bm.verts.ensure_lookup_table()

    # Create faces for each island
    # Island 1 - cube faces
    bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[2], bm.verts[3]])  # bottom

    # Island 2 - single triangle
    bm.faces.new([bm.verts[8], bm.verts[9], bm.verts[10]])

    # Island 3 - single quad
    bm.faces.new([bm.verts[11], bm.verts[12], bm.verts[13], bm.verts[14]])

    bm.to_mesh(mesh)
    bm.free()

    return obj

def create_nested_hierarchy_mesh(name="NestedMesh"):
    """Create mesh with deeply nested face loops."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create a complex nested structure
    radius = 2.0
    rings = 5
    segments_per_ring = [4, 8, 12, 16, 20]

    all_verts = []

    for ring in range(rings):
        if ring >= len(segments_per_ring):
            continue
        segments = segments_per_ring[ring]
        ring_verts = []

        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * (ring + 1) * math.cos(angle)
            y = radius * (ring + 1) * math.sin(angle)
            z = 0

            vert = bm.verts.new((x, y, z))
            ring_verts.append(vert)
            all_verts.append(vert)

        # Connect each ring
        if ring > 0:
            prev_segments = segments_per_ring[ring - 1]
            prev_ring_start = sum(segments_per_ring[:ring])

            for i in range(segments):
                # Connect to previous ring
                if i % 2 == 0:  # Create some complex patterns
                    prev_i1 = (i // 2) % prev_segments
                    prev_i2 = ((i // 2) + 1) % prev_segments

                    # Create triangles bridging rings (avoid duplicate vertices)
                    v1 = ring_verts[i]
                    v2 = all_verts[prev_ring_start + prev_i1]
                    v3 = all_verts[prev_ring_start + prev_i2]

                    # Only create face if vertices are distinct
                    if len(set([v1, v2, v3])) == 3:
                        try:
                            bm.faces.new([v1, v2, v3])
                        except ValueError:
                            pass  # Skip invalid faces

    bm.to_mesh(mesh)
    bm.free()

    return obj

def create_extremely_dense_mesh(name="DenseMesh"):
    """Create mesh with many small, densely packed faces."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    vertices = []
    faces = []

    # Create a dense grid
    grid_size = 20  # 400 vertices
    for x in range(grid_size):
        for z in range(grid_size):
            vertices.append((x * 0.1, 0, z * 0.1))

    # Create faces with random triangulation patterns
    random.seed(42)  # For reproducibility

    for x in range(grid_size - 1):
        for z in range(grid_size - 1):
            v1 = x * grid_size + z
            v2 = (x + 1) * grid_size + z
            v3 = (x + 1) * grid_size + z + 1
            v4 = x * grid_size + z + 1

            # Randomly choose triangulation pattern
            if random.choice([True, False]):
                # One way
                faces.extend([(v1, v2, v3), (v1, v3, v4)])
            else:
                # Other way
                faces.extend([(v1, v2, v4), (v2, v3, v4)])

    # Create mesh data
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    return obj

def test_complex_maze_topology(edge_case_setup):
    """Test encoding with complex maze-like topology."""
    bmesh_encoder = edge_case_setup
    obj = create_maze_mesh("MazeTest")

    # Store references before encoding
    mesh_data = obj.data
    obj_name = obj.name

    try:
        # Encode
        encoded_data = bmesh_encoder.encode_object_native(obj)
        assert encoded_data is not None, "Maze encoding should succeed"
        assert isinstance(encoded_data, dict), "Should return dictionary"
    finally:
        # Cleanup - handle potential invalidation gracefully
        try:
            if obj and obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj)
        except (ReferenceError, KeyError):
            pass  # Object already removed or invalid

        try:
            if mesh_data and mesh_data.name in bpy.data.meshes:
                bpy.data.meshes.remove(mesh_data)
        except (ReferenceError, KeyError):
            pass  # Mesh already removed or invalid

def test_degenerate_geometry_handling(edge_case_setup):
    """Test handling of degenerate geometry (zero-area faces, duplicates)."""
    bmesh_encoder = edge_case_setup
    obj = create_degenerate_geometry_mesh("DegenerateTest")

    # This should handle gracefully - not crash
    encoded_data = bmesh_encoder.encode_object_native(obj)

    if encoded_data is not None:  # May return None for degenerate cases
        assert isinstance(encoded_data, dict), "Should return dictionary"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)


def test_separate_island_mesh(edge_case_setup):
    """Test encoding with separate islands of geometry."""
    bmesh_encoder = edge_case_setup
    obj = create_island_mesh("IslandTest")

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Island encoding should succeed"
    assert isinstance(encoded_data, dict), "Should return dictionary"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)


def test_nested_hierarchy_mesh(edge_case_setup):
    """Test encoding with deeply nested face loops."""
    bmesh_encoder = edge_case_setup
    obj = create_nested_hierarchy_mesh("NestedTest")

    # This might be a challenging case - should handle gracefully
    encoded_data = bmesh_encoder.encode_object_native(obj)

    if encoded_data is not None:
        assert isinstance(encoded_data, dict), "Should return dictionary"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)


def test_extremely_dense_mesh(edge_case_setup):
    """Test encoding with extremely dense geometry."""
    bmesh_encoder = edge_case_setup
    obj = create_extremely_dense_mesh("DenseTest")

    # May take longer for dense meshes
    encoded_data = bmesh_encoder.encode_object_native(obj)

    if encoded_data is not None:  # May exceed limits
        assert isinstance(encoded_data, dict), "Should return dictionary"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)

def test_mixed_face_types_extensive(edge_case_setup):
    """Test mesh with extensive mixture of different face types."""
    bmesh_encoder = edge_case_setup
    # Create a mesh with triangles, quads, pentagons, hexagons
    vertices = []
    faces = []

    # Create large circular arrangement
    ring_count = 3
    for ring in range(ring_count):
        angle_step = 2 * math.pi / (6 + ring * 2)  # Different segment counts
        for i in range(6 + ring * 2):
            angle = i * angle_step
            radius = 1 + ring * 0.5
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            z = ring * 0.1
            vertices.append((x, y, z))

    # Manual face creation for different ngon types
    base_count = 6
    for ring in range(ring_count - 1):
        next_ring_start = sum(6 + i * 2 for i in range(ring + 1))
        current_ring_start = sum(6 + i * 2 for i in range(ring))

        current_count = 6 + ring * 2
        next_count = 6 + (ring + 1) * 2

        for i in range(current_count):
            # Create different face patterns
            if ring % 3 == 0:
                # Triangles
                faces.extend([
                    (current_ring_start + i, current_ring_start + (i + 1) % current_count,
                     next_ring_start + (i * 2) % next_count)
                ])
            elif ring % 3 == 1:
                # Quads
                faces.extend([
                    (current_ring_start + i, current_ring_start + (i + 1) % current_count,
                     next_ring_start + (i * 2 + 1) % next_count,
                     next_ring_start + (i * 2) % next_count)
                ])
            else:
                # Mixed ngons (pentagons, hexagons)
                if (i % 2 == 0):
                    faces.extend([
                        (current_ring_start + i, current_ring_start + (i + 1) % current_count,
                         current_ring_start + (i + 2) % current_count,
                         next_ring_start + (i * 2 + 1) % next_count,
                         next_ring_start + (i * 2) % next_count)
                    ])

    mesh = bpy.data.meshes.new("MixedTypesMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("MixedTypesObj", mesh)
    bpy.context.collection.objects.link(obj)

    # Test encoding
    encoded_data = bmesh_encoder.encode_object_native(obj)
    if encoded_data is not None:
        assert isinstance(encoded_data, dict), "Should return dictionary"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)

def test_mesh_with_transformations(edge_case_setup):
    """Test encoding with mesh that has non-identity transformations."""
    bmesh_encoder = edge_case_setup
    obj = create_test_mesh_object("TransformTest", "cube")

    # Apply various transformations
    obj.scale = (2.0, 0.5, 3.0)
    obj.rotation_euler = (math.pi / 4, math.pi / 6, math.pi / 8)
    obj.location = (1.0, 2.0, 3.0)

    # Update to apply transformations to mesh data
    bpy.context.view_layer.update()

    # Encode
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Transformed mesh encoding should succeed"
    assert isinstance(encoded_data, dict), "Should return dictionary"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)


def test_mesh_with_multiple_uv_layers(edge_case_setup):
    """Test encoding with mesh that has multiple UV layers."""
    bmesh_encoder = edge_case_setup
    obj = create_test_mesh_object("MultiUVTest", "cube")

    # Ensure we have at least one UV layer
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVLayer1")

    # Add another UV layer
    uv_layer2 = obj.data.uv_layers.new(name="UVLayer2")

    # Verify we have both layers
    assert len(obj.data.uv_layers) >= 2, f"Expected at least 2 UV layers, got {len(obj.data.uv_layers)}"

    # Create different UV mappings on each layer
    for i, polygon in enumerate(obj.data.polygons):
        for j, loop_index in enumerate(polygon.loop_indices):
            uv_layer1 = obj.data.uv_layers[0]
            uv_layer2 = obj.data.uv_layers[1]

            # Different UV unwraps
            u1 = v1 = 0.5
            if j == 0:
                u1, v1 = 0.0, 0.0
            elif j == 1:
                u1, v1 = 1.0, 0.0
            elif j == 2:
                u1, v1 = 1.0, 1.0
            elif j == 3:
                u1, v1 = 0.0, 1.0

            # Different mapping for second layer
            u2 = (u1 + i * 0.1) % 1.0
            v2 = (v1 + i * 0.1) % 1.0

            uv_layer1.data[loop_index].uv = (u1, v1)
            uv_layer2.data[loop_index].uv = (u2, v2)

    # Encode - should preserve topology despite multiple UVs
    encoded_data = bmesh_encoder.encode_object_native(obj)
    assert encoded_data is not None, "Multi-UV mesh encoding should succeed"
    assert isinstance(encoded_data, dict), "Should return dictionary"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)

def test_error_handling_corrupted_data(edge_case_setup):
    """Test error handling with potentially corrupted or incomplete data."""
    bmesh_encoder = edge_case_setup
    # Test various error conditions - encoder should handle gracefully
    error_cases = [
        None,           # None data
        {},            # Empty dict
        {"vertex": [], "face": [], "loop": []},  # Empty arrays
    ]

    for i, test_data in enumerate(error_cases):
        # Should handle gracefully without crashing
        try:
            result = bmesh_encoder.encode_object_native(test_data)
            # Result may be None or minimal data, but no exceptions
        except Exception:
            # Some error handling is expected for invalid inputs
            pass


def test_memory_usage_large_complex_mesh(edge_case_setup):
    """Test memory usage and performance with large complex meshes."""
    bmesh_encoder = edge_case_setup
    # Create a reasonably large mesh for performance testing
    verts = []
    faces = []

    grid_size = 10  # 100 vertices
    for x in range(grid_size):
        for z in range(grid_size):
            verts.append((x * 0.5, 0, z * 0.5))

    # Create faces with complex patterns
    for x in range(grid_size - 1):
        for z in range(grid_size - 1):
            base = x * grid_size + z
            # Change triangulation pattern
            if (x + z) % 2 == 0:
                faces.append((base, base + 1, base + grid_size + 1, base + grid_size))
            else:
                faces.extend([
                    (base, base + 1, base + grid_size),
                    (base + 1, base + grid_size + 1, base + grid_size)
                ])

    mesh = bpy.data.meshes.new("LargeComplexMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("LargeComplexObj", mesh)
    bpy.context.collection.objects.link(obj)

    # Time the encode operation
    import time
    start_time = time.time()

    encoded_data = bmesh_encoder.encode_object_native(obj)
    encode_time = time.time() - start_time

    if encoded_data is not None:
        # Should complete in reasonable time (< 1 second)
        assert encode_time < 1.0, f"Encoding too slow: {encode_time:.3f}s"

    # Cleanup
    mesh_data = obj.data  # Store reference before removing object
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh_data)


if __name__ == "__main__":
    unittest.main()
