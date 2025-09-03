# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""Standalone glTF exporter with EXT_bmesh_encoding support."""

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .encoding import BmeshEncoder
from .logger import get_logger

logger = get_logger(__name__)


class ExportGLTFWithEXTBmeshEncoding(Operator, ExportHelper):
    """Export glTF 2.0 with EXT_bmesh_encoding extension."""

    bl_idname = "export_scene.gltf_ext_bmesh_encoding"
    bl_label = "Export glTF with EXT_bmesh_encoding"
    bl_description = "Export scene as glTF 2.0 with EXT_bmesh_encoding extension for BMesh topology preservation"

    # ExportHelper mixin class uses this
    filename_ext = ".gltf"

    filter_glob: StringProperty(
        default="*.gltf;*.glb",
        options={'HIDDEN'},
        maxlen=255,
    )

    # Export options
    export_format: bpy.props.EnumProperty(
        name="Format",
        items=(
            ('GLTF_SEPARATE', "glTF Separate", "Separate (.gltf + .bin + textures)"),
            ('GLTF_EMBEDDED', "glTF Embedded", "Embedded (.gltf)"),
            ('GLB', "glTF Binary", "Binary (.glb)"),
        ),
        default='GLB',
    )

    use_selection: BoolProperty(
        name="Selected Objects",
        description="Export selected objects only",
        default=False,
    )

    export_apply: BoolProperty(
        name="Apply Transform",
        description="Apply object transforms to mesh data",
        default=True,
    )

    export_y_up: BoolProperty(
        name="Y Up",
        description="+Y Up",
        default=True,
    )

    export_ext_bmesh_encoding: BoolProperty(
        name="EXT_bmesh_encoding",
        description="Include EXT_bmesh_encoding extension for BMesh topology preservation",
        default=True,
    )

    def draw(self, context):
        """Draw the export options UI."""
        layout = self.layout

        # Format selection
        layout.prop(self, "export_format")

        # Export scope
        layout.prop(self, "use_selection")

        # Transform options
        layout.prop(self, "export_apply")
        layout.prop(self, "export_y_up")

        # Extension options
        box = layout.box()
        box.label(text="Extensions:")
        box.prop(self, "export_ext_bmesh_encoding")

    def execute(self, context):
        """Execute the export operation."""
        try:
            # Import glTF exporter at runtime to avoid import issues
            try:
                from io_scene_gltf2 import ExportGLTF2
            except ImportError as e:
                logger.error(f"Failed to import glTF exporter: {e}")
                self.report({'ERROR'}, "glTF exporter not available. Please ensure the glTF addon is enabled.")
                return {'CANCELLED'}

            # Create export arguments
            export_args = {
                'filepath': self.filepath,
                'check_existing': True,
                'export_format': self.export_format,
                'use_selection': self.use_selection,
                'export_apply': self.export_apply,
                'export_y_up': self.export_y_up,
                'export_extras': True,
                'export_cameras': True,
                'export_lights': True,
            }

            # Add EXT_bmesh_encoding if enabled
            if self.export_ext_bmesh_encoding:
                export_args['export_ext_bmesh_encoding'] = True

            # Call the glTF exporter
            result = ExportGLTF2.export(context, **export_args)

            if result == {'FINISHED'}:
                self.report({'INFO'}, f"Exported to {self.filepath}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Export failed: {result}")
                return {'CANCELLED'}

        except Exception as e:
            logger.error(f"Export failed: {e}")
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}


