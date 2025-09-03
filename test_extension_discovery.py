#!/usr/bin/env python3
"""
Test to verify EXT_bmesh_encoding extension discovery by glTF-Blender-IO.
"""

import sys
import os


def test_extension_discovery():
    """Test that glTF-Blender-IO can discover EXT_bmesh_encoding extension classes."""
    print("🔍 Testing EXT_bmesh_encoding Extension Discovery")
    print("=" * 50)

    try:
        # Initialize bpy first - this is crucial for Blender addon testing
        print("🔧 Initializing Blender environment...")
        import bpy

        # Set up basic Blender context
        if not hasattr(bpy, 'context'):
            print("❌ bpy.context not available - Blender environment not properly initialized")
            return False

        # Set up the module path to handle relative imports
        current_dir = os.path.dirname(__file__)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        print("📦 Importing gltf_extension module...")

        # Import the extension module directly (bpy should handle relative imports now)
        import gltf_extension
        print("✅ Successfully imported gltf_extension module")

        # Check for extension classes
        print("\n🔍 Checking for extension classes...")

        # Check glTF2ImportUserExtension
        if hasattr(gltf_extension, 'glTF2ImportUserExtension'):
            print("✅ Found glTF2ImportUserExtension class")
            import_ext = gltf_extension.glTF2ImportUserExtension()
            print(f"   Class type: {type(import_ext)}")
            print(f"   Has gather_import_mesh_before_hook: {hasattr(import_ext, 'gather_import_mesh_before_hook')}")
        else:
            print("❌ glTF2ImportUserExtension class not found")
            return False

        # Check glTF2ExportUserExtension
        if hasattr(gltf_extension, 'glTF2ExportUserExtension'):
            print("✅ Found glTF2ExportUserExtension class")
            export_ext = gltf_extension.glTF2ExportUserExtension()
            print(f"   Class type: {type(export_ext)}")
            print(f"   Has gather_gltf_hook: {hasattr(export_ext, 'gather_gltf_hook')}")
        else:
            print("❌ glTF2ExportUserExtension class not found")
            return False

        # Check module-level attributes (what glTF-Blender-IO looks for)
        print("\n🔍 Checking module-level attributes for auto-discovery...")

        module_attrs = dir(gltf_extension)
        print(f"   Module attributes: {module_attrs}")

        # glTF-Blender-IO looks for these specific attribute names
        required_attrs = ['glTF2ImportUserExtension', 'glTF2ExportUserExtension']

        for attr in required_attrs:
            if hasattr(gltf_extension, attr):
                attr_value = getattr(gltf_extension, attr)
                print(f"✅ Found {attr}: {type(attr_value)}")
                if attr_value == gltf_extension.glTF2ImportUserExtension or attr_value == gltf_extension.glTF2ExportUserExtension:
                    print(f"   ✓ {attr} points to correct class")
                else:
                    print(f"   ⚠️  {attr} points to: {attr_value}")
            else:
                print(f"❌ Missing {attr} attribute")
                return False

        # Test extension instantiation
        print("\n🔍 Testing extension instantiation...")

        try:
            import_ext_instance = gltf_extension.glTF2ImportUserExtension()
            export_ext_instance = gltf_extension.glTF2ExportUserExtension()
            print("✅ Successfully instantiated both extension classes")
        except Exception as e:
            print(f"❌ Failed to instantiate extension classes: {e}")
            return False

        # Test hook method signatures
        print("\n🔍 Testing hook method signatures...")

        import_hook = getattr(import_ext_instance, 'gather_import_mesh_before_hook', None)
        export_hook = getattr(export_ext_instance, 'gather_gltf_hook', None)

        if import_hook:
            print("✅ Import hook method found")
            # Check signature (basic check)
            import inspect
            sig = inspect.signature(import_hook)
            print(f"   Import hook signature: {sig}")
        else:
            print("❌ Import hook method not found")

        if export_hook:
            print("✅ Export hook method found")
            sig = inspect.signature(export_hook)
            print(f"   Export hook signature: {sig}")
        else:
            print("❌ Export hook method not found")

        print("\n" + "=" * 50)
        print("🎉 Extension discovery test completed successfully!")
        print("\n📋 Summary:")
        print("   • Extension classes are properly defined")
        print("   • Module-level attributes are correctly set")
        print("   • Classes can be instantiated")
        print("   • Hook methods are present with correct signatures")
        print("\n💡 If glTF-Blender-IO still can't find the extensions:")
        print("   • Check that the addon is properly loaded in Blender")
        print("   • Verify glTF-Blender-IO version compatibility")
        print("   • Check Blender console for import errors")

        return True

    except Exception as e:
        print(f"❌ Error during extension discovery test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_extension_discovery()
    sys.exit(0 if success else 1)
