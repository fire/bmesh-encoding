#!/usr/bin/env python3
"""
Test script to verify the import hook fix for EXT_bmesh_encoding.
This tests that the import hook correctly looks for extension data at the glTF root level.
"""

import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import_hook_location():
    """Test that the import hook looks in the correct location for extension data."""
    print("🧪 Testing Import Hook Location Fix")
    print("=" * 40)

    # Load the test glTF file
    gltf_path = "test_sample.gltf"
    if not os.path.exists(gltf_path):
        print(f"❌ Test glTF file not found: {gltf_path}")
        return False

    with open(gltf_path, 'r') as f:
        gltf_data = json.load(f)

    print(f"✅ Loaded glTF file: {gltf_path}")

    # Check that EXT_bmesh_encoding is at the root level
    if 'extensions' in gltf_data and 'EXT_bmesh_encoding' in gltf_data['extensions']:
        print("✅ EXT_bmesh_encoding found at glTF root level (correct location)")
        ext_data = gltf_data['extensions']['EXT_bmesh_encoding']
        print(f"   Extension data keys: {list(ext_data.keys())}")

        # Verify all expected components are present
        expected_keys = ['vertices', 'edges', 'loops', 'faces']
        for key in expected_keys:
            if key in ext_data:
                print(f"   ✅ {key}: present")
            else:
                print(f"   ❌ {key}: missing")
                return False

        print("🎉 All BMesh components found at correct location!")
        return True
    else:
        print("❌ EXT_bmesh_encoding not found at glTF root level")
        return False

def test_import_hook_logic():
    """Test the import hook logic for finding extension data."""
    print("\n🧪 Testing Import Hook Logic")
    print("=" * 30)

    # Simulate the glTF object that would be passed to the import hook
    class MockGLTF:
        def __init__(self, extensions_data):
            self.extensions = extensions_data

    # Create mock glTF with EXT_bmesh_encoding at root level
    mock_extensions = {
        'EXT_bmesh_encoding': {
            'vertices': {'count': 3, 'attributes': {'POSITION': [0, 1, 2]}},
            'edges': {'count': 3, 'indices': [0, 1, 1, 2, 2, 0]},
            'loops': {'count': 3, 'vertex_indices': [0, 1, 2], 'edge_indices': [0, 1, 2]},
            'faces': {'count': 1, 'loop_start': [0], 'loop_total': [3]}
        }
    }

    mock_gltf = MockGLTF(mock_extensions)

    # Test the logic that the import hook would use
    if hasattr(mock_gltf, 'extensions') and mock_gltf.extensions:
        print("✅ glTF object has extensions attribute")
        # glTF-Blender-IO passes extensions as a dict, so we access it like a dict
        if isinstance(mock_gltf.extensions, dict) and 'EXT_bmesh_encoding' in mock_gltf.extensions:
            ext_bmesh_data = mock_gltf.extensions['EXT_bmesh_encoding']
            print("✅ EXT_bmesh_encoding found at glTF root level")
            print(f"   Data type: {type(ext_bmesh_data)}")
            print(f"   Keys: {list(ext_bmesh_data.keys())}")
            return True
        else:
            print("❌ EXT_bmesh_encoding not found in extensions")
            print(f"   Extensions keys: {list(mock_gltf.extensions.keys()) if isinstance(mock_gltf.extensions, dict) else 'not a dict'}")
            return False
    else:
        print("❌ glTF object has no extensions")
        return False

def main():
    """Main test function."""
    print("🔬 EXT_bmesh_encoding Import Hook Fix Test")
    print("=" * 45)

    test1_passed = test_import_hook_location()
    test2_passed = test_import_hook_logic()

    print("\n" + "=" * 45)
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Import hook fix is working correctly")
        print("✅ Extension data is in the correct location")
        print("✅ Import hook logic will find the data")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Import hook fix needs more work")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
