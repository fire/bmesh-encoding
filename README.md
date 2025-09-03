# EXT_bmesh_encoding - Standalone Blender Addon

A standalone Blender addon that provides glTF export with EXT_bmesh_encoding extension support for preserving BMesh topology information.

## Overview

This addon extracts the EXT_bmesh_encoding functionality from the VRM-Addon-for-Blender and makes it available as an independent addon. The EXT_bmesh_encoding extension preserves BMesh topology data during glTF export, allowing for accurate reconstruction of mesh connectivity and edge flow in supporting applications.

## Features

- **BMesh Topology Preservation**: Maintains vertex adjacency, edge connectivity, and face relationships
- **UV Coordinate Support**: Preserves UV mapping information for texture coordinates
- **Manifold Information**: Optionally includes manifold status for edges
- **Buffer-Based Storage**: Efficient binary storage in glTF buffers
- **glTF 2.0 Compatible**: Fully compliant with glTF 2.0 specification
- **Standalone Operation**: Works independently of VRM addon

## Installation

1. Download or clone the VRM-Addon-for-Blender repository
2. Copy the `src/ext_bmesh_encoding/` directory to your Blender addons folder
3. Enable the addon in Blender's preferences

## Usage

### Basic Export

1. Open Blender with your mesh scene
2. Go to `File > Export > glTF 2.0 with EXT_bmesh_encoding`
3. Choose your export options:
   - **Format**: glTF Binary (.glb) recommended
   - **Selected Objects**: Export selected objects only
   - **Apply Transform**: Apply object transforms to mesh data
   - **EXT_bmesh_encoding**: Enable the extension (enabled by default)

### Export Options

- **Format**: Choose between glTF Separate, Embedded, or Binary
- **Selected Objects**: Export only selected objects
- **Apply Transform**: Apply object transformations to mesh data
- **Y Up**: Use +Y up coordinate system
- **EXT_bmesh_encoding**: Include BMesh topology extension

## Technical Details

### Extension Structure

The EXT_bmesh_encoding extension adds the following data to glTF meshes:

```json
{
  "meshes": [
    {
      "primitives": [
        {
          "extensions": {
            "EXT_bmesh_encoding": {
              "vertices": {
                "count": 8,
                "positions": {"data": "...", "target": 34962, "componentType": 5126, "type": "VEC3", "count": 8},
                "attributes": {
                  "NORMAL": {"data": "...", "target": 34962, "componentType": 5126, "type": "VEC3", "count": 8}
                }
              },
              "edges": {
                "count": 12,
                "vertices": {"data": "...", "target": 34963, "componentType": 5125, "type": "VEC2", "count": 12},
                "attributes": {
                  "_SMOOTH": {"data": "...", "target": 34962, "componentType": 5121, "type": "SCALAR", "count": 12}
                }
              },
              "loops": {
                "count": 24,
                "topology": {"data": "...", "target": 34962, "componentType": 5125, "type": "SCALAR", "count": 168},
                "attributes": {
                  "TEXCOORD_0": {"data": "...", "target": 34962, "componentType": 5126, "type": "VEC2", "count": 24}
                }
              },
              "faces": {
                "count": 6,
                "vertices": {"data": "...", "target": 34962, "componentType": 5125, "type": "SCALAR"},
                "offsets": {"data": "...", "target": 34962, "componentType": 5125, "type": "SCALAR", "count": 7},
                "normals": {"data": "...", "target": 34962, "componentType": 5126, "type": "VEC3", "count": 6},
                "smooth": {"data": "...", "target": 34962, "componentType": 5121, "type": "SCALAR", "count": 6}
              }
            }
          }
        }
      ]
    }
  ]
}
```

### Data Components

- **Vertices**: Position and normal data with adjacency information
- **Edges**: Vertex pairs, face adjacency, and smooth flags
- **Loops**: Topology navigation (vertex, edge, face, next, prev, radial)
- **Faces**: Variable-length vertex lists with offsets and face normals

## API Reference

### BmeshEncoder Class

```python
from ext_bmesh_encoding.encoding import BmeshEncoder

encoder = BmeshEncoder()

# Encode using BMesh (recommended for complex topology)
extension_data = encoder.encode_object(mesh_object)

# Encode using native mesh API (more stable)
extension_data = encoder.encode_object_native(mesh_object)
```

### Export Operator

```python
# Programmatic export
bpy.ops.export_scene.gltf_ext_bmesh_encoding(
    filepath="/path/to/output.glb",
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_y_up=True,
    export_ext_bmesh_encoding=True
)
```

## Compatibility

- **Blender**: 3.6.0+
- **glTF**: 2.0
- **Python**: 3.10+
- **Operating Systems**: Windows, macOS, Linux

## Development

### Project Structure

```
src/ext_bmesh_encoding/
├── __init__.py              # Main addon file
├── blender_manifest.toml    # Blender 4.2+ manifest
├── encoding.py              # Core encoding logic
├── exporter.py              # Export operators and UI
├── logger.py                # Logging utilities
├── ui.py                    # UI panels and menus
├── pyproject.toml           # Python project configuration
├── README.md                # This file
└── tests/                   # Test suite
    ├── __init__.py
    └── test_encoding.py
```

### Running Tests

```bash
cd src/ext_bmesh_encoding
python -m pytest tests/
```

### Building

```bash
cd src/ext_bmesh_encoding
uv build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Related Projects

- [VRM-Addon-for-Blender](https://github.com/vrm-c/VRM-Addon-for-Blender) - Original VRM addon
- [EXT_bmesh_encoding Specification](https://github.com/vrm-c/vrm-specification/tree/master/specification/0.0/schema/extensions/EXT_bmesh_encoding) - Extension specification
- [glTF 2.0 Specification](https://www.khronos.org/gltf/) - glTF standard
