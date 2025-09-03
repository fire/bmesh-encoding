#!/usr/bin/env python3
"""
Test script for EXT_bmesh_encoding extension hooks using bpy in headless mode.

This script tests the extension hook registration and functionality without
requiring the full Blender GUI to be running.
"""

import sys
import os
from unittest.mock import Mock, MagicMock
import logging

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_extension_discovery():
    """Test that our extension classes are discoverable by glTF-Blender-IO."""
    logger.info("Testing extension discovery...")

    try:
        # Import our addon module directly using a different approach
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # Try importing as a regular module first
        try:
            import ext_bmesh_encoding
        except ImportError:
            # If that fails, try the dynamic import approach
            import importlib.util
            spec = importlib.util.spec_from_file_location("ext_bmesh_encoding", os.path.join(current_dir, "__init__.py"))
            ext_bmesh_encoding = importlib.util.module_from_spec(spec)
            sys.modules["ext_bmesh_encoding"] = ext_bmesh_encoding
            spec.loader.exec_module(ext_bmesh_encoding)

        # Check for the required extension classes
        has_import_extension = hasattr(ext_bmesh_encoding, 'glTF2ImportUserExtension')
        has_export_extension = hasattr(ext_bmesh_encoding, 'glTF2ExportUserExtension')

        logger.info(f"glTF2ImportUserExtension found: {has_import_extension}")
        logger.info(f"glTF2ExportUserExtension found: {has_export_extension}")

        if not has_import_extension:
            logger.error("❌ glTF2ImportUserExtension not found in addon")
            return False

        if not has_export_extension:
            logger.error("❌ glTF2ExportUserExtension not found in addon")
            return False

        logger.info("✅ Extension classes are discoverable")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to test extension discovery: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_extension_instantiation():
    """Test that extension classes can be instantiated."""
    logger.info("Testing extension instantiation...")

    try:
        # Import our addon module directly using a different approach
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # Try importing as a regular module first
        try:
            import ext_bmesh_encoding
        except ImportError:
            # If that fails, try the dynamic import approach
            import importlib.util
            spec = importlib.util.spec_from_file_location("ext_bmesh_encoding", os.path.join(current_dir, "__init__.py"))
            ext_bmesh_encoding = importlib.util.module_from_spec(spec)
            sys.modules["ext_bmesh_encoding"] = ext_bmesh_encoding
            spec.loader.exec_module(ext_bmesh_encoding)

        # Test import extension
        import_extension_class = ext_bmesh_encoding.glTF2ImportUserExtension
        import_extension = import_extension_class()

        # Test export extension
        export_extension_class = ext_bmesh_encoding.glTF2ExportUserExtension
        export_extension = export_extension_class()

        # Verify they have the expected methods
        import_methods = ['gather_import_mesh_before_hook', 'gather_import_armature_bone_after_hook']
        export_methods = ['gather_gltf_hook']

        for method in import_methods:
            if not hasattr(import_extension, method):
                logger.error(f"❌ Import extension missing method: {method}")
                return False

        for method in export_methods:
            if not hasattr(export_extension, method):
                logger.error(f"❌ Export extension missing method: {method}")
                return False

        # Test the hook signatures by calling them
        try:
            # Test import hooks with correct signatures
            mocks = create_mock_blender_objects()
            import_extension.gather_import_mesh_before_hook(mocks['gltf_mesh'], mocks['gltf_importer'])
            import_extension.gather_import_armature_bone_after_hook(None, None, None, Mock())

            # Test export hook
            export_extension.gather_gltf_hook(Mock(), None, Mock())

            logger.info("✅ Hook signatures are correct")
        except Exception as e:
            logger.error(f"❌ Hook signature test failed: {e}")
            return False

        logger.info("✅ Extension classes can be instantiated and have required methods")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to test extension instantiation: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def create_mock_blender_objects():
    """Create mock Blender objects for testing."""
    logger.info("Creating mock Blender objects...")

    # Mock bpy module
    bpy_mock = Mock()

    # Mock Blender mesh object
    mock_mesh = Mock()
    mock_mesh.name = "TestMesh"
    mock_mesh.type = 'MESH'

    # Mock mesh data
    mock_mesh_data = Mock()
    mock_mesh_data.name = "TestMeshData"
    mock_mesh.data = mock_mesh_data

    # Mock glTF structures
    mock_gltf_mesh = Mock()
    mock_gltf_mesh.name = "TestGLTFMesh"
    mock_gltf_mesh.primitives = []

    # Mock primitive with extension
    mock_primitive = Mock()
    mock_primitive.extensions = Mock()

    # Create proper binary data for vertices (4 vertices with positions)
    import struct
    vertex_positions = struct.pack('<12f',  # 4 vertices * 3 floats each
        0.0, 0.0, 0.0,  # vertex 0
        1.0, 0.0, 0.0,  # vertex 1
        1.0, 1.0, 0.0,  # vertex 2
        0.0, 1.0, 0.0   # vertex 3
    )

    # Create proper binary data for edges (4 edges with vertex pairs)
    edge_vertices = struct.pack('<8I',  # 4 edges * 2 vertices each
        0, 1,  # edge 0
        1, 2,  # edge 1
        2, 3,  # edge 2
        3, 0   # edge 3
    )

    # Create proper binary data for face vertices and offsets
    face_vertices = struct.pack('<4I', 0, 1, 2, 3)  # single face with 4 vertices
    face_offsets = struct.pack('<2I', 0, 4)  # offset 0, and final offset 4

    mock_primitive.extensions.EXT_bmesh_encoding = {
        "vertices": {
            "count": 4,
            "positions": {
                "data": vertex_positions,
                "target": 34962,
                "componentType": 5126,
                "type": "VEC3",
                "count": 4
            }
        },
        "edges": {
            "count": 4,
            "vertices": {
                "data": edge_vertices,
                "target": 34963,
                "componentType": 5125,
                "type": "VEC2",
                "count": 4
            }
        },
        "loops": {
            "count": 4,
            "topology": {
                "data": struct.pack('<16I', 0, 0, 0, 1, 2, 3, 0, 0, 1, 1, 0, 2, 3, 1, 0, 0),  # mock topology data
                "target": 34962,
                "componentType": 5125,
                "type": "SCALAR",
                "count": 16
            }
        },
        "faces": {
            "count": 1,
            "vertices": {
                "data": face_vertices,
                "target": 34962,
                "componentType": 5125,
                "type": "SCALAR"
            },
            "offsets": {
                "data": face_offsets,
                "target": 34962,
                "componentType": 5125,
                "type": "SCALAR",
                "count": 2
            }
        }
    }
    mock_gltf_mesh.primitives.append(mock_primitive)

    # Mock glTF importer
    mock_gltf_importer = Mock()
    mock_gltf_importer.data = Mock()
    mock_gltf_importer.data.images = []

    return {
        'bpy': bpy_mock,
        'mesh_object': mock_mesh,
        'gltf_mesh': mock_gltf_mesh,
        'gltf_importer': mock_gltf_importer
    }

