"""
EXT_bmesh_encoding Blender Addon
Preserves mesh topology during glTF export/import operations.
"""

import bpy
from . import gltf_extension


def register():
    """Register the addon."""
    try:
        gltf_extension.register()
        print("EXT_bmesh_encoding addon registered successfully")
    except Exception as e:
        print(f"Failed to register EXT_bmesh_encoding addon: {e}")


def unregister():
    """Unregister the addon."""
    try:
        gltf_extension.unregister()
        print("EXT_bmesh_encoding addon unregistered successfully")
    except Exception as e:
        print(f"Failed to unregister EXT_bmesh_encoding addon: {e}")


if __name__ == "__main__":
    register()
