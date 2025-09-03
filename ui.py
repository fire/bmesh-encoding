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
        scene = context.scene

        # Header
        box = layout.box()
        box.label(text="EXT_bmesh_encoding", icon='MESH_DATA')

        # Settings section
        box = layout.box()
        box.label(text="Settings:")
        col = box.column(align=True)

        # Extension enable/disable
        row = col.row()
        row.prop(scene, "enable_ext_bmesh_encoding", text="Enable EXT_bmesh_encoding")

        # Additional settings (if available)
        if hasattr(scene, 'enable_ext_bmesh_encoding') and scene.enable_ext_bmesh_encoding:
            # Show additional options when extension is enabled
            col.separator()
            col.label(text="Extension Options:")

            # Add any additional settings here as they become available
            # For now, just show that the extension is active
            row = col.row()
            row.label(text="Status: Active", icon='CHECKMARK')

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

        # Status information
        if hasattr(scene, 'enable_ext_bmesh_encoding'):
            if scene.enable_ext_bmesh_encoding:
                col.label(text="• Extension: Enabled", icon='CHECKBOX_HLT')
            else:
                col.label(text="• Extension: Disabled", icon='CHECKBOX_DEHLT')


class EXTBMeshEncoding_PT_GLTFPanel(Panel):
    """Panel for EXT_bmesh_encoding in glTF export dialog."""

    bl_label = "EXT_bmesh_encoding"
    bl_idname = "EXT_BMESH_ENCODING_PT_gltf"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        """Check if this panel should be shown."""
        return (context.space_data.active_operator and
                hasattr(context.space_data.active_operator, 'bl_idname') and
                'gltf' in context.space_data.active_operator.bl_idname.lower())

    def draw(self, context):
        """Draw the glTF export panel."""
        layout = self.layout
        scene = context.scene

        layout.use_property_split = True
        layout.use_property_decorate = False

        # Extension settings
        col = layout.column(align=True)
        col.prop(scene, "enable_ext_bmesh_encoding", text="Include EXT_bmesh_encoding")

        # Additional info when enabled
        if hasattr(scene, 'enable_ext_bmesh_encoding') and scene.enable_ext_bmesh_encoding:
            box = layout.box()
            box.label(text="Extension will preserve:")
            col = box.column(align=True)
            col.label(text="• BMesh topology information")
            col.label(text="• Edge connectivity and flow")
            col.label(text="• UV coordinate mapping")
            col.label(text="• Surface smoothness data")


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
    bpy.utils.register_class(EXTBMeshEncoding_PT_GLTFPanel)
    bpy.utils.register_class(EXTBMeshEncoding_MT_ExportMenu)

    # Add to menus
    bpy.types.VIEW3D_MT_object.append(menu_func_view3d)


def unregister():
    """Unregister UI components."""
    # Remove from menus
    bpy.types.VIEW3D_MT_object.remove(menu_func_view3d)

    bpy.utils.unregister_class(EXTBMeshEncoding_MT_ExportMenu)
    bpy.utils.unregister_class(EXTBMeshEncoding_PT_GLTFPanel)
    bpy.utils.unregister_class(EXTBMeshEncoding_PT_MainPanel)