def test_import_hooks():
    """Test the import extension hooks."""
    logger.info("Testing import extension hooks...")

    try:
        # Import our addon module directly using a different approach
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # Try importing as a regular module first
        try:
            import ext_bmesh_encoding
        except ImportError:
            # If that fails, try the dynamic import approach
            import importlib.util
            spec = importlib.util.spec_from_file_location("ext_bmesh_encoding", os.path.join(current_dir, "__init__.py"))
            ext_bmesh_encoding = importlib.util.module_from_spec(spec)
            sys.modules["ext_bmesh_encoding"] = ext_bmesh_encoding
            spec.loader.exec_module(ext_bmesh_encoding)

        from ext_bmesh_encoding.importer import EXTBMeshEncodingImporter

        # Create mock objects
        mocks = create_mock_blender_objects()

        # Create importer instance
        importer = EXTBMeshEncodingImporter()

        # Test mesh before hook
        logger.info("Testing gather_import_mesh_before_hook...")
        importer.process_mesh_before_hook(
            mocks['gltf_mesh'],
            mocks['mesh_object'].data,
            mocks['gltf_importer']
        )

        # Test armature bone after hook
        logger.info("Testing gather_import_armature_bone_after_hook...")
        importer.process_armature_bone_after_hook(
            mocks['gltf_mesh'],  # Using as mock gltf_node
            mocks['mesh_object'],
            None,  # mock blender_bone
            mocks['gltf_importer']
        )

        logger.info("✅ Import hooks executed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to test import hooks: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_export_hooks():
    """Test the export extension hooks."""
    logger.info("Testing export extension hooks...")

    try:
        # Import our addon module directly using a different approach
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # Try importing as a regular module first
        try:
            import ext_bmesh_encoding
        except ImportError:
            # If that fails, try the dynamic import approach
            import importlib.util
            spec = importlib.util.spec_from_file_location("ext_bmesh_encoding", os.path.join(current_dir, "__init__.py"))
            ext_bmesh_encoding = importlib.util.module_from_spec(spec)
            sys.modules["ext_bmesh_encoding"] = ext_bmesh_encoding
            spec.loader.exec_module(ext_bmesh_encoding)

        from ext_bmesh_encoding.exporter import EXTBMeshEncodingExporter

        # Create mock objects
        mocks = create_mock_blender_objects()

        # Mock export settings
        mock_export_settings = Mock()
        mock_export_settings.export_ext_bmesh_encoding = True

        # Mock glTF object
        mock_gltf_object = Mock()
        mock_gltf_object.extensions = {}

        # Create exporter instance
        exporter = EXTBMeshEncodingExporter()

        # Test export hook
        logger.info("Testing gather_gltf_hook...")
        exporter.process_export_hook(
            mock_gltf_object,
            mocks['mesh_object'],
            mock_export_settings
        )

        logger.info("✅ Export hooks executed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to test export hooks: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_gltf_discovery_simulation():
    """Simulate the glTF-Blender-IO addon discovery process."""
    logger.info("Testing glTF addon discovery simulation...")

    try:
        # Import our addon module directly using a different approach
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # Try importing as a regular module first
        try:
            import ext_bmesh_encoding
        except ImportError:
            # If that fails, try the dynamic import approach
            import importlib.util
            spec = importlib.util.spec_from_file_location("ext_bmesh_encoding", os.path.join(current_dir, "__init__.py"))
            ext_bmesh_encoding = importlib.util.module_from_spec(spec)
            sys.modules["ext_bmesh_encoding"] = ext_bmesh_encoding
            spec.loader.exec_module(ext_bmesh_encoding)

        # Simulate the discovery process used by glTF-Blender-IO
        user_extensions = []
        pre_export_callbacks = []
        post_export_callbacks = []

        # This simulates the loop in glTF-Blender-IO that discovers extensions
        addon_modules = [ext_bmesh_encoding]  # In real Blender, this would be all enabled addons

        for module in addon_modules:
            try:
                if hasattr(module, 'glTF2ImportUserExtension'):
                    extension_ctor = module.glTF2ImportUserExtension
                    user_extensions.append(extension_ctor())
                    logger.info("✅ Found glTF2ImportUserExtension")

                if hasattr(module, 'glTF2ExportUserExtension'):
                    extension_ctor = module.glTF2ExportUserExtension
                    user_extensions.append(extension_ctor())
                    logger.info("✅ Found glTF2ExportUserExtension")

                if hasattr(module, 'glTF2_pre_export_callback'):
                    pre_export_callbacks.append(module.glTF2_pre_export_callback)

                if hasattr(module, 'glTF2_post_export_callback'):
                    post_export_callbacks.append(module.glTF2_post_export_callback)

            except Exception as e:
                logger.warning(f"Error processing module {module}: {e}")

        logger.info(f"✅ Discovery complete: {len(user_extensions)} extensions found")
        logger.info(f"✅ Pre-export callbacks: {len(pre_export_callbacks)}")
        logger.info(f"✅ Post-export callbacks: {len(post_export_callbacks)}")

        return len(user_extensions) > 0

    except Exception as e:
        logger.error(f"❌ Failed to test glTF discovery simulation: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting EXT_bmesh_encoding extension hook tests...")
    logger.info("=" * 60)

    tests = [
        ("Extension Discovery", test_extension_discovery),
        ("Extension Instantiation", test_extension_instantiation),
        ("Import Hooks", test_import_hooks),
        ("Export Hooks", test_export_hooks),
        ("glTF Discovery Simulation", test_gltf_discovery_simulation),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY:")
    logger.info("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1

    logger.info("-" * 60)
    logger.info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! Extension hooks are working correctly.")
        return 0
    else:
        logger.error(f"❌ {total - passed} test(s) failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
