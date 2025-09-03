# SPDX-License-Identifier: MIT
"""
EXT_bmesh_encoding - Standalone Blender addon for glTF EXT_bmesh_encoding extension.

This addon provides independent support for the EXT_bmesh_encoding glTF extension,
allowing preservation of BMesh topology information during glTF export.
"""

import bpy
from bpy.props import BoolProperty
from bpy.types import AddonPreferences

from .logger import get_logger
from .gltf_extension import glTF2ImportUserExtension, glTF2ExportUserExtension

logger = get_logger(__name__)

# Expose extension classes as module attributes for glTF-Blender-IO discovery
# glTF-Blender-IO looks for these specific attribute names on enabled addons
# These must be assigned to the module so hasattr(module, 'glTF2ImportUserExtension') works
import sys
current_module = sys.modules[__name__]
current_module.glTF2ImportUserExtension = glTF2ImportUserExtension
current_module.glTF2ExportUserExtension = glTF2ExportUserExtension


bl_info = {
    "name": "EXT_bmesh_encoding",
    "author": "VRM Consortium",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "File > Export > glTF 2.0 with EXT_bmesh_encoding",
    "description": "Export glTF files with EXT_bmesh_encoding extension for BMesh topology preservation",
    "warning": "",
    "doc_url": "https://github.com/fire/bmesh-encoding/tree/main/thirdparty/EXT_bmesh_encoding",
    "support": "COMMUNITY",
    "category": "Import-Export",
    "tracker_url": "https://github.com/fire/bmesh-encoding.git/issues",
}


class EXTBMeshEncodingPreferences(AddonPreferences):
    """Preferences for EXT_bmesh_encoding addon."""

    bl_idname = __name__

    # Export preferences
    enable_debug_logging: BoolProperty(
        name="Enable Debug Logging",
        description="Enable detailed logging for debugging EXT_bmesh_encoding operations",
        default=False,
    )

    preserve_manifold_info: BoolProperty(
        name="Preserve Manifold Information",
        description="Include manifold status information in the extension data",
        default=True,
    )

    def draw(self, context):
        """Draw the preferences UI."""
        layout = self.layout

        box = layout.box()
        box.label(text="Debug Options:")
        box.prop(self, "enable_debug_logging")

        box = layout.box()
        box.label(text="Extension Options:")
        box.prop(self, "preserve_manifold_info")


def register():
    """Register the addon."""
    try:
        logger.info("Registering EXT_bmesh_encoding addon...")

        # Register preferences first
        bpy.utils.register_class(EXTBMeshEncodingPreferences)
        logger.debug("Preferences class registered")

        # Import and register glTF extension classes for auto-discovery
        from . import gltf_extension
        from .gltf_extension import glTF2ImportUserExtension, glTF2ExportUserExtension

        logger.info("EXT_bmesh_encoding addon registered successfully")
        logger.info("glTF extension hooks will be auto-discovered by glTF-Blender-IO")

    except Exception as e:
        logger.error(f"Failed to register EXT_bmesh_encoding addon: {e}")
        # Don't re-raise - allow Blender to continue loading other addons


def unregister():
    """Unregister the addon."""
    try:
        logger.info("Unregistering EXT_bmesh_encoding addon...")

        # Unregister preferences
        bpy.utils.unregister_class(EXTBMeshEncodingPreferences)
        logger.debug("Preferences class unregistered")

        logger.info("EXT_bmesh_encoding addon unregistered successfully")

    except Exception as e:
        logger.error(f"Failed to unregister EXT_bmesh_encoding addon: {e}")
        # Don't re-raise - allow Blender to continue unloading other addons


if __name__ == "__main__":
    register()
