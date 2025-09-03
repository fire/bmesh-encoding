# EXT_bmesh_encoding Blender Addon

Preserves mesh topology during glTF export/import operations by implementing the EXT_bmesh_encoding glTF extension.

## Features

- ✅ Preserve quad faces during glTF roundtrip
- ✅ Maintain ngon topology
- ✅ Support for complex mesh structures
- ✅ Compatible with VRM 0.x and 1.x formats
- ✅ Automatic integration with glTF-Blender-IO

## Installation

### Method 1: Install as Blender Addon (Recommended)

1. **Download the addon files:**

   ```bash
   git clone https://github.com/fire/bmesh-encoding.git
   cd bmesh-encoding
   ```

2. **Install in Blender:**

   - Open Blender 4.0 or later
   - Go to `Edit > Preferences > Add-ons`
   - Click `Install...`
   - Navigate to the cloned repository folder
   - Select the `blender_manifest.toml` file
   - Click `Install Add-on`

3. **Enable the addon:**
   - In the Add-ons preferences, search for "EXT_bmesh_encoding"
   - Check the checkbox to enable the addon
   - The addon should now be active

### Method 2: Manual Installation

1. **Copy files to Blender addons directory:**

   ```bash
   # On Linux/Mac
   cp -r /path/to/ext_bmesh_encoding ~/.config/blender/4.0/scripts/addons/

   # On Windows
   copy "C:\path\to\ext_bmesh_encoding" "%APPDATA%\Blender Foundation\Blender\4.0\scripts\addons\"
   ```

2. **Enable in Blender:**
   - Open Blender
   - Go to `Edit > Preferences > Add-ons`
   - Search for "EXT_bmesh_encoding"
   - Enable the addon

## Usage

### Exporting with EXT_bmesh_encoding

1. Create or load a mesh with quads/ngons in Blender
2. Go to `File > Export > glTF 2.0 (.gltf/.glb)`
3. In the export settings, ensure EXT_bmesh_encoding is enabled (it should be automatic)
4. Export your glTF file
5. Check the Blender console for confirmation messages

### Importing glTF files with EXT_bmesh_encoding

1. Go to `File > Import > glTF 2.0 (.gltf/.glb)`
2. Select your glTF file that contains EXT_bmesh_encoding data
3. The addon will automatically detect and preserve the original mesh topology
4. Check the Blender console for processing messages

## Testing the Installation

You can test if the addon is working correctly by running the included diagnostic script:

1. Open Blender's Python console (`Scripting` workspace > Python Console)
2. Run the diagnostic script:
   ```python
   import sys
   sys.path.append('/path/to/ext_bmesh_encoding')
   import test_blender_integration
   test_blender_integration.main()
   ```

## Troubleshooting

### Common Issues

**Addon not appearing in preferences:**

- Ensure you're using Blender 4.0 or later
- Check that all files were copied correctly
- Try restarting Blender after installation

**Extension not working during export/import:**

- Check Blender console for error messages
- Ensure the glTF-Blender-IO addon is enabled
- Verify that your mesh contains quads/ngons

**Python errors:**

- Make sure Blender's Python can access the bmesh module
- Check that all dependencies are available

### Debug Mode

To enable debug logging:

1. Open Blender's Python console
2. Run:
   ```python
   import logging
   logging.getLogger('ext_bmesh_encoding').setLevel(logging.DEBUG)
   ```

## Development

### Project Structure

```
ext_bmesh_encoding/
├── __init__.py              # Main addon file with bl_info
├── blender_manifest.toml    # Blender 4.0+ addon manifest
├── gltf_extension.py        # glTF extension hooks
├── encoding.py              # BMesh encoding logic
├── decoding.py              # BMesh decoding logic
├── ui.py                    # User interface components
├── logger.py                # Logging utilities
├── exporter.py              # Export utilities
├── importer.py              # Import utilities
└── tests/                   # Test suite
```

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Run specific test
pytest tests/test_bmesh_encoding_roundtrip.py
```

## Compatibility

- **Blender:** 4.0.0 and later
- **Python:** 3.10+ (as required by Blender)
- **glTF-Blender-IO:** Automatic integration
- **VRM:** Compatible with VRM 0.x and 1.x

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Support

- **Issues:** [GitHub Issues](https://github.com/fire/bmesh-encoding/issues)
- **Discussions:** [GitHub Discussions](https://github.com/fire/bmesh-encoding/discussions)
- **Documentation:** See the `docs/` directory for detailed documentation
