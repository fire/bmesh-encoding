"""
Mock VRM addon components for testing EXT_bmesh_encoding in standalone environment.

This module provides mock implementations of VRM addon classes and functions
that are needed for the integration tests to run properly.
"""

import bpy
from typing import Any, Dict, List, Optional
from pathlib import Path
import json


class MockParseResult:
    """Mock result from glTF parsing."""
    def __init__(self, gltf_data: dict, binary_data: bytes = b''):
        self.gltf_data = gltf_data
        self.binary_data = binary_data


def mock_parse_glb(glb_data: bytes) -> tuple:
    """Mock glTF binary parsing function."""
    # Simple mock - just return empty dict and empty binary
    # In real implementation, this would parse the glTF binary format
    return {}, b''


class MockOps:
    """Mock VRM operations module."""
    class icyp:
        @staticmethod
        def make_basic_armature():
            """Create a basic armature for testing."""
            armature_data = bpy.data.armatures.new("TestArmature")
            armature = bpy.data.objects.new("TestArmature", armature_data)
            bpy.context.collection.objects.link(armature)
            bpy.context.view_layer.objects.active = armature
            return armature


class MockVrm0Exporter:
    """Mock VRM 0.x exporter for testing."""

    def __init__(self, context, objects, armature, preferences=None, export_ext_bmesh_encoding=None):
        self.context = context
        self.objects = objects
        self.armature = armature
        self.preferences = preferences

        # Handle both preferences object and direct parameter
        if export_ext_bmesh_encoding is not None:
            self.export_ext_bmesh_encoding = export_ext_bmesh_encoding
        elif preferences:
            self.export_ext_bmesh_encoding = getattr(preferences, 'export_ext_bmesh_encoding', False)
        else:
            self.export_ext_bmesh_encoding = False

        self.original_mesh_topology = {}

    def export_vrm(self):
        """Mock VRM export - returns mock glTF binary data."""
        # Create a simple mock glTF structure
        gltf_data = {
            "asset": {"version": "2.0"},
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0}],
            "meshes": [{"primitives": [{}]}]
        }

        # Add EXT_bmesh_encoding if enabled
        if self.export_ext_bmesh_encoding:
            gltf_data["extensionsUsed"] = ["EXT_bmesh_encoding"]
            gltf_data["meshes"][0]["primitives"][0]["extensions"] = {
                "EXT_bmesh_encoding": {
                    "faceLoopIndices": [0, 1, 2, 3],
                    "faceCounts": [4]
                }
            }

        # Convert to JSON and add glTF header
        json_str = json.dumps(gltf_data, separators=(',', ':'))
        json_bytes = json_str.encode('utf-8')

        # Create simple glTF binary (glb) format
        # glTF header
        header = b'glTF' + (2).to_bytes(4, 'little') + len(json_bytes).to_bytes(4, 'little')
        # JSON chunk
        json_chunk = len(json_bytes).to_bytes(4, 'little') + b'JSON' + json_bytes
        # No binary chunk for this simple mock
        binary_chunk = (0).to_bytes(4, 'little') + b'BIN\x00'

        return header + json_chunk + binary_chunk

    def capture_original_mesh_topology(self):
        """Mock topology capture."""
        if not self.export_ext_bmesh_encoding:
            return

        from ..encoding import BmeshEncoder
        encoder = BmeshEncoder()

        for obj in self.objects:
            if obj.type == 'MESH':
                try:
                    topology = encoder.encode_object(obj)
                    if topology:
                        self.original_mesh_topology[obj.name] = topology
                except Exception as e:
                    print(f"Failed to capture topology for {obj.name}: {e}")

    def add_ext_bmesh_encoding_to_meshes(self, json_dict, buffer0, object_name_to_index_dict):
        """Mock extension addition to meshes."""
        if not self.export_ext_bmesh_encoding or not self.original_mesh_topology:
            return

        # Add extension to extensionsUsed
        if "extensionsUsed" not in json_dict:
            json_dict["extensionsUsed"] = []
        if "EXT_bmesh_encoding" not in json_dict["extensionsUsed"]:
            json_dict["extensionsUsed"].append("EXT_bmesh_encoding")

        # Add extension data to meshes
        for mesh in json_dict.get("meshes", []):
            mesh_name = mesh.get("name", "")
            if mesh_name in self.original_mesh_topology:
                for primitive in mesh.get("primitives", []):
                    if "extensions" not in primitive:
                        primitive["extensions"] = {}
                    primitive["extensions"]["EXT_bmesh_encoding"] = self.original_mesh_topology[mesh_name]


