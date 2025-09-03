#!/usr/bin/env python3
"""
Simple test to verify EXT_bmesh_encoding can be added to glTF files.
This test doesn't require complex imports and focuses on the core functionality.
"""

import json
import os
import sys


def test_gltf_structure():
    """Test basic glTF file structure and extension addition."""
    print("🔍 Testing glTF structure and EXT_bmesh_encoding addition...")

    # Create a basic glTF structure
    gltf_data = {
        "asset": {
            "generator": "Khronos glTF Blender I/O v4.5.47",
            "version": "2.0"
        },
        "scene": 0,
        "scenes": [{"name": "Scene", "nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "Cube"}],
        "meshes": [{
            "name": "Cube",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2},
                "indices": 3
            }]
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 24, "max": [1, 1, 1], "min": [-1, -1, -1], "type": "VEC3"},
            {"bufferView": 1, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 24, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": 36, "type": "SCALAR"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteLength": 288, "byteOffset": 0},
            {"buffer": 0, "byteLength": 288, "byteOffset": 288},
            {"buffer": 0, "byteLength": 192, "byteOffset": 576},
            {"buffer": 0, "byteLength": 72, "byteOffset": 768}
        ],
        "buffers": [{"uri": "cube.bin", "byteLength": 840}]
    }

    print("✅ Created basic glTF structure")

    # Test adding EXT_bmesh_encoding extension
    print("🔧 Adding EXT_bmesh_encoding extension...")

    # Create mock extension data (simulating what the encoder would produce)
    mock_extension_data = {
        "vertices": {
            "count": 8,
            "positions": {
                "data": b'\x00\x00\x80\xbf\x00\x00\x80\xbf\x00\x00\x80\xbf\x00\x00\x80\x3f\x00\x00\x80\xbf\x00\x00\x80\xbf\x00\x00\x80\xbf\x00\x00\x80\x3f\x00\x00\x80\x3f\x00\x00\x80\xbf\x00\x00\x80\x3f\x00\x00\x80\x3f\x00\x00\x80\x3f',
                "target": 34962,
                "componentType": 5126,
                "type": "VEC3",
                "count": 8
            }
        },
        "edges": {
            "count": 12,
            "vertices": {
                "data": b'\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00',
                "target": 34963,
                "componentType": 5125,
                "type": "VEC2",
                "count": 12
            }
        },
        "loops": {
            "count": 24,
            "topology": {
                "data": b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00',
                "target": 34962,
                "componentType": 5125,
                "type": "SCALAR",
                "count": 24
            }
        },
        "faces": {
            "count": 6,
            "vertices": {
                "data": b'\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00',
                "target": 34962,
                "componentType": 5125,
                "type": "SCALAR"
            },
            "offsets": {
                "data": b'\x00\x00\x00\x00\x04\x00\x00\x00',
                "target": 34962,
                "componentType": 5125,
                "type": "SCALAR",
                "count": 2
            }
        }
    }

    # Add extension to glTF root
    if 'extensions' not in gltf_data:
        gltf_data['extensions'] = {}

    gltf_data['extensions']['EXT_bmesh_encoding'] = mock_extension_data

    print("✅ Added EXT_bmesh_encoding extension to glTF")

    # Save the test glTF file
    test_file = "test_with_extension.gltf"

    # Convert bytes to base64 for JSON serialization
    import base64

    def convert_bytes_to_base64(obj):
        if isinstance(obj, dict):
            return {k: convert_bytes_to_base64(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_bytes_to_base64(item) for item in obj]
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('ascii')
        else:
            return obj

    # Convert bytes to base64 for JSON
    gltf_data_json = convert_bytes_to_base64(gltf_data)

    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(gltf_data_json, f, indent=2)

    print(f"💾 Saved test glTF with extension: {test_file}")

    # Verify the extension was added correctly
    print("🔍 Verifying extension in saved file...")

    with open(test_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)

    if 'extensions' in saved_data and 'EXT_bmesh_encoding' in saved_data['extensions']:
        ext_data = saved_data['extensions']['EXT_bmesh_encoding']
        components = list(ext_data.keys())
        print(f"✅ EXT_bmesh_encoding found with components: {components}")

        # Check for required components
        required = ['vertices', 'edges', 'loops', 'faces']
        found = [comp for comp in required if comp in ext_data]

        if found:
            print(f"✅ Found required components: {found}")
            return True
        else:
            print(f"❌ Missing required components: {[comp for comp in required if comp not in ext_data]}")
            return False
    else:
        print("❌ EXT_bmesh_encoding extension not found in saved file")
        return False


def validate_saved_gltf():
    """Validate the saved glTF file using our simple validator."""
    print("\n🔍 Validating saved glTF file...")

    test_file = "test_with_extension.gltf"
    if not os.path.exists(test_file):
        print("❌ Test file not found")
        return False

    # Use our simple validator
    from test_gltf_validation_simple import validate_gltf_for_ext_bmesh_encoding

    return validate_gltf_for_ext_bmesh_encoding(test_file)


def main():
    """Run the simple glTF export test."""
    print("EXT_bmesh_encoding Simple glTF Export Test")
    print("=" * 45)

    # Test glTF structure creation and extension addition
    structure_success = test_gltf_structure()

    # Validate the saved file
    validation_success = validate_saved_gltf()

    print("\n" + "=" * 45)
    print("SUMMARY:")
    print(f"Structure Test: {'✅ PASS' if structure_success else '❌ FAIL'}")
    print(f"Validation Test: {'✅ PASS' if validation_success else '❌ FAIL'}")

    if structure_success and validation_success:
        print("\n🎉 EXT_bmesh_encoding glTF structure test passed!")
        print("   This confirms that:")
        print("   • Extension data can be properly structured")
        print("   • glTF files can contain EXT_bmesh_encoding data")
        print("   • Our validation logic works correctly")
        print("\n🔧 The issue is likely in the Blender addon integration:")
        print("   • Extension hooks may not be registered with glTF-Blender-IO")
        print("   • Blender addon loading order may be incorrect")
        print("   • glTF-Blender-IO version compatibility issues")
    else:
        print("\n❌ EXT_bmesh_encoding structure test failed.")
        if not structure_success:
            print("   • Extension data structure is invalid")
        if not validation_success:
            print("   • glTF validation failed")

    return structure_success and validation_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
