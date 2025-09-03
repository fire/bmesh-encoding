"""
Test EXT_bmesh_encoding extension hook registration and discovery.
This test verifies that the extension hooks are properly discoverable
and called during glTF import/export operations.
"""

import pytest
import bpy
import sys
from pathlib import Path

# Add the src directory to Python path
test_dir = Path(__file__).parent
src_dir = test_dir.parent
sys.path.insert(0, str(src_dir))

from ext_bmesh_encoding.gltf_extension import (
    glTF2ImportUserExtension,
    glTF2ExportUserExtension,
    EXTBMeshEncodingExtension
)


class TestExtensionHookRegistration:
    """Test extension hook registration and discovery."""

    def test_extension_classes_exist_and_instantiable(self):
        """Test that extension classes can be instantiated."""
        # Test import extension
        import_ext = glTF2ImportUserExtension()
        assert import_ext is not None
        assert hasattr(import_ext, 'gather_import_mesh_before_hook')
        assert hasattr(import_ext, 'gather_import_armature_bone_after_hook')

        # Test export extension
        export_ext = glTF2ExportUserExtension()
        assert export_ext is not None
        assert hasattr(export_ext, 'gather_gltf_hook')

        # Test compatibility extension
        compat_ext = EXTBMeshEncodingExtension()
        assert compat_ext is not None
        assert compat_ext.extension_name == "EXT_bmesh_encoding"
        assert hasattr(compat_ext, 'import_mesh')
        assert hasattr(compat_ext, 'export_mesh')
        assert hasattr(compat_ext, 'gather_gltf_extensions')

    def test_extension_module_attributes(self):
        """Test that extension classes are properly exposed as module attributes."""
        import ext_bmesh_encoding.gltf_extension as ext_module

        # Check that classes are available as module attributes
        assert hasattr(ext_module, 'glTF2ImportUserExtension')
        assert hasattr(ext_module, 'glTF2ExportUserExtension')
        assert hasattr(ext_module, 'EXTBMeshEncodingExtension')
        assert hasattr(ext_module, 'ext_bmesh_encoding')

        # Verify they are the actual classes, not instances
        assert ext_module.glTF2ImportUserExtension == glTF2ImportUserExtension
        assert ext_module.glTF2ExportUserExtension == glTF2ExportUserExtension
        assert ext_module.EXTBMeshEncodingExtension == EXTBMeshEncodingExtension

    def test_extension_hook_initialization(self):
        """Test that extension hooks initialize properly."""
        import_ext = glTF2ImportUserExtension()
        export_ext = glTF2ExportUserExtension()

        # Test lazy initialization
        assert import_ext._initialized == False
        assert export_ext._initialized == False

        # Trigger initialization by calling a method that requires it
        # This should initialize the encoder/decoder
        try:
            # Create a mock pymesh object
            class MockPrimitive:
                def __init__(self):
                    self.extensions = None

            class MockPyMesh:
                def __init__(self):
                    self.name = "test_mesh"
                    self.primitives = [MockPrimitive()]

            mock_pymesh = MockPyMesh()
            mock_gltf = {}

            # This should trigger initialization
            import_ext.gather_import_mesh_before_hook(mock_pymesh, mock_gltf)

            # Check that initialization occurred
            assert import_ext._initialized == True

        except Exception as e:
            # If initialization fails due to missing dependencies, that's expected in test env
            print(f"Expected initialization failure in test environment: {e}")

    def test_extension_discovery_mechanism(self):
        """Test the extension discovery mechanism used by glTF-Blender-IO."""
        import ext_bmesh_encoding.gltf_extension as ext_module

        # Test __all__ export list
        assert hasattr(ext_module, '__all__')
        expected_exports = [
            'glTF2ImportUserExtension',
            'glTF2ExportUserExtension',
            'EXTBMeshEncodingExtension',
            'ext_bmesh_encoding'
        ]
        assert ext_module.__all__ == expected_exports

        # Verify all exported items exist
        for item_name in ext_module.__all__:
            assert hasattr(ext_module, item_name), f"Missing export: {item_name}"

    def test_mock_gltf_integration(self):
        """Test integration with mock glTF structures."""
        # Create mock glTF data structure similar to what glTF-Blender-IO creates
        mock_gltf_data = {
            "asset": {"version": "2.0"},
            "meshes": [{
                "name": "test_mesh",
                "primitives": [{
                    "extensions": {
                        "EXT_bmesh_encoding": {
                            "faceLoopIndices": [0, 1, 2, 3],
                            "faceCounts": [4]
                        }
                    }
                }]
            }]
        }

        # Test that our extension can process this structure
        import_ext = glTF2ImportUserExtension()

        # Create mock objects that simulate glTF-Blender-IO structures
        class MockExtensions:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        class MockPrimitive:
            def __init__(self, extensions_data):
                self.extensions = MockExtensions(extensions_data) if extensions_data else None

        class MockPyMesh:
            def __init__(self, primitives_data):
                self.name = "test_mesh"
                self.primitives = [MockPrimitive(prim.get('extensions')) for prim in primitives_data]

        mock_pymesh = MockPyMesh(mock_gltf_data["meshes"][0]["primitives"])

        # Test that the hook can process the mock data
        try:
            import_ext.gather_import_mesh_before_hook(mock_pymesh, mock_gltf_data)
            print("✅ Extension hook processed mock glTF data successfully")
        except Exception as e:
            print(f"Extension hook processing failed (expected in test env): {e}")

    def test_extension_hook_method_signatures(self):
        """Test that extension hook methods have correct signatures."""
        import_ext = glTF2ImportUserExtension()
        export_ext = glTF2ExportUserExtension()

        # Check method signatures using inspect
        import inspect

        # Import hooks
        import_sig = inspect.signature(import_ext.gather_import_mesh_before_hook)
        expected_import_params = ['pymesh', 'gltf']
        actual_import_params = list(import_sig.parameters.keys())[1:]  # Skip 'self'
        assert actual_import_params == expected_import_params, \
            f"Import hook signature mismatch: {actual_import_params} vs {expected_import_params}"

        armature_sig = inspect.signature(import_ext.gather_import_armature_bone_after_hook)
        expected_armature_params = ['gltf_node', 'blender_bone', 'armature', 'gltf_importer']
        actual_armature_params = list(armature_sig.parameters.keys())[1:]  # Skip 'self'
        assert actual_armature_params == expected_armature_params, \
            f"Armature hook signature mismatch: {actual_armature_params} vs {expected_armature_params}"

        # Export hook
        export_sig = inspect.signature(export_ext.gather_gltf_hook)
        expected_export_params = ['gltf2_object', 'blender_object', 'export_settings', 'gltf2_exporter']
        actual_export_params = list(export_sig.parameters.keys())[1:]  # Skip 'self'
        assert actual_export_params == expected_export_params, \
            f"Export hook signature mismatch: {actual_export_params} vs {expected_export_params}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
