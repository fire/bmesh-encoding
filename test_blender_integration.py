#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Diagnostic script to test EXT_bmesh_encoding integration with Blender.

Run this script in Blender's Python console to verify extension integration.
"""

import bpy
import sys

def test_extension_discovery():
    """Test if EXT_bmesh_encoding extension classes are discoverable."""
    print("=== EXT_bmesh_encoding Discovery Test ===")

    # Check if addon is loaded
    if 'ext_bmesh_encoding' not in bpy.context.preferences.addons:
        print("❌ EXT_bmesh_encoding addon not found in preferences")
        return False

    addon_module = bpy.context.preferences.addons['ext_bmesh_encoding']
    print(f"✅ Addon found: {addon_module}")

    # Check if extension classes are discoverable
    module = addon_module.module
    print(f"Module: {module}")

    has_import_ext = hasattr(module, 'glTF2ImportUserExtension')
    has_export_ext = hasattr(module, 'glTF2ExportUserExtension')

    print(f"glTF2ImportUserExtension found: {has_import_ext}")
    print(f"glTF2ExportUserExtension found: {has_export_ext}")

    if has_import_ext:
        import_ext_class = getattr(module, 'glTF2ImportUserExtension')
        print(f"Import extension class: {import_ext_class}")
        try:
            import_ext_instance = import_ext_class()
            print(f"✅ Import extension instantiated: {import_ext_instance}")
        except Exception as e:
            print(f"❌ Import extension instantiation failed: {e}")

    if has_export_ext:
        export_ext_class = getattr(module, 'glTF2ExportUserExtension')
        print(f"Export extension class: {export_ext_class}")
        try:
            export_ext_instance = export_ext_class()
            print(f"✅ Export extension instantiated: {export_ext_instance}")
        except Exception as e:
            print(f"❌ Export extension instantiation failed: {e}")

    return has_import_ext and has_export_ext

def test_gltf_addon_discovery():
    """Test if glTF-Blender-IO can discover our extensions."""
    print("\n=== glTF-Blender-IO Discovery Test ===")

    if 'io_scene_gltf2' not in bpy.context.preferences.addons:
        print("❌ glTF-Blender-IO addon not found")
        return False

    # Simulate glTF-Blender-IO's extension discovery
    user_extensions = []

    for addon_name in bpy.context.preferences.addons.keys():
        if addon_name == 'io_scene_gltf2':
            continue  # Skip the glTF addon itself

        try:
            addon_prefs = bpy.context.preferences.addons[addon_name]
            module = addon_prefs.module

            if hasattr(module, 'glTF2ImportUserExtension'):
                ext_class = getattr(module, 'glTF2ImportUserExtension')
                user_extensions.append(('import', addon_name, ext_class))

            if hasattr(module, 'glTF2ExportUserExtension'):
                ext_class = getattr(module, 'glTF2ExportUserExtension')
                user_extensions.append(('export', addon_name, ext_class))

        except Exception as e:
            print(f"Error checking addon {addon_name}: {e}")

    print(f"Discovered extensions: {len(user_extensions)}")
    for ext_type, addon_name, ext_class in user_extensions:
        print(f"  {ext_type}: {addon_name} -> {ext_class}")

    ext_bmesh_extensions = [ext for ext in user_extensions if 'ext_bmesh_encoding' in ext[1]]
    print(f"EXT_bmesh_encoding extensions found: {len(ext_bmesh_extensions)}")

    return len(ext_bmesh_extensions) > 0

def main():
    """Run all diagnostic tests."""
    print("EXT_bmesh_encoding Blender Integration Diagnostics")
    print("=" * 50)

    discovery_ok = test_extension_discovery()
    gltf_discovery_ok = test_gltf_addon_discovery()

    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Extension Discovery: {'✅ PASS' if discovery_ok else '❌ FAIL'}")
    print(f"glTF Integration: {'✅ PASS' if gltf_discovery_ok else '❌ FAIL'}")

    if discovery_ok and gltf_discovery_ok:
        print("\n🎉 EXT_bmesh_encoding should be working with glTF-Blender-IO!")
        print("\nNext steps:")
        print("1. Create a mesh with quads/ngons")
        print("2. Export as glTF using File > Export > glTF 2.0")
        print("3. Check console for EXT_bmesh_encoding messages")
        print("4. Import the glTF file")
        print("5. Verify quads/ngons are preserved")
    else:
        print("\n❌ Issues found. Check the error messages above.")

if __name__ == "__main__":
    main()
