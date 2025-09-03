# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""Standalone glTF importer with EXT_bmesh_encoding support."""

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper

from .logger import get_logger

logger = get_logger(__name__)


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

    def draw(self, context):
        """Draw the import options UI."""
        layout = self.layout

        # Import options
        layout.prop(self, "import_pack_images")
        layout.prop(self, "import_shading")
        layout.prop(self, "use_custom_normals")
        layout.prop(self, "use_custom_properties")

        # EXT_bmesh_encoding is handled automatically by registered extension hooks
        # No UI parameter needed since it's always enabled when the addon is active

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

            logger.info(f"Starting glTF import with EXT_bmesh_encoding support from: {self.filepath}")
            logger.debug(f"Import arguments: {import_args}")

            # Call the glTF import operator
            # EXT_bmesh_encoding extension will be handled automatically by the registered extension
            result = bpy.ops.import_scene.gltf(**import_args)

            if result == {'FINISHED'}:
                logger.info(f"Successfully imported glTF file: {self.filepath}")
                self.report({'INFO'}, f"Imported from {self.filepath}")
                return {'FINISHED'}
            else:
                logger.error(f"glTF import failed with result: {result}")
                self.report({'ERROR'}, f"Import failed: {result}")
                return {'CANCELLED'}

        except Exception as e:
            logger.error(f"Import failed with exception: {e}")
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            return {'CANCELLED'}


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

        # EXT_bmesh_encoding is handled automatically by registered extension hooks
        # No UI parameter needed since it's always enabled when the addon is active


def menu_func_import(self, context):
    """Add import menu item."""
    self.layout.operator(
        ImportGLTFWithEXTBmeshEncoding.bl_idname,
        text="glTF 2.0 with EXT_bmesh_encoding (.gltf/.glb)"
    )


def register():
    """Register the importer."""
    bpy.utils.register_class(ImportGLTFWithEXTBmeshEncoding)
    bpy.utils.register_class(EXTBMeshEncoding_PT_ImportPanel)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    """Unregister the importer."""
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(EXTBMeshEncoding_PT_ImportPanel)
    bpy.utils.unregister_class(ImportGLTFWithEXTBmeshEncoding)
