#!/usr/bin/env python3
"""
Direct test of EXT_bmesh_encoding extension functionality.
Tests the extension classes and hooks directly without Blender addon system.
"""

import sys
import os
import inspect


def test_direct_extension_import():
    """Test importing extension modules directly."""
    print("🔍 Testing direct extension import...")

    try:
        # Set up the module path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # Import the extension module directly
        print("📦 Importing gltf_extension module directly...")
        import gltf_extension
        print("✅ Successfully imported gltf_extension module")

        return gltf_extension

    except Exception as e:
        print(f"❌ Failed to import gltf_extension: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_extension_classes(gltf_ext):
    """Test the extension classes directly."""
    print("\n🔍 Testing extension classes...")

    if not gltf_ext:
        print("❌ No gltf_extension module available")
        return False

    success = True

    # Test glTF2ImportUserExtension
    if hasattr(gltf_ext, 'glTF2ImportUserExtension'):
        import_class = gltf_ext.glTF2ImportUserExtension
        print(f"✅ Found glTF2ImportUserExtension: {import_class}")

        # Check required methods
        required_methods = ['gather_import_mesh_before_hook', 'gather_import_armature_bone_after_hook']
        for method_name in required_methods:
            if hasattr(import_class, method_name):
                method = getattr(import_class, method_name)
                sig = inspect.signature(method)
                print(f"   ✅ {method_name}: {sig}")
            else:
                print(f"   ❌ Missing {method_name}")
                success = False
    else:
        print("❌ glTF2ImportUserExtension not found")
        success = False

    # Test glTF2ExportUserExtension
    if hasattr(gltf_ext, 'glTF2ExportUserExtension'):
        export_class = gltf_ext.glTF2ExportUserExtension
        print(f"✅ Found glTF2ExportUserExtension: {export_class}")

        # Check required methods
        if hasattr(export_class, 'gather_gltf_hook'):
            method = getattr(export_class, 'gather_gltf_hook')
            sig = inspect.signature(method)
            print(f"   ✅ gather_gltf_hook: {sig}")
        else:
            print("   ❌ Missing gather_gltf_hook")
            success = False
    else:
        print("❌ glTF2ExportUserExtension not found")
        success = False

    return success


def test_extension_instantiation(gltf_ext):
    """Test instantiating extension classes."""
    print("\n🔍 Testing extension instantiation...")

    if not gltf_ext:
        return False

    success = True

    # Mock the required dependencies to avoid import errors
    class MockBMeshEncoder:
        def encode_object(self, obj):
            return {"mock": "encoder_data"}

    class MockBMeshDecoder:
        def decode_gltf_extension_to_bmesh(self, data, gltf):
            return None

    # Temporarily replace the imports
    original_modules = {}
    try:
        # Mock the modules
        sys.modules['encoding'] = type('MockEncoding', (), {'BmeshEncoder': MockBMeshEncoder})()
        sys.modules['decoding'] = type('MockDecoding', (), {'BmeshDecoder': MockBMeshDecoder})()
        sys.modules['logger'] = type('MockLogger', (), {'get_logger': lambda x: print})()

        # Test instantiation
        if hasattr(gltf_ext, 'glTF2ExportUserExtension'):
            try:
                export_ext = gltf_ext.glTF2ExportUserExtension()
                print("✅ Successfully instantiated glTF2ExportUserExtension")
            except Exception as e:
                print(f"❌ Failed to instantiate glTF2ExportUserExtension: {e}")
                success = False

        if hasattr(gltf_ext, 'glTF2ImportUserExtension'):
            try:
                import_ext = gltf_ext.glTF2ImportUserExtension()
                print("✅ Successfully instantiated glTF2ImportUserExtension")
            except Exception as e:
                print(f"❌ Failed to instantiate glTF2ImportUserExtension: {e}")
                success = False

    except Exception as e:
        print(f"❌ Error during instantiation test: {e}")
        success = False
    finally:
        # Restore original modules
        for name in ['encoding', 'decoding', 'logger']:
            if name in original_modules:
                sys.modules[name] = original_modules[name]
            elif name in sys.modules:
                del sys.modules[name]

    return success


def test_hook_execution(gltf_ext):
    """Test executing extension hooks with mock data."""
    print("\n🔍 Testing hook execution...")

    if not gltf_ext:
        return False

    # Mock dependencies
    class MockBMeshEncoder:
        def encode_object(self, obj):
            return {"mock": "encoder_data"}

    class MockBMeshDecoder:
        def decode_gltf_extension_to_bmesh(self, data, gltf):
            return None

    # Set up mock modules
    sys.modules['encoding'] = type('MockEncoding', (), {'BmeshEncoder': MockBMeshEncoder})()
    sys.modules['decoding'] = type('MockDecoding', (), {'BmeshDecoder': MockBMeshDecoder})()
    sys.modules['logger'] = type('MockLogger', (), {'get_logger': lambda x: print})()

    try:
        if hasattr(gltf_ext, 'glTF2ExportUserExtension'):
            export_ext = gltf_ext.glTF2ExportUserExtension()
            print("✅ Created export extension instance")

            # Create mock parameters
            mock_gltf_object = type('MockGLTFObject', (), {})()
            mock_blender_object = type('MockBlenderObject', (), {
                'type': 'MESH',
                'name': 'TestMesh'
            })()
            mock_export_settings = type('MockExportSettings', (), {
                'export_ext_bmesh_encoding': True
            })()
            mock_exporter = type('MockExporter', (), {})()

            # Test the hook with detailed debugging
            if hasattr(export_ext, 'gather_gltf_hook'):
                print("🔄 Calling gather_gltf_hook...")

                # Debug: Check extension state before hook call
                print(f"   Encoder available: {export_ext.encoder is not None}")
                print(f"   Decoder available: {export_ext.decoder is not None}")
                print(f"   Blender object type: {getattr(mock_blender_object, 'type', 'unknown')}")
                print(f"   Export settings: {getattr(mock_export_settings, 'export_ext_bmesh_encoding', 'unknown')}")

                # Call the hook
                try:
                    export_ext.gather_gltf_hook(
                        mock_gltf_object,
                        mock_blender_object,
                        mock_export_settings,
                        mock_exporter
                    )
                    print("✅ gather_gltf_hook executed without exception")
                except Exception as hook_error:
                    print(f"❌ Hook execution failed with error: {hook_error}")
                    return False

                # Debug: Check glTF object state after hook call
                print(f"   glTF object has extensions: {hasattr(mock_gltf_object, 'extensions')}")

                if hasattr(mock_gltf_object, 'extensions'):
                    print("📋 Extensions object found in glTF object")
                    extensions = mock_gltf_object.extensions
                    print(f"   Extensions type: {type(extensions)}")

                    # Check if it's a dict-like object
                    if hasattr(extensions, 'keys'):
                        ext_keys = list(extensions.keys())
                        print(f"   Extension keys: {ext_keys}")

                        if 'EXT_bmesh_encoding' in ext_keys:
                            print("🎉 EXT_bmesh_encoding data found in glTF object!")
                            ext_data = extensions['EXT_bmesh_encoding']
                            print(f"   Extension data: {ext_data}")
                            return True
                        else:
                            print("❌ EXT_bmesh_encoding data NOT found in extensions")
                            print(f"   Available extensions: {ext_keys}")
                            return False
                    else:
                        print(f"   Extensions object doesn't have keys(): {dir(extensions)}")
                        # Try direct attribute access
                        if hasattr(extensions, 'EXT_bmesh_encoding'):
                            print("🎉 EXT_bmesh_encoding found via attribute access!")
                            return True
                        else:
                            print("❌ EXT_bmesh_encoding NOT found via attribute access")
                            return False
                else:
                    print("❌ No extensions object found in glTF object")
                    print(f"   glTF object attributes: {[attr for attr in dir(mock_gltf_object) if not attr.startswith('_')]}")
                    return False
            else:
                print("❌ gather_gltf_hook method not found")
                return False
        else:
            print("❌ glTF2ExportUserExtension not available")
            return False

    except Exception as e:
        print(f"❌ Error during hook execution: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up mock modules
        for name in ['encoding', 'decoding', 'logger']:
            if name in sys.modules:
                del sys.modules[name]


def main():
    """Run the direct extension test."""
    print("EXT_bmesh_encoding Direct Extension Test")
    print("=" * 50)
    print("Testing extension functionality directly without Blender addon system")
    print("=" * 50)

    # Test direct import
    gltf_ext = test_direct_extension_import()
    if not gltf_ext:
        print("\n❌ Cannot proceed without gltf_extension module")
        return False

    # Test extension classes
    class_success = test_extension_classes(gltf_ext)

    # Test instantiation
    instantiation_success = test_extension_instantiation(gltf_ext)

    # Test hook execution
    hook_success = test_hook_execution(gltf_ext)

    print("\n" + "=" * 50)
    print("DIRECT EXTENSION TEST SUMMARY:")
    print(f"Import:     {'✅ PASS' if gltf_ext else '❌ FAIL'}")
    print(f"Classes:    {'✅ PASS' if class_success else '❌ FAIL'}")
    print(f"Instantiation: {'✅ PASS' if instantiation_success else '❌ FAIL'}")
    print(f"Hook Execution: {'✅ PASS' if hook_success else '❌ FAIL'}")

    overall_success = all([gltf_ext, class_success, instantiation_success, hook_success])

    if overall_success:
        print("\n🎉 EXT_bmesh_encoding extension is working correctly!")
        print("   The extension classes, methods, and hooks are all functional.")
        print("   The issue is likely in the Blender addon registration/integration.")
        print("\n🔧 Next steps:")
        print("   1. Test in actual Blender environment")
        print("   2. Check Blender console for addon loading errors")
        print("   3. Verify glTF-Blender-IO version compatibility")
        print("   4. Ensure addon is properly enabled in Blender preferences")
    else:
        print("\n❌ EXT_bmesh_encoding extension has issues:")
        if not class_success:
            print("   • Extension classes are not properly defined")
        if not instantiation_success:
            print("   • Extension classes cannot be instantiated")
        if not hook_success:
            print("   • Extension hooks are not working correctly")

    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
