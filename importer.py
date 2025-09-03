# SPDX-License-Identifier: MIT
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


class EXTBMeshEncodingImporter:
    """Importer class for EXT_bmesh_encoding extension hooks."""

    def __init__(self):
        """Initialize the importer."""
        from .decoding import BmeshDecoder
        self.decoder = BmeshDecoder()

    def process_mesh_before_hook(self, gltf_mesh, blender_mesh, gltf_importer):
        """Process EXT_bmesh_encoding during mesh import."""
        try:
            logger.info("Processing EXT_bmesh_encoding for mesh import")

            # Check if any primitives have EXT_bmesh_encoding extension
            if hasattr(gltf_mesh, 'primitives'):
                for primitive in gltf_mesh.primitives:
                    if hasattr(primitive, 'extensions') and primitive.extensions:
                        ext_bmesh_data = getattr(primitive.extensions, 'EXT_bmesh_encoding', None)
                        if ext_bmesh_data:
                            logger.info("Found EXT_bmesh_encoding data in primitive")

                            # Convert extension data to dict format
                            extension_dict = self._convert_extension_to_dict(ext_bmesh_data)

                            # Reconstruct BMesh from extension data
                            reconstructed_bmesh = self.decoder.decode_gltf_extension_to_bmesh(extension_dict, gltf_importer)

                            if reconstructed_bmesh and blender_mesh:
                                # Apply reconstructed BMesh to Blender mesh
                                success = self.decoder.apply_bmesh_to_blender_mesh(
                                    reconstructed_bmesh, blender_mesh
                                )
                                if success:
                                    logger.info("Successfully applied EXT_bmesh_encoding topology")
                                else:
                                    logger.warning("Failed to apply EXT_bmesh_encoding topology")

                                reconstructed_bmesh.free()

        except Exception as e:
            logger.error(f"Error processing EXT_bmesh_encoding during import: {e}")

    def process_gltf_mesh_before_hook(self, pymesh, gltf):
        """Process EXT_bmesh_encoding during glTF mesh import (before Blender mesh creation)."""
        try:
            logger.info("Processing EXT_bmesh_encoding for glTF mesh import")

            # Store the EXT_bmesh_encoding data for later use when the Blender mesh is created
            if hasattr(pymesh, 'primitives'):
                for primitive in pymesh.primitives:
                    if hasattr(primitive, 'extensions') and primitive.extensions:
                        ext_bmesh_data = getattr(primitive.extensions, 'EXT_bmesh_encoding', None)
                        if ext_bmesh_data:
                            logger.info("Found EXT_bmesh_encoding data in primitive - storing for later processing")

                            # Convert extension data to dict format
                            extension_dict = self._convert_extension_to_dict(ext_bmesh_data)

                            # Store the extension data in the glTF context for later retrieval
                            # We'll use the pymesh object as a key to store the data
                            if not hasattr(gltf, 'ext_bmesh_encoding_data'):
                                gltf.ext_bmesh_encoding_data = {}

                            # Store by mesh index to match later
                            mesh_idx = getattr(pymesh, 'mesh_idx', id(pymesh))
                            gltf.ext_bmesh_encoding_data[mesh_idx] = extension_dict

        except Exception as e:
            logger.error(f"Error processing EXT_bmesh_encoding during glTF mesh import: {e}")

    def process_armature_bone_after_hook(self, gltf_node, blender_object, blender_bone, gltf):
        """Process armature/bone after import."""
        # This hook can be used for armature-specific EXT_bmesh_encoding processing
        # For now, we don't need special handling here
        pass

    def _convert_extension_to_dict(self, ext_data):
        """Convert glTF extension object to dictionary format."""
        try:
            logger.info(f"Converting extension data of type: {type(ext_data)}")

            # Handle direct dictionary
            if isinstance(ext_data, dict):
                logger.info(f"Extension data is already dict with keys: {list(ext_data.keys())}")
                return ext_data

            # Handle object with __dict__
            if hasattr(ext_data, '__dict__'):
                result = vars(ext_data)
                logger.info(f"Converted object to dict with keys: {list(result.keys())}")
                return result

            # Fallback: try to extract known attributes recursively
            result = {}
            for attr in ['vertices', 'edges', 'loops', 'faces']:
                value = getattr(ext_data, attr, None)
                if value is not None:
                    logger.info(f"Found {attr} attribute of type: {type(value)}")

                    # Recursively convert nested objects
                    if hasattr(value, '__dict__'):
                        converted_value = vars(value)
                        logger.info(f"Converted {attr} object to dict with keys: {list(converted_value.keys())}")

                        # Special handling for attributes nested objects
                        if 'attributes' in converted_value:
                            attrs = converted_value['attributes']
                            if hasattr(attrs, '__dict__'):
                                converted_value['attributes'] = vars(attrs)
                                logger.info(f"Converted {attr}.attributes to dict with keys: {list(converted_value['attributes'].keys())}")
                            elif isinstance(attrs, dict):
                                logger.info(f"{attr}.attributes is already dict with keys: {list(attrs.keys())}")

                        result[attr] = converted_value
                    elif isinstance(value, (list, dict)):
                        result[attr] = value
                        logger.info(f"Used {attr} as-is (list/dict)")
                    else:
                        logger.warning(f"Unknown type for {attr}: {type(value)}")

            logger.info(f"Final converted extension data keys: {list(result.keys())}")
            return result

        except Exception as e:
            logger.error(f"Failed to convert extension data: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}


def register():
    """Register the importer."""
    # Note: We don't register menu items since glTF-Blender-IO already provides
    # standard glTF import/export. Our extension hooks are discovered automatically.
    pass


def unregister():
    """Unregister the importer."""
    # No menu items to unregister since we don't register any
    pass
