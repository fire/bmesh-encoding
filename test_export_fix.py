#!/usr/bin/env python3
"""
Test script to verify the EXT_bmesh_encoding export fix.
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_extension_data_addition():
    """Test that extension data is properly added to glTF objects."""
    print("🧪 Testing EXT_bmesh_encoding export fix")
    print("=" * 50)

    try:
        # Import the extension classes
        from gltf_extension import glTF2ExportUserExtension

        # Create a mock extension instance
        extension = glTF2ExportUserExtension()

        # Mock Blender object with native mesh data
        class MockBlenderObject:
            def __init__(self):
                self.name = "TestMesh"
                self.type = 'MESH'
                self.data = MockMeshData()

        class MockMeshData:
            def __init__(self):
                self.name = "TestMesh"
                self.vertices = [
                    MockVertex(0, (0.0, 0.0, 0.0)),
                    MockVertex(1, (1.0, 0.0, 0.0)),
                    MockVertex(2, (1.0, 1.0, 0.0)),
                    MockVertex(3, (0.0, 1.0, 0.0)),
                ]
                self.edges = [
                    MockEdge(0, (0, 1)),
                    MockEdge(1, (1, 2)),
                    MockEdge(2, (2, 3)),
                    MockEdge(3, (3, 0)),
                ]
                self.polygons = [
                    MockPolygon(0, [0, 1, 2, 3], 0),  # quad
                ]
                self.loops = [
                    MockLoop(0, 0, 0, 0),  # vertex 0, edge 0, face 0
                    MockLoop(1, 1, 0, 1),  # vertex 1, edge 1, face 0
                    MockLoop(2, 2, 0, 2),  # vertex 2, edge 2, face 0
                    MockLoop(3, 3, 0, 3),  # vertex 3, edge 3, face 0
                ]

        class MockVertex:
            def __init__(self, index, co):
                self.index = index
                self.co = co
                self.normal = (0.0, 0.0, 1.0)

        class MockEdge:
            def __init__(self, index, vertices):
                self.index = index
                self.vertices = vertices
                self.use_edge_sharp = False

        class MockPolygon:
            def __init__(self, index, vertices, loop_start):
                self.index = index
                self.vertices = vertices
                self.loop_start = loop_start
                self.loop_total = len(vertices)
                self.normal = (0.0, 0.0, 1.0)
                self.use_smooth = True

        class MockLoop:
            def __init__(self, index, vertex_index, edge_index, face_index):
                self.index = index
                self.vertex_index = vertex_index
                self.edge_index = edge_index

        # Mock glTF exporter
        class MockGLTFExporter:
            def __init__(self):
                self.gltf = MockGLTFObject()

        class MockGLTFObject:
            def __init__(self):
                self.extensions = {}

        # Mock the encoder to return test data
        class MockEncoder:
            def encode_object(self, obj):
                return {
                    "vertices": {"count": 4, "positions": {"data": b"test", "target": 34962}},
                    "edges": {"count": 4, "vertices": {"data": b"test", "target": 34963}},
                    "loops": {"count": 4, "topology": {"data": b"test", "target": 34962}},
                    "faces": {"count": 1, "vertices": {"data": b"test", "target": 34962}}
                }
        extension.encoder = MockEncoder()

        # Test the extension processing
        blender_obj = MockBlenderObject()
        gltf2_object = 0  # Integer index (the problematic case)
        export_settings = None
        gltf2_exporter = MockGLTFExporter()

        print("📤 Testing extension hook with integer gltf2_object...")
        result = extension.gather_gltf_hook(
            gltf2_object, blender_obj, export_settings, gltf2_exporter
        )

        print(f"📋 Extension hook result: {result}")

        # Check if extension was added to glTF root
        if hasattr(gltf2_exporter.gltf, 'extensions') and 'EXT_bmesh_encoding' in gltf2_exporter.gltf.extensions:
            print("✅ EXT_bmesh_encoding successfully added to glTF root!")
            ext_data = gltf2_exporter.gltf.extensions['EXT_bmesh_encoding']
            print(f"   Extension data keys: {list(ext_data.keys()) if isinstance(ext_data, dict) else 'N/A'}")
            return True
        else:
            print("❌ EXT_bmesh_encoding not found in glTF root")
            print(f"   Available extensions: {list(gltf2_exporter.gltf.extensions.keys()) if hasattr(gltf2_exporter.gltf, 'extensions') else 'None'}")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    success = test_extension_data_addition()

    print("\n" + "=" * 50)
    if success:
        print("🎉 Export fix test PASSED!")
        print("   EXT_bmesh_encoding extension data is being added correctly")
    else:
        print("❌ Export fix test FAILED!")
        print("   Extension data is not being added to glTF files")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
