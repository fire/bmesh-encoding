#!/usr/bin/env python3
"""
Test script to validate EXT_bmesh_encoding in glTF files.

This script checks if glTF files contain valid EXT_bmesh_encoding extension data
and provides diagnostic information about the extension processing.
"""

import json
import os
import sys
from typing import Dict, Any, Optional, Tuple


class GLTFExtensionValidator:
    """Validator for EXT_bmesh_encoding in glTF files."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def log_error(self, message: str):
        """Log an error message."""
        self.errors.append(message)
        print(f"❌ {message}")

    def log_warning(self, message: str):
        """Log a warning message."""
        self.warnings.append(message)
        print(f"⚠️  {message}")

    def log_info(self, message: str):
        """Log an info message."""
        self.info.append(message)
        print(f"ℹ️  {message}")

    def log_success(self, message: str):
        """Log a success message."""
        print(f"✅ {message}")

    def validate_gltf_file(self, gltf_path: str) -> bool:
        """Validate a glTF file for EXT_bmesh_encoding presence and validity."""
        print(f"\n🔍 Validating glTF file: {gltf_path}")
        print("=" * 60)

        try:
            with open(gltf_path, 'r', encoding='utf-8') as f:
                gltf_data = json.load(f)
        except Exception as e:
            self.log_error(f"Failed to load glTF file: {e}")
            return False

        return self.validate_gltf_data(gltf_data)

    def validate_gltf_data(self, gltf_data: Dict[str, Any]) -> bool:
        """Validate glTF data dictionary for EXT_bmesh_encoding."""
        # Reset logs
        self.errors = []
        self.warnings = []
        self.info = []

        # Check if extensions exist at root level
        if 'extensions' not in gltf_data:
            self.log_error("No 'extensions' object found at glTF root level")
            self.log_info("EXT_bmesh_encoding requires an extensions object")
            return False

        extensions = gltf_data['extensions']
        self.log_info(f"Found extensions object with keys: {list(extensions.keys())}")

        # Check for EXT_bmesh_encoding
        if 'EXT_bmesh_encoding' not in extensions:
            self.log_error("EXT_bmesh_encoding extension not found in glTF")
            self.log_info("Available extensions: " + ", ".join(extensions.keys()))
            return False

        self.log_success("EXT_bmesh_encoding extension found!")

        # Validate extension structure
        ext_data = extensions['EXT_bmesh_encoding']
        return self.validate_extension_structure(ext_data)

    def validate_extension_structure(self, ext_data: Any) -> bool:
        """Validate the structure of EXT_bmesh_encoding extension data."""
        if not isinstance(ext_data, dict):
            self.log_error(f"EXT_bmesh_encoding should be a dictionary, got {type(ext_data)}")
            return False

        self.log_info(f"Extension data keys: {list(ext_data.keys())}")

        # Check for required BMesh components
        required_components = ['vertices', 'edges', 'loops', 'faces']
        found_components = []

        for component in required_components:
            if component in ext_data:
                found_components.append(component)
                self.validate_component_structure(ext_data[component], component)
            else:
                self.log_warning(f"Missing required component: {component}")

        if not found_components:
            self.log_error("No BMesh components found in extension data")
            return False

        self.log_success(f"Found BMesh components: {', '.join(found_components)}")
        return len(self.errors) == 0

    def validate_component_structure(self, component_data: Any, component_name: str):
        """Validate the structure of a BMesh component."""
        if not isinstance(component_data, dict):
            self.log_error(f"{component_name} should be a dictionary, got {type(component_data)}")
            return

        self.log_info(f"{component_name} has keys: {list(component_data.keys())}")

        # Check for attributes in vertices
        if component_name == 'vertices' and 'attributes' in component_data:
            attrs = component_data['attributes']
            if isinstance(attrs, dict):
                self.log_info(f"vertices.attributes has keys: {list(attrs.keys())}")
            else:
                self.log_warning(f"vertices.attributes should be a dict, got {type(attrs)}")


def test_encoder_directly():
    """Test the BMesh encoder directly to see if it generates data."""
    print("\n🔧 Testing BMesh Encoder Directly")
    print("=" * 40)

    try:
        # Try to import the encoder
        sys.path.insert(0, os.path.dirname(__file__))
        from ext_bmesh_encoding.encoding import BmeshEncoder

        encoder = BmeshEncoder()
        print("✅ BMeshEncoder imported successfully")

        # Test with mock data (since we don't have Blender objects)
        print("ℹ️  Note: Cannot test encoder with real Blender objects outside Blender")
        print("   This test would need to run within Blender environment")

        return True

    except ImportError as e:
        print(f"❌ Failed to import BmeshEncoder: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing encoder: {e}")
        return False


def diagnose_export_process():
    """Diagnose potential issues with the export process."""
    print("\n🔍 Diagnosing Export Process")
    print("=" * 30)

    issues = []

    # Get the correct directory (where this test file is located)
    test_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if addon files exist
    addon_files = ['__init__.py', 'addon.py', 'gltf_extension.py']
    for file in addon_files:
        file_path = os.path.join(test_dir, file)
        if os.path.exists(file_path):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            issues.append(f"Missing file: {file}")

    # Check if extension classes are properly exposed
    try:
        # Add the test directory to Python path
        if test_dir not in sys.path:
            sys.path.insert(0, test_dir)

        import ext_bmesh_encoding.gltf_extension as gltf_ext

        has_import_ext = hasattr(gltf_ext, 'glTF2ImportUserExtension')
        has_export_ext = hasattr(gltf_ext, 'glTF2ExportUserExtension')

        print(f"glTF2ImportUserExtension: {'✅' if has_import_ext else '❌'}")
        print(f"glTF2ExportUserExtension: {'✅' if has_export_ext else '❌'}")

        if not has_export_ext:
            issues.append("glTF2ExportUserExtension not found - export hook won't work")
        if not has_import_ext:
            issues.append("glTF2ImportUserExtension not found - import hook won't work")

    except ImportError as e:
        if 'bpy' in str(e):
            print("⚠️ Cannot import gltf_extension - bpy not available (expected outside Blender)")
            print("   This is normal when running outside Blender environment")
        else:
            print(f"❌ Cannot import gltf_extension: {e}")
            issues.append(f"Import error: {e}")
    except Exception as e:
        print(f"❌ Error checking extension classes: {e}")
        issues.append(f"Extension check error: {e}")

    if issues:
        print("\n🚨 Issues found:")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("\n✅ No obvious issues found with addon structure")

    return issues


def main():
    """Main test function."""
    print("EXT_bmesh_encoding glTF Validation Test")
    print("=" * 50)

    # Test encoder import
    encoder_ok = test_encoder_directly()

    # Diagnose export process
    issues = diagnose_export_process()

    # Check for glTF files in the test directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    gltf_files = []
    for file in os.listdir(test_dir):
        if file.endswith('.gltf') or file.endswith('.glb'):
            gltf_files.append(file)
            # Use full path for validation
            gltf_files[-1] = os.path.join(test_dir, file)

    if gltf_files:
        print(f"\n📁 Found glTF files: {gltf_files}")
        for gltf_file in gltf_files:
            validator = GLTFExtensionValidator()
            is_valid = validator.validate_gltf_file(gltf_file)

            if is_valid:
                print(f"🎉 {gltf_file} contains valid EXT_bmesh_encoding data!")
            else:
                print(f"❌ {gltf_file} is missing or has invalid EXT_bmesh_encoding data")
                if validator.errors:
                    print("Errors:")
                    for error in validator.errors:
                        print(f"  • {error}")
    else:
        print("\n📁 No glTF files found in current directory")
        print("💡 To test EXT_bmesh_encoding export:")
        print("   1. Export a mesh from Blender with EXT_bmesh_encoding enabled")
        print("   2. Run this test script in the same directory")
        print("   3. The test will validate the exported glTF file")

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Encoder import: {'✅ PASS' if encoder_ok else '❌ FAIL'}")
    print(f"Addon structure: {'✅ PASS' if not issues else '❌ FAIL'}")
    print(f"glTF files found: {len(gltf_files)}")

    if issues:
        print("\n🚨 Critical Issues:")
        for issue in issues:
            print(f"  • {issue}")

        print("\n🔧 Recommended fixes:")
        if "Missing file" in str(issues):
            print("  • Ensure all addon files are present")
        if "not found" in str(issues):
            print("  • Check that extension classes are properly exposed in gltf_extension.py")
        if "Import error" in str(issues):
            print("  • Fix import issues in the addon modules")

    success = encoder_ok and not issues
    print(f"\nOverall result: {'✅ PASS' if success else '❌ FAIL'}")
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