class ImportGLTFWithEXTBmeshEncoding(Operator, ImportHelper):
    """Import glTF 2.0 with EXT_bmesh_encoding extension support."""

    bl_idname = "import_scene.gltf_ext_bmesh_encoding"
    bl_label = "Import glTF with EXT_bmesh_encoding"
    bl_description = "Import glTF 2.0 files with EXT_bmesh_encoding extension support for BMesh topology reconstruction"

    # ImportHelper mixin class uses this
    filename_ext = ".gltf"

    filter_glob: StringProperty(
        default="*.gltf;*.glb",
        options={'HIDDEN'},
        maxlen=255,
    )

    # Import options
    import_pack_images: BoolProperty(
        name="Pack Images",
        description="Pack all images into the .blend file",
        default=True,
    )

    import_shading: bpy.props.EnumProperty(
        name="Shading",
        items=(
            ('NORMALS', "Use Normal Data", "Use normal data from file"),
            ('FLAT', "Flat Shading", "Use flat shading"),
            ('SMOOTH', "Smooth Shading", "Use smooth shading"),
        ),
        default='NORMALS',
    )

    use_custom_normals: BoolProperty(
        name="Custom Normals",
        description="Import custom normals, if available",
        default=True,
    )

    use_custom_properties: BoolProperty(
        name="Custom Properties",
        description="Import custom properties as custom properties",
        default=True,
    )

    import_ext_bmesh_encoding: BoolProperty(
        name="EXT_bmesh_encoding",
        description="Import EXT_bmesh_encoding extension for BMesh topology reconstruction",
        default=True,
    )

    def draw(self, context):
        """Draw the import options UI."""
        layout = self.layout

        # Import options
        layout.prop(self, "import_pack_images")
        layout.prop(self, "import_shading")
        layout.prop(self, "use_custom_normals")
        layout.prop(self, "use_custom_properties")

        # Extension options
        box = layout.box()
        box.label(text="Extensions:")
        box.prop(self, "import_ext_bmesh_encoding")

    def execute(self, context):
        """Execute the import operation."""
        try:
            # Use version-appropriate parameters for glTF import operator
            # (similar to VRM addon approach)
            if bpy.app.version < (4, 2):
                import_args = {
                    'filepath': self.filepath,
                    'import_pack_images': self.import_pack_images,
                    'bone_heuristic': 'BLENDER',
                    'guess_original_bind_pose': True,
                }
            elif bpy.app.version < (4, 5):
                import_args = {
                    'filepath': self.filepath,
                    'import_pack_images': self.import_pack_images,
                    'bone_heuristic': 'BLENDER',
                    'guess_original_bind_pose': True,
                    'disable_bone_shape': False,
                }
            else:  # Blender 4.5+
                import_args = {
                    'filepath': self.filepath,
                    'import_pack_images': self.import_pack_images,
                    'bone_heuristic': 'BLENDER',
                    'guess_original_bind_pose': True,
                    'disable_bone_shape': False,
                    'import_scene_as_collection': False,
                }

            # Call the glTF import operator
            # EXT_bmesh_encoding extension will be handled automatically by the registered extension
            result = bpy.ops.import_scene.gltf(**import_args)

            if result == {'FINISHED'}:
                self.report({'INFO'}, f"Imported from {self.filepath}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Import failed: {result}")
                return {'CANCELLED'}

        except Exception as e:
            logger.error(f"Import failed: {e}")
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            return {'CANCELLED'}


class EXTBMeshEncoding_PT_ExportPanel(Panel):
    """Panel for EXT_bmesh_encoding export options."""

    bl_label = "EXT_bmesh_encoding Export"
    bl_idname = "EXT_BMESH_ENCODING_PT_export"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        """Check if this panel should be shown."""
        return (context.space_data.active_operator and
                context.space_data.active_operator.bl_idname == "export_scene.gltf_ext_bmesh_encoding")

    def draw(self, context):
        """Draw the panel."""
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        operator = context.space_data.active_operator

        layout.prop(operator, "export_format")
        layout.prop(operator, "use_selection")
        layout.prop(operator, "export_apply")
        layout.prop(operator, "export_y_up")

        box = layout.box()
        box.label(text="Extensions:")
        box.prop(operator, "export_ext_bmesh_encoding")


class EXTBMeshEncoding_PT_ImportPanel(Panel):
    """Panel for EXT_bmesh_encoding import options."""

    bl_label = "EXT_bmesh_encoding Import"
    bl_idname = "EXT_BMESH_ENCODING_PT_import"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        """Check if this panel should be shown."""
        return (context.space_data.active_operator and
                context.space_data.active_operator.bl_idname == "import_scene.gltf_ext_bmesh_encoding")

    def draw(self, context):
        """Draw the panel."""
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        operator = context.space_data.active_operator

        layout.prop(operator, "import_pack_images")
        layout.prop(operator, "import_shading")
        layout.prop(operator, "use_custom_normals")
        layout.prop(operator, "use_custom_properties")

        box = layout.box()
        box.label(text="Extensions:")
        box.prop(operator, "import_ext_bmesh_encoding")


def menu_func_export(self, context):
    """Add export menu item."""
    self.layout.operator(
        ExportGLTFWithEXTBmeshEncoding.bl_idname,
        text="glTF 2.0 with EXT_bmesh_encoding (.gltf/.glb)"
    )


def menu_func_import(self, context):
    """Add import menu item."""
    self.layout.operator(
        ImportGLTFWithEXTBmeshEncoding.bl_idname,
        text="glTF 2.0 with EXT_bmesh_encoding (.gltf/.glb)"
    )


def register():
    """Register the exporter and importer."""
    bpy.utils.register_class(ExportGLTFWithEXTBmeshEncoding)
    bpy.utils.register_class(ImportGLTFWithEXTBmeshEncoding)
    bpy.utils.register_class(EXTBMeshEncoding_PT_ExportPanel)
    bpy.utils.register_class(EXTBMeshEncoding_PT_ImportPanel)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    """Unregister the exporter and importer."""
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(EXTBMeshEncoding_PT_ImportPanel)
    bpy.utils.unregister_class(EXTBMeshEncoding_PT_ExportPanel)
    bpy.utils.unregister_class(ImportGLTFWithEXTBmeshEncoding)
    bpy.utils.unregister_class(ExportGLTFWithEXTBmeshEncoding)
