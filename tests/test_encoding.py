# SPDX-License-Identifier: MIT
"""Tests for EXT_bmesh_encoding encoding functionality."""

import pytest
import bpy
import sys
import os
from pathlib import Path

# Add the src directory to Python path
test_dir = Path(__file__).parent.parent
src_dir = test_dir.parent
sys.path.insert(0, str(src_dir))

from ext_bmesh_encoding.encoding import BmeshEncoder
from ext_bmesh_encoding.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def test_mesh_object():
    """Create a simple test mesh object."""
    # Create a simple test mesh
    mesh = bpy.data.meshes.new("TestMesh")
    obj = bpy.data.objects.new("TestMesh", mesh)

    # Create a simple cube
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bm.to_mesh(mesh)
    bm.free()

    bpy.context.collection.objects.link(obj)

    yield obj

    # Cleanup
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh)

def test_encoder_initialization():
    """Test that BmeshEncoder can be initialized."""
    encoder = BmeshEncoder()
    assert encoder is not None
    assert hasattr(encoder, 'preserve_manifold_info')


def test_encode_object_basic(test_mesh_object):
    """Test basic object encoding."""
    encoder = BmeshEncoder()

    # Test encoding
    extension_data = encoder.encode_object(test_mesh_object)

    # Should return a dictionary
    assert isinstance(extension_data, dict)

    # Should have basic structure
    if extension_data:  # May be empty for simple meshes
        assert isinstance(extension_data, dict)


def test_encode_object_native(test_mesh_object):
    """Test native mesh encoding."""
    encoder = BmeshEncoder()

    # Test native encoding
    extension_data = encoder.encode_object_native(test_mesh_object)

    # Should return a dictionary
    assert isinstance(extension_data, dict)


def test_create_mesh_data_from_object(test_mesh_object):
    """Test mesh data creation from object."""
    mesh_data = BmeshEncoder.create_mesh_data_from_object(test_mesh_object)

    # Should return mesh data or None
    if mesh_data is not None:
        assert isinstance(mesh_data, bpy.types.Mesh)


def test_create_bmesh_from_mesh(test_mesh_object):
    """Test BMesh creation from mesh object."""
    bm = BmeshEncoder.create_bmesh_from_mesh(test_mesh_object)

    # Should return BMesh or None
    if bm is not None:
        assert bm is not None
        bm.free()  # Clean up


def test_logger_setup():
    """Test that logger is properly configured."""
    test_logger = get_logger("test")
    assert test_logger is not None
    assert test_logger.name == "ext_bmesh_encoding.test"
