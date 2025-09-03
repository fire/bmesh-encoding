"""
EXT_bmesh_encoding Blender Addon
Preserves mesh topology during glTF export/import operations.
"""

# Module version
__version__ = "1.1.0"

# Blender addon registration functions
# These are called by Blender when enabling/disabling the addon
def register():
    """Register the addon with Blender."""
    try:
        # Ensure the addon directory is in the Python path
        import sys
        import os
        addon_dir = os.path.dirname(__file__)
        if addon_dir not in sys.path:
            sys.path.insert(0, addon_dir)

        # Register properties first
        try:
            import gltf_extension
            gltf_extension.register_properties()
        except ImportError:
            # Fallback: register properties directly
            import bpy
            from bpy.props import BoolProperty
            bpy.types.Scene.enable_ext_bmesh_encoding = BoolProperty(
                name="EXT_bmesh_encoding",
                description="Enable EXT_bmesh_encoding extension for BMesh topology preservation during glTF export/import",
                default=True,
            )
            print("EXT_bmesh_encoding properties registered (fallback - gltf_extension not found)")

        # Register UI components
        try:
            import ui
            ui.register()
        except ImportError:
            print("UI components not available (ui module not found)")

        # The glTF extension classes are automatically discovered by glTF-Blender-IO
        # through the module-level attributes defined in gltf_extension.py
        print("EXT_bmesh_encoding addon registered successfully")
        print("glTF extension classes available for auto-discovery by glTF-Blender-IO")
    except Exception as e:
        print(f"Failed to register EXT_bmesh_encoding addon: {e}")
        # Final fallback: try to register properties directly
        try:
            import bpy
            from bpy.props import BoolProperty
            bpy.types.Scene.enable_ext_bmesh_encoding = BoolProperty(
                name="EXT_bmesh_encoding",
                description="Enable EXT_bmesh_encoding extension for BMesh topology preservation during glTF export/import",
                default=True,
            )
            print("EXT_bmesh_encoding properties registered (final fallback)")
        except Exception as e2:
            print(f"Failed to register properties: {e2}")


def unregister():
    """Unregister the addon from Blender."""
    try:
        # Unregister UI components
        try:
            import ui
            ui.unregister()
        except ImportError:
            print("UI components not available for unregister (ui module not found)")

        # Unregister properties last
        try:
            import gltf_extension
            gltf_extension.unregister_properties()
        except ImportError:
            # Fallback: unregister properties directly
            import bpy
            if hasattr(bpy.types.Scene, 'enable_ext_bmesh_encoding'):
                del bpy.types.Scene.enable_ext_bmesh_encoding
                print("EXT_bmesh_encoding properties unregistered (fallback - gltf_extension not found)")

        print("EXT_bmesh_encoding addon unregistered successfully")
    except Exception as e:
        print(f"Failed to unregister EXT_bmesh_encoding addon: {e}")
        # Final fallback: try to unregister properties directly
        try:
            import bpy
            if hasattr(bpy.types.Scene, 'enable_ext_bmesh_encoding'):
                del bpy.types.Scene.enable_ext_bmesh_encoding
                print("EXT_bmesh_encoding properties unregistered (final fallback)")
        except Exception as e2:
            print(f"Failed to unregister properties: {e2}")


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
