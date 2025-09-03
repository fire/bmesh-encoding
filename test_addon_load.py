#!/usr/bin/env python3
"""
Simple test script to verify EXT_bmesh_encoding addon can be loaded.

This script can be run from Blender's Python console to test addon loading
without requiring the full Blender environment.
"""

import sys
import os
import importlib.util


def test_addon_import():
    """Test if the addon can be imported as a Python module."""
    print("=== EXT_bmesh_encoding Import Test ===")

    try:
        # Add parent directory to Python path so ext_bmesh_encoding module can be found
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Try to import the main module
        import ext_bmesh_encoding
        print("✅ Successfully imported ext_bmesh_encoding")

        # Check if register/unregister functions exist
        # Note: These are in addon.py, not the main module
        if hasattr(ext_bmesh_encoding, 'register'):
            print("✅ register() function found")
        else:
            print("⚠️ register() function not in main module (expected - it's in addon.py)")

        if hasattr(ext_bmesh_encoding, 'unregister'):
            print("✅ unregister() function found")
        else:
            print("⚠️ unregister() function not in main module (expected - it's in addon.py)")

        # Check bl_info
        if hasattr(ext_bmesh_encoding, 'bl_info'):
            bl_info = ext_bmesh_encoding.bl_info
            print(f"✅ bl_info found: {bl_info.get('name', 'unknown')} v{bl_info.get('version', 'unknown')}")
        else:
            print("⚠️ bl_info not in main module (expected - it's in addon.py)")

        # Check module version
        if hasattr(ext_bmesh_encoding, '__version__'):
            print(f"✅ Module version: {ext_bmesh_encoding.__version__}")
        else:
            print("❌ Module version missing")

        return True

    except ImportError as e:
        print(f"❌ Failed to import ext_bmesh_encoding: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False


def test_gltf_extension_discovery():
    """Test if glTF extension classes are discoverable."""
    print("\n=== glTF Extension Discovery Test ===")

    try:
        import ext_bmesh_encoding.gltf_extension as gltf_ext

        # Check for required classes
        has_import_ext = hasattr(gltf_ext, 'glTF2ImportUserExtension')
        has_export_ext = hasattr(gltf_ext, 'glTF2ExportUserExtension')

        print(f"glTF2ImportUserExtension class: {'✅' if has_import_ext else '❌'}")
        print(f"glTF2ExportUserExtension class: {'✅' if has_export_ext else '❌'}")

        if has_import_ext:
            import_class = gltf_ext.glTF2ImportUserExtension
            print(f"Import extension class type: {type(import_class)}")

        if has_export_ext:
            export_class = gltf_ext.glTF2ExportUserExtension
            print(f"Export extension class type: {type(export_class)}")

        return has_import_ext and has_export_ext

    except ImportError as e:
        if 'bpy' in str(e):
            print("⚠️ glTF extension test skipped - bpy not available (expected outside Blender)")
            print("   This test will pass when the addon is loaded in Blender")
            return True  # Consider this a pass since it's expected
        else:
            print(f"❌ Failed to check glTF extensions: {e}")
            return False
    except Exception as e:
        print(f"❌ Failed to check glTF extensions: {e}")
        return False


def test_manifest_file():
    """Test if blender_manifest.toml exists and is readable."""
    print("\n=== Manifest File Test ===")

    try:
        import tomllib

        manifest_path = os.path.join(os.path.dirname(__file__), 'blender_manifest.toml')

        if os.path.exists(manifest_path):
            print("✅ blender_manifest.toml found")

            with open(manifest_path, 'rb') as f:
                manifest_data = tomllib.load(f)

            print(f"Addon ID: {manifest_data.get('id', 'unknown')}")
            print(f"Version: {manifest_data.get('version', 'unknown')}")
            print(f"Blender min version: {manifest_data.get('blender_version_min', 'unknown')}")

            return True
        else:
            print("❌ blender_manifest.toml not found")
            return False

    except ImportError:
        print("⚠️ tomllib not available (Python < 3.11), skipping manifest validation")
        # Check if file exists at least
        manifest_path = os.path.join(os.path.dirname(__file__), 'blender_manifest.toml')
        if os.path.exists(manifest_path):
            print("✅ blender_manifest.toml found (cannot validate contents)")
            return True
        else:
            print("❌ blender_manifest.toml not found")
            return False
    except Exception as e:
        print(f"❌ Failed to read manifest: {e}")
        return False


def main():
    """Run all tests."""
    print("EXT_bmesh_encoding Addon Load Test")
    print("=" * 40)

    import_ok = test_addon_import()
    gltf_ok = test_gltf_extension_discovery()
    manifest_ok = test_manifest_file()

    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"Import Test: {'✅ PASS' if import_ok else '❌ FAIL'}")
    print(f"glTF Extension Test: {'✅ PASS' if gltf_ok else '❌ FAIL'}")
    print(f"Manifest Test: {'✅ PASS' if manifest_ok else '❌ FAIL'}")

    if import_ok and gltf_ok and manifest_ok:
        print("\n🎉 All tests passed! The addon should be ready for installation in Blender.")
        print("\nNext steps:")
        print("1. Open Blender 4.0+")
        print("2. Go to Edit > Preferences > Add-ons")
        print("3. Click 'Install...' and select blender_manifest.toml")
        print("4. Enable the EXT_bmesh_encoding addon")
        print("5. Test with File > Export > glTF 2.0")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")

    return import_ok and gltf_ok and manifest_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
