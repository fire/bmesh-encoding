#!/usr/bin/env python3
"""
Diagnostic test for glTF-Blender-IO extension discovery mechanism.
This test simulates how glTF-Blender-IO discovers and calls EXT_bmesh_encoding hooks.
"""

import sys
import os
import bpy
import inspect
from pathlib import Path


class MockGLTFBlenderIO:
    """Mock glTF-Blender-IO system to test extension discovery."""

    def __init__(self):
        self.discovered_extensions = {}
        self.called_hooks = []
        self.errors = []

    def register_addon_manually(self):
        """Manually register the EXT_bmesh_encoding addon in mock bpy environment."""
        print("🔧 Manually registering EXT_bmesh_encoding addon...")

        try:
            # Set up the module path to make ext_bmesh_encoding importable
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)

            # Instead of importing the full module, load the __init__.py directly
            init_file = os.path.join(current_dir, '__init__.py')
            if os.path.exists(init_file):
                # Execute the __init__.py file in a controlled namespace
                namespace = {}
                with open(init_file, 'r', encoding='utf-8') as f:
                    code = f.read()

                # Add necessary modules to namespace
                namespace['__file__'] = init_file
                namespace['__name__'] = 'ext_bmesh_encoding'

                # Execute the code
                exec(code, namespace)

                # Register the addon
                if 'register' in namespace:
                    namespace['register']()
                    print("✅ Addon registered successfully")
                else:
                    print("⚠️ No register function found in __init__.py")

                # Check if addon is already registered or try to register it properly
                addon_name = "ext_bmesh_encoding"
                if addon_name not in bpy.context.preferences.addons:
                    print(f"⚠️ Addon '{addon_name}' not in bpy.context.preferences.addons")
                    print("   This is expected in uv environment - proceeding with discovery")
                else:
                    print("✅ Addon found in bpy.context.preferences.addons")

                return True
            else:
                self.errors.append("__init__.py not found")
                return False

        except Exception as e:
            self.errors.append(f"Failed to register addon manually: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return False

    def discover_extensions(self):
        """Simulate glTF-Blender-IO's extension discovery process."""
        print("🔍 Simulating glTF-Blender-IO extension discovery...")

        # glTF-Blender-IO looks for extensions in specific places:
        # 1. bpy.context.preferences.addons (for enabled addons)
        # 2. Module-level attributes in addon modules
        # 3. Specific class names and hook methods

        try:
            # First, ensure addon is registered
            addon_registered = self.register_addon_manually()
            if not addon_registered:
                return False

            # Check if EXT_bmesh_encoding addon is loaded
            addon_name = "ext_bmesh_encoding"
            if addon_name not in bpy.context.preferences.addons:
                self.errors.append(f"Addon '{addon_name}' not found in bpy.context.preferences.addons")
                return False

            addon = bpy.context.preferences.addons[addon_name]
            print(f"✅ Found addon: {addon.module}")

            # Try to import the extension module
            try:
                import ext_bmesh_encoding.gltf_extension as gltf_ext
                print("✅ Successfully imported gltf_extension module")
            except ImportError as e:
                self.errors.append(f"Failed to import gltf_extension: {e}")
                return False

            # Check for required extension classes
            required_classes = ['glTF2ImportUserExtension', 'glTF2ExportUserExtension']

            for class_name in required_classes:
                if hasattr(gltf_ext, class_name):
                    ext_class = getattr(gltf_ext, class_name)
                    print(f"✅ Found extension class: {class_name}")

                    # Check if it's actually a class
                    if not inspect.isclass(ext_class):
                        self.errors.append(f"{class_name} is not a class: {type(ext_class)}")
                        continue

                    # Store discovered extension
                    self.discovered_extensions[class_name] = ext_class

                    # Check for required hook methods
                    if class_name == 'glTF2ImportUserExtension':
                        required_hooks = ['gather_import_mesh_before_hook', 'gather_import_armature_bone_after_hook']
                    else:  # glTF2ExportUserExtension
                        required_hooks = ['gather_gltf_hook']

                    for hook_name in required_hooks:
                        if hasattr(ext_class, hook_name):
                            hook_method = getattr(ext_class, hook_name)
                            print(f"   ✅ Found hook method: {hook_name}")

                            # Check method signature
                            try:
                                sig = inspect.signature(hook_method)
                                print(f"   📝 Hook signature: {sig}")
                            except Exception as e:
                                self.errors.append(f"Could not get signature for {hook_name}: {e}")
                        else:
                            self.errors.append(f"Missing hook method: {hook_name} in {class_name}")

                else:
                    self.errors.append(f"Missing extension class: {class_name}")

            # Check module-level attributes (glTF-Blender-IO looks for these)
            print("\n🔍 Checking module-level attributes...")
            module_attrs = dir(gltf_ext)

            for class_name in required_classes:
                if class_name in module_attrs:
                    print(f"✅ Module attribute found: {class_name}")
                else:
                    self.errors.append(f"Module attribute missing: {class_name}")

            return len(self.errors) == 0

        except Exception as e:
            self.errors.append(f"Extension discovery failed: {e}")
            return False

    def test_hook_invocation(self):
        """Test calling the discovered extension hooks."""
        print("\n🔄 Testing extension hook invocation...")

        if not self.discovered_extensions:
            self.errors.append("No extensions discovered to test")
            return False

        # Test glTF2ExportUserExtension (most relevant for our issue)
        if 'glTF2ExportUserExtension' in self.discovered_extensions:
            export_class = self.discovered_extensions['glTF2ExportUserExtension']

            try:
                # Create instance
                export_ext = export_class()
                print("✅ Successfully instantiated glTF2ExportUserExtension")

                # Test gather_gltf_hook
                if hasattr(export_ext, 'gather_gltf_hook'):
                    print("🔄 Calling gather_gltf_hook...")

                    # Create mock parameters that glTF-Blender-IO would pass
                    mock_gltf_object = type('MockGLTFObject', (), {})()
                    mock_blender_object = type('MockBlenderObject', (), {
                        'type': 'MESH',
                        'name': 'TestMesh'
                    })()
                    mock_export_settings = type('MockExportSettings', (), {
                        'export_ext_bmesh_encoding': True
                    })()
                    mock_exporter = type('MockExporter', (), {})()

                    # Call the hook
                    export_ext.gather_gltf_hook(
                        mock_gltf_object,
                        mock_blender_object,
                        mock_export_settings,
                        mock_exporter
                    )

                    self.called_hooks.append('gather_gltf_hook')
                    print("✅ gather_gltf_hook called successfully")

                    # Check if extension data was added to glTF object
                    if hasattr(mock_gltf_object, 'extensions'):
                        print("📋 Extensions found in glTF object after hook call")
                        if hasattr(mock_gltf_object.extensions, 'EXT_bmesh_encoding'):
                            print("🎉 EXT_bmesh_encoding data found!")
                            return True
                        else:
                            print("❌ EXT_bmesh_encoding data NOT found in glTF object")
                            return False
                    else:
                        print("❌ No extensions object found in glTF object")
                        return False

                else:
                    self.errors.append("gather_gltf_hook method not found")
                    return False

            except Exception as e:
                self.errors.append(f"Hook invocation failed: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return False
        else:
            self.errors.append("glTF2ExportUserExtension not discovered")
            return False

    def simulate_gltf_export_pipeline(self):
        """Simulate the complete glTF export pipeline."""
        print("\n🔄 Simulating complete glTF export pipeline...")

        # This simulates the typical glTF export flow:
        # 1. Export operator called
        # 2. Extensions discovered
        # 3. Hooks called during export
        # 4. glTF file written

        try:
            # Step 1: Discover extensions
            discovery_success = self.discover_extensions()
            if not discovery_success:
                return False

            # Step 2: Simulate export process
            print("📤 Simulating glTF export process...")

            # Create mock export context
            mock_context = type('MockContext', (), {})()

            # This would be where glTF-Blender-IO calls our hooks
            hook_success = self.test_hook_invocation()
            if not hook_success:
                return False

            print("✅ glTF export pipeline simulation completed")
            return True

        except Exception as e:
            self.errors.append(f"Export pipeline simulation failed: {e}")
            return False

    def print_diagnostic_report(self):
        """Print comprehensive diagnostic report."""
        print("\n" + "="*60)
        print("GLTF-BLENDER-IO EXTENSION DISCOVERY DIAGNOSTIC REPORT")
        print("="*60)

        print(f"\n🔍 Extensions Discovered: {len(self.discovered_extensions)}")
        for name, ext_class in self.discovered_extensions.items():
            print(f"   • {name}: {ext_class}")

        print(f"\n🔄 Hooks Called: {len(self.called_hooks)}")
        for hook in self.called_hooks:
            print(f"   • {hook}")

        if self.errors:
            print(f"\n❌ Errors Found: {len(self.errors)}")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        else:
            print("\n✅ No errors found")

        print("\n" + "="*60)

        # Provide troubleshooting recommendations
        if self.errors:
            print("🔧 TROUBLESHOOTING RECOMMENDATIONS:")
            print("   1. Check Blender console for import errors during addon loading")
            print("   2. Verify addon is enabled in Blender preferences")
            print("   3. Check glTF-Blender-IO version compatibility")
            print("   4. Ensure extension classes are properly defined")
            print("   5. Verify hook method signatures match glTF-Blender-IO expectations")


def main():
    """Run the glTF-Blender-IO extension discovery diagnostic."""
    print("EXT_bmesh_encoding glTF-Blender-IO Integration Diagnostic")
    print("=" * 60)
    print("This test simulates glTF-Blender-IO's extension discovery process")
    print("to identify why EXT_bmesh_encoding hooks aren't being called.")
    print("=" * 60)

    # Create mock glTF-Blender-IO system
    mock_gltf_io = MockGLTFBlenderIO()

    # Run diagnostic tests
    discovery_success = mock_gltf_io.discover_extensions()
    hook_success = mock_gltf_io.test_hook_invocation()
    pipeline_success = mock_gltf_io.simulate_gltf_export_pipeline()

    # Print diagnostic report
    mock_gltf_io.print_diagnostic_report()

    # Overall assessment
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY:")
    print(f"Discovery: {'✅ PASS' if discovery_success else '❌ FAIL'}")
    print(f"Hook Test: {'✅ PASS' if hook_success else '❌ FAIL'}")
    print(f"Pipeline:  {'✅ PASS' if pipeline_success else '❌ FAIL'}")

    overall_success = discovery_success and hook_success and pipeline_success

    if overall_success:
        print("\n🎉 EXT_bmesh_encoding extension discovery is working correctly!")
        print("   The issue may be in the real glTF-Blender-IO integration.")
        print("   Check Blender console for runtime errors during actual export.")
    else:
        print("\n❌ EXT_bmesh_encoding extension discovery has issues:")
        if not discovery_success:
            print("   • Extension classes not being discovered properly")
        if not hook_success:
            print("   • Hook methods not working as expected")
        if not pipeline_success:
            print("   • Integration with glTF export pipeline failing")

    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
