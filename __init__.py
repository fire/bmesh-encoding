# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""
EXT_bmesh_encoding - Standalone Blender addon for glTF EXT_bmesh_encoding extension.

This addon provides independent support for the EXT_bmesh_encoding glTF extension,
allowing preservation of BMesh topology information during glTF export.
"""

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import AddonPreferences, Operator, Panel

from . import exporter
from . import ui


bl_info = {
    "name": "EXT_bmesh_encoding",
    "author": "VRM Consortium",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "File > Export > glTF 2.0 with EXT_bmesh_encoding",
    "description": "Export glTF files with EXT_bmesh_encoding extension for BMesh topology preservation",
    "warning": "",
    "doc_url": "https://github.com/vrm-c/vrm-specification/tree/master/specification/0.0/schema/extensions/EXT_bmesh_encoding",
    "support": "COMMUNITY",
    "category": "Import-Export",
    "tracker_url": "https://github.com/vrm-c/VRM-Addon-for-Blender/issues",
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
    bpy.utils.register_class(EXTBMeshEncodingPreferences)
    exporter.register()
    ui.register()


def unregister():
    """Unregister the addon."""
    ui.unregister()
    exporter.unregister()
    bpy.utils.unregister_class(EXTBMeshEncodingPreferences)


if __name__ == "__main__":
    register()