class MockVrm1Exporter:
    """Mock VRM 1.x exporter for testing."""

    def __init__(self, context, objects, armature, preferences):
        self.context = context
        self.objects = objects
        self.armature = armature
        self.preferences = preferences
        self.export_ext_bmesh_encoding = getattr(preferences, 'export_ext_bmesh_encoding', False)
        self.original_mesh_topology = {}
        self.extras_main_armature_key = "main_armature"
        self.extras_object_name_key = "object_name"

    def export_vrm(self):
        """Mock VRM 1.x export."""
        # Similar to VRM 0.x but with VRM 1.0 structure
        gltf_data = {
            "asset": {"version": "2.0"},
            "extensions": {"VRM": {"specVersion": "1.0"}},
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0}],
            "meshes": [{"primitives": [{}]}]
        }

        # Add EXT_bmesh_encoding if enabled
        if self.export_ext_bmesh_encoding:
            gltf_data["extensionsUsed"] = ["EXT_bmesh_encoding"]
            gltf_data["meshes"][0]["primitives"][0]["extensions"] = {
                "EXT_bmesh_encoding": {
                    "faceLoopIndices": [0, 1, 2, 3],
                    "faceCounts": [4]
                }
            }

        # Convert to JSON and add glTF header
        json_str = json.dumps(gltf_data, separators=(',', ':'))
        json_bytes = json_str.encode('utf-8')

        # Create simple glTF binary (glb) format
        header = b'glTF' + (2).to_bytes(4, 'little') + len(json_bytes).to_bytes(4, 'little')
        json_chunk = len(json_bytes).to_bytes(4, 'little') + b'JSON' + json_bytes
        binary_chunk = (0).to_bytes(4, 'little') + b'BIN\x00'

        return header + json_chunk + binary_chunk

    def capture_original_mesh_topology(self):
        """Mock topology capture for VRM 1.x."""
        if not self.export_ext_bmesh_encoding:
            return

        from ..encoding import BmeshEncoder
        encoder = BmeshEncoder()

        for obj in self.objects:
            if obj.type == 'MESH':
                try:
                    topology = encoder.encode_object(obj)
                    if topology:
                        self.original_mesh_topology[obj.name] = topology
                except Exception as e:
                    print(f"Failed to capture topology for {obj.name}: {e}")

    def add_ext_bmesh_encoding_to_meshes(self, json_dict, buffer0, object_name_to_index_dict):
        """Mock extension addition for VRM 1.x."""
        if not self.export_ext_bmesh_encoding or not self.original_mesh_topology:
            return

        # Add extension to extensionsUsed
        if "extensionsUsed" not in json_dict:
            json_dict["extensionsUsed"] = []
        if "EXT_bmesh_encoding" not in json_dict["extensionsUsed"]:
            json_dict["extensionsUsed"].append("EXT_bmesh_encoding")

        # Add extension data to meshes
        for mesh in json_dict.get("meshes", []):
            mesh_name = mesh.get("name", "")
            if mesh_name in self.original_mesh_topology:
                for primitive in mesh.get("primitives", []):
                    if "extensions" not in primitive:
                        primitive["extensions"] = {}
                    primitive["extensions"]["EXT_bmesh_encoding"] = self.original_mesh_topology[mesh_name]


# Create mock modules to simulate the VRM addon structure
import sys
from types import ModuleType

# Create mock io_scene_vrm module
mock_vrm = ModuleType('io_scene_vrm')

# Add submodules
mock_vrm.editor = ModuleType('io_scene_vrm.editor')
mock_vrm.editor.bmesh_encoding = ModuleType('io_scene_vrm.editor.bmesh_encoding')
mock_vrm.common = ModuleType('io_scene_vrm.common')
mock_vrm.common.gltf = ModuleType('io_scene_vrm.common.gltf')
mock_vrm.common.logger = ModuleType('io_scene_vrm.common.logger')
mock_vrm.exporter = ModuleType('io_scene_vrm.exporter')

# Add classes and functions to submodules
mock_vrm.editor.bmesh_encoding.BmeshEncoder = None  # Will be imported from local
mock_vrm.editor.bmesh_encoding.BmeshDecoder = None  # Will be imported from local
mock_vrm.common.ops = MockOps()
mock_vrm.common.gltf.parse_glb = mock_parse_glb
mock_vrm.common.logger.get_logger = None  # Will be imported from local
mock_vrm.exporter.Vrm0Exporter = MockVrm0Exporter
mock_vrm.exporter.Vrm1Exporter = MockVrm1Exporter

# Add to sys.modules so imports work
sys.modules['io_scene_vrm'] = mock_vrm
sys.modules['io_scene_vrm.editor'] = mock_vrm.editor
sys.modules['io_scene_vrm.editor.bmesh_encoding'] = mock_vrm.editor.bmesh_encoding
sys.modules['io_scene_vrm.common'] = mock_vrm.common
sys.modules['io_scene_vrm.common.gltf'] = mock_vrm.common.gltf
sys.modules['io_scene_vrm.common.logger'] = mock_vrm.common.logger
sys.modules['io_scene_vrm.exporter'] = mock_vrm.exporter
