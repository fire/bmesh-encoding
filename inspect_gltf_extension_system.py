#!/usr/bin/env python3
"""
Python introspection script to examine glTF-Blender-IO extension system.
This will help us understand what hooks are available and how they work.
"""

import sys
import inspect
import importlib
from typing import Dict, List, Any


def inspect_gltf_module():
    """Inspect the glTF-Blender-IO module for extension hooks."""
    print("🔍 Inspecting glTF-Blender-IO Extension System")
    print("=" * 50)

    try:
        # Try to import glTF-Blender-IO
        gltf_module = importlib.import_module('io_scene_gltf2')
        print(f"✅ Successfully imported glTF module: {gltf_module}")
        print(f"   Module file: {gltf_module.__file__}")

        # Get all attributes of the module
        module_attrs = dir(gltf_module)
        print(f"\n📋 Module attributes ({len(module_attrs)}):")
        for attr in sorted(module_attrs):
            obj = getattr(gltf_module, attr)
            obj_type = type(obj).__name__
            print(f"   {attr}: {obj_type}")

        # Look for extension-related classes and functions
        extension_related = []
        for attr_name in module_attrs:
            if 'extension' in attr_name.lower():
                extension_related.append(attr_name)

        print(f"\n🔧 Extension-related attributes ({len(extension_related)}):")
        for attr in extension_related:
            obj = getattr(gltf_module, attr)
            print(f"   {attr}: {type(obj).__name__}")

            # If it's a class, inspect its methods
            if inspect.isclass(obj):
                methods = [m for m in dir(obj) if not m.startswith('_') and callable(getattr(obj, m))]
                print(f"      Methods: {methods}")

        # Look for hook-related functions
        hook_related = []
        for attr_name in module_attrs:
            if 'hook' in attr_name.lower() or 'gather' in attr_name.lower():
                hook_related.append(attr_name)

        print(f"\n🎣 Hook-related attributes ({len(hook_related)}):")
        for attr in hook_related:
            obj = getattr(gltf_module, attr)
            print(f"   {attr}: {type(obj).__name__}")

            if callable(obj):
                try:
                    sig = inspect.signature(obj)
                    print(f"      Signature: {sig}")
                except Exception as e:
                    print(f"      Signature: Unable to inspect ({e})")

        # Look for export-related classes
        export_related = []
        for attr_name in module_attrs:
            if 'export' in attr_name.lower():
                export_related.append(attr_name)

        print(f"\n📤 Export-related attributes ({len(export_related)}):")
        for attr in export_related:
            obj = getattr(gltf_module, attr)
            print(f"   {attr}: {type(obj).__name__}")

            # If it's a class, inspect its methods
            if inspect.isclass(obj):
                methods = [m for m in dir(obj) if not m.startswith('_') and callable(getattr(obj, m))]
                print(f"      Methods: {methods}")

                # Look for extension-related methods
                ext_methods = [m for m in methods if 'extension' in m.lower()]
                if ext_methods:
                    print(f"         Extension methods: {ext_methods}")

        # Try to find the main export operator
        try:
            export_operator = getattr(gltf_module, 'ExportGLTF2', None)
            if export_operator:
                print(f"\n🎯 Found ExportGLTF2 operator: {export_operator}")
                print(f"   Type: {type(export_operator)}")

                if inspect.isclass(export_operator):
                    methods = [m for m in dir(export_operator) if not m.startswith('_')]
                    print(f"   Methods: {methods}")

                    # Look for extension-related methods
                    ext_methods = [m for m in methods if 'extension' in m.lower()]
                    if ext_methods:
                        print(f"   Extension methods: {ext_methods}")

                        for method in ext_methods:
                            try:
                                method_obj = getattr(export_operator, method)
                                if callable(method_obj):
                                    sig = inspect.signature(method_obj)
                                    print(f"      {method}: {sig}")
                            except Exception as e:
                                print(f"      {method}: Unable to inspect ({e})")
        except Exception as e:
            print(f"❌ Error inspecting ExportGLTF2: {e}")

        # Look for submodules
        print("\n📚 Submodules:")
        if hasattr(gltf_module, '__path__'):
            import os
            import pkgutil

            submodules = []
            for importer, modname, ispkg in pkgutil.iter_modules(gltf_module.__path__):
                submodules.append(modname)

            print(f"   Found {len(submodules)} submodules: {submodules}")

            # Try to inspect key submodules
            for submod_name in ['blender', 'exp', 'com']:
                try:
                    submod = importlib.import_module(f'io_scene_gltf2.{submod_name}')
                    print(f"\n   📖 Submodule {submod_name}:")
                    print(f"      File: {submod.__file__}")

                    # Look for extension-related items in submodule
                    sub_attrs = dir(submod)
                    ext_items = [a for a in sub_attrs if 'extension' in a.lower()]
                    if ext_items:
                        print(f"      Extension items: {ext_items}")

                except ImportError as e:
                    print(f"   ❌ Could not import submodule {submod_name}: {e}")

    except ImportError as e:
        print(f"❌ Could not import glTF-Blender-IO: {e}")
        print("💡 Make sure Blender's scripts directory is in Python path")

        # Try to find Blender's scripts directory
        import os
        possible_paths = [
            '/opt/blender/blender-4.5.1-linux-x64/4.5/scripts',
            '/usr/share/blender/scripts',
            '/Applications/Blender.app/Contents/Resources/4.5/scripts'
        ]

        print("\n🔍 Looking for Blender scripts directory:")
        for path in possible_paths:
            if os.path.exists(path):
                print(f"   ✅ Found: {path}")
                print(f"   💡 Try adding this to PYTHONPATH")
                break
        else:
            print("   ❌ Could not find Blender scripts directory")


