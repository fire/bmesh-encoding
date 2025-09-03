#!/usr/bin/env python3
"""
Simple test to validate EXT_bmesh_encoding in glTF files without module imports.
"""

import json
import os


def validate_gltf_for_ext_bmesh_encoding(gltf_path):
    """Simple validation of glTF file for EXT_bmesh_encoding."""
    print(f"🔍 Validating: {gltf_path}")

    try:
        with open(gltf_path, 'r', encoding='utf-8') as f:
            gltf_data = json.load(f)

        # Check if extensions exist
        if 'extensions' not in gltf_data:
            print("❌ No 'extensions' object found at glTF root level")
            print("   EXT_bmesh_encoding requires an extensions object")
            return False

        extensions = gltf_data['extensions']
        print(f"ℹ️  Found extensions: {list(extensions.keys())}")

        # Check for EXT_bmesh_encoding
        if 'EXT_bmesh_encoding' not in extensions:
            print("❌ EXT_bmesh_encoding extension not found in glTF")
            print(f"   Available extensions: {list(extensions.keys())}")
            return False

        print("✅ EXT_bmesh_encoding extension found!")

        # Validate extension structure
        ext_data = extensions['EXT_bmesh_encoding']
        if not isinstance(ext_data, dict):
            print(f"❌ EXT_bmesh_encoding should be a dictionary, got {type(ext_data)}")
            return False

        print(f"ℹ️  Extension data keys: {list(ext_data.keys())}")

        # Check for required BMesh components
        required = ['vertices', 'edges', 'loops', 'faces']
        found = [comp for comp in required if comp in ext_data]

        if not found:
            print("❌ No BMesh components found in extension data")
            return False

        print(f"✅ Found BMesh components: {', '.join(found)}")

        # Check for missing components
        missing = [comp for comp in required if comp not in ext_data]
        if missing:
            print(f"⚠️  Missing components: {', '.join(missing)}")

        return True

    except Exception as e:
        print(f"❌ Error validating glTF file: {e}")
        return False


def main():
    """Main test function."""
    print("EXT_bmesh_encoding glTF Validation (Simple)")
    print("=" * 45)

    # Find glTF files in current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    gltf_files = []

    for file in os.listdir(current_dir):
        if file.endswith('.gltf') or file.endswith('.glb'):
            gltf_files.append(os.path.join(current_dir, file))

    if not gltf_files:
        print("❌ No glTF files found in current directory")
        print("💡 Place a glTF file in this directory to test EXT_bmesh_encoding validation")
        return False

    print(f"📁 Found {len(gltf_files)} glTF file(s)")

    all_valid = True
    for gltf_file in gltf_files:
        print(f"\n🔍 Checking: {os.path.basename(gltf_file)}")
        print("-" * 40)

        is_valid = validate_gltf_for_ext_bmesh_encoding(gltf_file)
        if not is_valid:
            all_valid = False

    print(f"\n{'='*45}")
    if all_valid:
        print("🎉 All glTF files contain valid EXT_bmesh_encoding data!")
    else:
        print("❌ Some glTF files are missing EXT_bmesh_encoding data")
        print("\n🔧 This indicates that:")
        print("   • EXT_bmesh_encoding extension hooks are not being triggered")
        print("   • The addon is not properly integrated with glTF-Blender-IO")
        print("   • Extension data is not being added during export")

    return all_valid


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
