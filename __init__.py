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
from . import importer
from . import ui
from . import gltf_extension
from .logger import get_logger

logger = get_logger(__name__)


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

        # Register exporter
        exporter.register()
        logger.debug("Exporter registered")

        # Register importer
        importer.register()
        logger.debug("Importer registered")

        # Register UI
        ui.register()
        logger.debug("UI registered")

        # Register glTF extension
        gltf_extension.EXT_bmesh_encoding.register()
        logger.debug("glTF extension registered")

        logger.info("EXT_bmesh_encoding addon registered successfully")

    except Exception as e:
        logger.error(f"Failed to register EXT_bmesh_encoding addon: {e}")
        # Don't re-raise - allow Blender to continue loading other addons
        # The addon will still be listed but may not function properly


def unregister():
    """Unregister the addon."""
    try:
        logger.info("Unregistering EXT_bmesh_encoding addon...")

        # Unregister in reverse order
        gltf_extension.EXT_bmesh_encoding.unregister()
        logger.debug("glTF extension unregistered")

        ui.unregister()
        logger.debug("UI unregistered")

        importer.unregister()
        logger.debug("Importer unregistered")

        exporter.unregister()
        logger.debug("Exporter unregistered")

        bpy.utils.unregister_class(EXTBMeshEncodingPreferences)
        logger.debug("Preferences class unregistered")

        logger.info("EXT_bmesh_encoding addon unregistered successfully")

    except Exception as e:
        logger.error(f"Failed to unregister EXT_bmesh_encoding addon: {e}")
        # Don't re-raise - allow Blender to continue unloading other addons


class glTF2ImportUserExtension:
    """glTF import user extension for EXT_bmesh_encoding."""

    def __init__(self):
        """Initialize the import extension."""
        # Lazy import to minimize initialization
        from .importer import EXTBMeshEncodingImporter
        self.importer = EXTBMeshEncodingImporter()

    def gather_import_decode_primitive(self, gltf, pymesh, prim, skin_idx):
        """Hook called during primitive decoding to process EXT_bmesh_encoding BEFORE triangulation."""
        try:
            logger.info("EXT_bmesh_encoding gather_import_decode_primitive called - processing before triangulation")

            # Check if this primitive has EXT_bmesh_encoding extension
            if hasattr(prim, 'extensions') and prim.extensions and 'EXT_bmesh_encoding' in prim.extensions:
                logger.info("Found EXT_bmesh_encoding extension in primitive - storing data for post-triangulation reconstruction")

                # Store the extension data in the glTF context for later use
                if not hasattr(gltf, 'ext_bmesh_encoding_data'):
                    gltf.ext_bmesh_encoding_data = {}

                # Use primitive index as key
                prim_idx = getattr(prim, 'index', id(prim))
                gltf.ext_bmesh_encoding_data[prim_idx] = prim.extensions['EXT_bmesh_encoding']

                logger.info(f"Stored EXT_bmesh_encoding data for primitive {prim_idx}")
            else:
                logger.debug("No EXT_bmesh_encoding extension found in this primitive")

        except Exception as e:
            logger.error(f"Error in gather_import_decode_primitive: {e}")

    def gather_import_mesh_after_hook(self, gltf, pymesh, mesh):
        """Hook called after mesh import to reconstruct original topology from EXT_bmesh_encoding."""
        try:
            logger.info("EXT_bmesh_encoding gather_import_mesh_after_hook called - reconstructing topology")

            # Check if we have stored EXT_bmesh_encoding data
            if hasattr(gltf, 'ext_bmesh_encoding_data') and gltf.ext_bmesh_encoding_data:
                logger.info(f"Found stored EXT_bmesh_encoding data for {len(gltf.ext_bmesh_encoding_data)} primitives")

                # Process each primitive that had EXT_bmesh_encoding data
                for prim_idx, extension_data in gltf.ext_bmesh_encoding_data.items():
                    logger.info(f"Processing EXT_bmesh_encoding for primitive {prim_idx}")

                    # Reconstruct BMesh from extension data
                    reconstructed_bmesh = self.importer.decoder.decode_extension_to_bmesh(extension_data, gltf)

                    if reconstructed_bmesh:
                        logger.info(f"Successfully reconstructed BMesh: {len(reconstructed_bmesh.verts)} verts, {len(reconstructed_bmesh.faces)} faces")

                        # Apply reconstructed BMesh to Blender mesh
                        success = self.importer.decoder.apply_bmesh_to_blender_mesh(reconstructed_bmesh, mesh)

                        if success:
                            logger.info("Successfully applied EXT_bmesh_encoding topology reconstruction")
                        else:
                            logger.warning("Failed to apply EXT_bmesh_encoding topology reconstruction")

                        reconstructed_bmesh.free()
                    else:
                        logger.warning(f"Failed to reconstruct BMesh from EXT_bmesh_encoding data for primitive {prim_idx}")
            else:
                logger.debug("No EXT_bmesh_encoding data found for reconstruction")

        except Exception as e:
            logger.error(f"Error in gather_import_mesh_after_hook: {e}")

    def gather_import_mesh_before_hook(self, pymesh, gltf):
        """Hook called before mesh import - now mainly for logging."""
        try:
            logger.debug("EXT_bmesh_encoding gather_import_mesh_before_hook called")
        except Exception as e:
            logger.error(f"Error in gather_import_mesh_before_hook: {e}")

    def gather_import_armature_bone_after_hook(self, gltf_node, blender_object, blender_bone, gltf):
        """Hook called after armature/bone import."""
        try:
            self.importer.process_armature_bone_after_hook(gltf_node, blender_object, blender_bone, gltf)
        except Exception as e:
            logger.error(f"Error in gather_import_armature_bone_after_hook: {e}")


class glTF2ExportUserExtension:
    """glTF export user extension for EXT_bmesh_encoding."""

    def __init__(self):
        """Initialize the export extension."""
        # Lazy import to minimize initialization
        from .exporter import EXTBMeshEncodingExporter
        self.exporter = EXTBMeshEncodingExporter()

    def gather_gltf_hook(self, gltf2_object, blender_object, export_settings):
        """Hook called during glTF export to add EXT_bmesh_encoding."""
        try:
            self.exporter.process_export_hook(gltf2_object, blender_object, export_settings)
        except Exception as e:
            logger.error(f"Error in gather_gltf_hook: {e}")


if __name__ == "__main__":
    register()