def inspect_extension_base_classes():
    """Try to find and inspect extension base classes."""
    print("\n🎯 Inspecting Extension Base Classes")
    print("=" * 40)

    try:
        # Try to import extension base classes
        from io_scene_gltf2.blender import exp as gltf_exp

        print(f"✅ Imported gltf_exp: {gltf_exp}")

        # Look for extension-related classes
        exp_attrs = dir(gltf_exp)
        ext_classes = []

        for attr in exp_attrs:
            obj = getattr(gltf_exp, attr)
            if inspect.isclass(obj):
                # Check if it's an extension-related class
                if 'extension' in attr.lower() or 'Extension' in attr:
                    ext_classes.append((attr, obj))

        print(f"📋 Found {len(ext_classes)} extension-related classes:")
        for name, cls in ext_classes:
            print(f"   {name}: {cls}")

            # Get methods
            methods = [m for m in dir(cls) if not m.startswith('_') and callable(getattr(cls, m))]
            print(f"      Methods: {methods}")

            # Check if it has gather methods
            gather_methods = [m for m in methods if 'gather' in m.lower()]
            if gather_methods:
                print(f"         Gather methods: {gather_methods}")

                for method in gather_methods:
                    try:
                        method_obj = getattr(cls, method)
                        sig = inspect.signature(method_obj)
                        print(f"            {method}: {sig}")
                    except Exception as e:
                        print(f"            {method}: Unable to inspect ({e})")

    except ImportError as e:
        print(f"❌ Could not import gltf_exp: {e}")


def main():
    """Main inspection function."""
    print("🔬 glTF-Blender-IO Extension System Introspection")
    print("=" * 55)

    # Add Blender scripts to path if possible
    import sys
    blender_scripts = '/opt/blender/blender-4.5.1-linux-x64/4.5/scripts'
    if blender_scripts not in sys.path:
        sys.path.insert(0, blender_scripts)
        print(f"📍 Added to sys.path: {blender_scripts}")

    inspect_gltf_module()
    inspect_extension_base_classes()

    print("\n🎉 Introspection complete!")
    print("Use this information to understand how glTF-Blender-IO extension hooks work.")


if __name__ == "__main__":
    main()
