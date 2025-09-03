# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""UI components for EXT_bmesh_encoding addon."""

import bpy
from bpy.types import Panel, Menu


class EXTBMeshEncoding_PT_MainPanel(Panel):
    """Main panel for EXT_bmesh_encoding in the 3D View."""

    bl_label = "EXT_bmesh_encoding"
    bl_idname = "EXT_BMESH_ENCODING_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EXT_bmesh_encoding"

    def draw(self, context):
        """Draw the main panel."""
        layout = self.layout

        # Header
        box = layout.box()
        box.label(text="EXT_bmesh_encoding", icon='MESH_DATA')

        # Export section
        col = layout.column(align=True)
        col.label(text="Export:")
        col.operator("export_scene.gltf_ext_bmesh_encoding", text="Export glTF with EXT_bmesh_encoding", icon='EXPORT')

        # Information section
        box = layout.box()
        box.label(text="Information:")
        col = box.column(align=True)
        col.label(text="• Preserves BMesh topology")
        col.label(text="• Maintains edge flow")
        col.label(text="• Supports UV coordinates")
        col.label(text="• Compatible with glTF 2.0")


class EXTBMeshEncoding_MT_ExportMenu(Menu):
    """Export menu for EXT_bmesh_encoding."""

    bl_label = "EXT_bmesh_encoding Export"
    bl_idname = "EXT_BMESH_ENCODING_MT_export"

    def draw(self, context):
        """Draw the export menu."""
        layout = self.layout

        layout.operator("export_scene.gltf_ext_bmesh_encoding", text="glTF 2.0 (.gltf)", icon='FILE')
        layout.operator("export_scene.gltf_ext_bmesh_encoding", text="glTF Binary (.glb)", icon='FILE')


def menu_func_view3d(self, context):
    """Add to 3D View menu."""
    self.layout.menu(EXTBMeshEncoding_MT_ExportMenu.bl_idname)


def register():
    """Register UI components."""
    bpy.utils.register_class(EXTBMeshEncoding_PT_MainPanel)
    bpy.utils.register_class(EXTBMeshEncoding_MT_ExportMenu)

    # Add to menus
    bpy.types.VIEW3D_MT_object.append(menu_func_view3d)


def unregister():
    """Unregister UI components."""
    # Remove from menus
    bpy.types.VIEW3D_MT_object.remove(menu_func_view3d)

    bpy.utils.unregister_class(EXTBMeshEncoding_MT_ExportMenu)
    bpy.utils.unregister_class(EXTBMeshEncoding_PT_MainPanel)
