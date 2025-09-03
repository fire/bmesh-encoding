# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""Standalone glTF exporter with EXT_bmesh_encoding support."""

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ExportHelper

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


def menu_func_export(self, context):
    """Add export menu item."""
    self.layout.operator(
        ExportGLTFWithEXTBmeshEncoding.bl_idname,
        text="glTF 2.0 with EXT_bmesh_encoding (.gltf/.glb)"
    )


class EXTBMeshEncodingExporter:
    """Exporter class for EXT_bmesh_encoding extension hooks."""

    def __init__(self):
        """Initialize the exporter."""
        self.encoder = BmeshEncoder()

    def process_export_hook(self, gltf2_object, blender_object, export_settings):
        """Process EXT_bmesh_encoding during glTF export."""
        try:
            logger.info("Processing EXT_bmesh_encoding for glTF export")

            # Check if EXT_bmesh_encoding is enabled in export settings
            if not getattr(export_settings, 'export_ext_bmesh_encoding', True):
                logger.info("EXT_bmesh_encoding disabled in export settings")
                return

            # Process mesh objects for EXT_bmesh_encoding
            if hasattr(blender_object, 'type') and blender_object.type == 'MESH':
                logger.info(f"Processing mesh object: {blender_object.name}")

                # Get the mesh data
                mesh = blender_object.data

                # Encode BMesh topology to extension data
                extension_data = self.encoder.encode_bmesh_to_gltf_extension(mesh, export_settings)

                if extension_data:
                    # Add extension to glTF object
                    if not hasattr(gltf2_object, 'extensions'):
                        gltf2_object.extensions = {}

                    gltf2_object.extensions['EXT_bmesh_encoding'] = extension_data
                    logger.info("Added EXT_bmesh_encoding extension to glTF object")
                else:
                    logger.warning("Failed to encode BMesh topology")

        except Exception as e:
            logger.error(f"Error processing EXT_bmesh_encoding during export: {e}")


def register():
    """Register the exporter."""
    # Note: We don't register menu items since glTF-Blender-IO already provides
    # standard glTF import/export. Our extension hooks are discovered automatically.
    pass


def unregister():
    """Unregister the exporter."""
    # No menu items to unregister since we don't register any
    pass
