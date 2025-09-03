"""
EXT_bmesh_encoding Blender Addon
Preserves mesh topology during glTF export/import operations.
"""

import bpy
from . import gltf_extension, ui


def register():
    """Register the addon with Blender."""
    try:
        # Register properties first
        from . import gltf_extension
        gltf_extension.register_properties()

        # Register UI components
        ui.register()

        # The glTF extension classes are automatically discovered by glTF-Blender-IO
        # through the module-level attributes defined in gltf_extension.py
        print("EXT_bmesh_encoding addon registered successfully")
        print("glTF extension classes available for auto-discovery by glTF-Blender-IO")
    except Exception as e:
        print(f"Failed to register EXT_bmesh_encoding addon: {e}")
        import traceback
        traceback.print_exc()


def unregister():
    """Unregister the addon from Blender."""
    try:
        # Unregister UI components
        ui.unregister()

        # Unregister properties last
        from . import gltf_extension
        gltf_extension.unregister_properties()

        print("EXT_bmesh_encoding addon unregistered successfully")
    except Exception as e:
        print(f"Failed to unregister EXT_bmesh_encoding addon: {e}")
        import traceback
        traceback.print_exc()


# Blender addon info
bl_info = {
    "name": "EXT_bmesh_encoding",
    "author": "EXT_bmesh_encoding Team",
    "description": "Preserve mesh topology during glTF export/import",
    "blender": (4, 0, 0),
    "version": (1, 1, 0),
    "location": "File > Import/Export > glTF 2.0",
    "warning": "",
    "category": "Import-Export",
    "support": "COMMUNITY",
}


if __name__ == "__main__":
    register()
