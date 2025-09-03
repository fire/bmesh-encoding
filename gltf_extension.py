# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""glTF EXT_bmesh_encoding extension hooks for Blender's glTF exporter."""

import bpy
from bpy.props import BoolProperty
from bpy.types import Scene
import json
from typing import Any, Dict, Optional, Tuple

from .logger import get_logger

logger = get_logger(__name__)


class EXT_bmesh_encoding:
    """glTF EXT_bmesh_encoding extension implementation."""

    def __init__(self):
        """Initialize the extension."""
        self.extension_name = "EXT_bmesh_encoding"
        self.encoder = None
        self.decoder = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of encoder and decoder."""
        if self._initialized:
            return

        try:
            from .encoding import BmeshEncoder
            from .decoding import BmeshDecoder
            self.encoder = BmeshEncoder()
            self.decoder = BmeshDecoder()
            self._initialized = True
            logger.debug("EXT_bmesh_encoding encoder and decoder initialized")
        except ImportError as e:
            logger.warning(f"Failed to import BMesh encoder/decoder: {e}")
            logger.warning("EXT_bmesh_encoding will not function without Blender's bmesh module")
            self.encoder = None
            self.decoder = None

    @staticmethod
    def register():
        """Register the extension with Blender."""
        try:
            # Register scene property for extension enable/disable
            Scene.enable_ext_bmesh_encoding = BoolProperty(
                name="EXT_bmesh_encoding",
                description="Enable EXT_bmesh_encoding extension for BMesh topology preservation",
                default=True,
            )
            logger.debug("EXT_bmesh_encoding scene property registered")

            # Try immediate registration first
            if EXT_bmesh_encoding._try_register_gltf_extension():
                logger.info("EXT_bmesh_encoding registered immediately with glTF exporter")
            else:
                # Defer registration until glTF system is available
                EXT_bmesh_encoding._setup_deferred_registration()
                logger.info("EXT_bmesh_encoding registration deferred until glTF system is available")

        except Exception as e:
            logger.error(f"Failed to register EXT_bmesh_encoding: {e}")
            # Don't raise - allow addon to load even if extension registration fails

    @staticmethod
    def _try_register_gltf_extension():
        """Attempt to register with glTF exporter if available."""
        try:
            from io_scene_gltf2 import export_gltf2, import_gltf2

            # Add extension to export hooks
            if hasattr(export_gltf2, 'register_extension'):
                export_gltf2.register_extension(ext_bmesh_encoding)

            # Add extension to import hooks
            if hasattr(import_gltf2, 'register_extension'):
                import_gltf2.register_extension(ext_bmesh_encoding)

            return True

        except ImportError:
            return False

    @staticmethod
    def _setup_deferred_registration():
        """Set up deferred registration using scene update handler."""
        @bpy.app.handlers.persistent
        def deferred_gltf_registration(scene, depsgraph=None):
            """Register EXT_bmesh_encoding when glTF system becomes available."""
            if EXT_bmesh_encoding._try_register_gltf_extension():
                logger.info("EXT_bmesh_encoding successfully registered with glTF exporter (deferred)")
                # Remove this handler once registration succeeds
                bpy.app.handlers.depsgraph_update_post.remove(deferred_gltf_registration)
                return

            # If still not available, keep trying (handler will be called again)
            logger.debug("glTF system still not available, will retry registration")

        # Add the handler if not already present
        if deferred_gltf_registration not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(deferred_gltf_registration)

    @staticmethod
    def unregister():
        """Unregister the extension from Blender."""
        # Unregister scene property
        if hasattr(Scene, 'enable_ext_bmesh_encoding'):
            del Scene.enable_ext_bmesh_encoding

        # Clean up any deferred registration handlers
        EXT_bmesh_encoding._cleanup_deferred_registration()

        # Unregister from glTF exporter if available
        try:
            from io_scene_gltf2 import export_gltf2, import_gltf2

            if hasattr(export_gltf2, 'unregister_extension'):
                export_gltf2.unregister_extension(ext_bmesh_encoding)

            if hasattr(import_gltf2, 'unregister_extension'):
                import_gltf2.unregister_extension(ext_bmesh_encoding)

            logger.info("EXT_bmesh_encoding unregistered from glTF exporter")

        except ImportError:
            pass

    @staticmethod
    def _cleanup_deferred_registration():
        """Clean up any deferred registration handlers."""
        # Remove any deferred registration handlers that might be active
        handlers_to_remove = []
        for handler in bpy.app.handlers.depsgraph_update_post:
            # Check if this is our deferred registration handler
            if hasattr(handler, '__name__') and handler.__name__ == 'deferred_gltf_registration':
                handlers_to_remove.append(handler)

        for handler in handlers_to_remove:
            bpy.app.handlers.depsgraph_update_post.remove(handler)
            logger.debug("Removed deferred glTF registration handler")

    def export_node(self, gltf2_object: Any, blender_object: bpy.types.Object, export_settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Export hook for nodes.

        This is called during glTF export for each Blender object.
        We don't need to do anything special for nodes, as the mesh export handles the extension.
        """
        return None

    def export_mesh(self, gltf2_object: Any, blender_mesh: bpy.types.Mesh, export_settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Export hook for meshes.

        This is called during glTF export for each mesh primitive.
        We encode the BMesh topology and add it as an extension to the primitive.
        """
        # Check if extension is enabled
        if not getattr(bpy.context.scene, 'enable_ext_bmesh_encoding', True):
            logger.debug("EXT_bmesh_encoding disabled, skipping mesh export hook")
            return None

        # Find the Blender object this mesh belongs to
        blender_object = None
        for obj in bpy.context.scene.objects:
            if obj.data == blender_mesh:
                blender_object = obj
                break

        if not blender_object:
            logger.warning(f"Could not find Blender object for mesh {blender_mesh.name}")
            return None

        logger.info(f"Exporting EXT_bmesh_encoding for mesh '{blender_mesh.name}'")

        try:
            # Encode the mesh topology
            extension_data = self.encoder.encode_object(blender_object)

            if not extension_data:
                logger.warning(f"No extension data generated for mesh '{blender_mesh.name}'")
                return None

            # Create buffer views for the encoded data
            buffer_views = self.encoder.create_buffer_views(gltf2_object, b'', extension_data)

            if not buffer_views:
                logger.warning(f"No buffer views created for mesh '{blender_mesh.name}'")
                return None

            # Add extension to the mesh primitive
            extension_dict = {
                self.extension_name: buffer_views
            }

            logger.info(f"Successfully exported EXT_bmesh_encoding for mesh '{blender_mesh.name}'")
            return extension_dict

        except Exception as e:
            logger.error(f"Failed to export EXT_bmesh_encoding for mesh '{blender_mesh.name}': {e}")
            return None

    def import_node(self, gltf2_object: Any, blender_object: bpy.types.Object, import_settings: Dict[str, Any]) -> Optional[bpy.types.Object]:
        """
        Import hook for nodes.

        This is called during glTF import for each node.
        We don't need to do anything special for nodes.
        """
        return None

    def import_mesh(self, gltf2_object: Any, blender_mesh: bpy.types.Mesh, import_settings: Dict[str, Any]) -> Optional[bpy.types.Mesh]:
        """
        Import hook for meshes.

        This is called during glTF import for each mesh primitive.
        We check for EXT_bmesh_encoding extension and reconstruct the topology.
        """
        # Check if the primitive has our extension
        if not hasattr(gltf2_object, 'extensions') or not gltf2_object.extensions:
            return None

        extension_data = gltf2_object.extensions.get(self.extension_name)
        if not extension_data:
            return None

        logger.info(f"Importing EXT_bmesh_encoding for mesh '{blender_mesh.name}'")

        try:
            # Decode the extension data to reconstruct BMesh topology
            reconstructed_bmesh = self.decoder.decode_extension_to_bmesh(extension_data, gltf2_object)

            if not reconstructed_bmesh:
                logger.warning(f"Failed to reconstruct BMesh from EXT_bmesh_encoding for mesh '{blender_mesh.name}'")
                return None

            # Apply the reconstructed topology to the imported mesh
            # This would typically involve updating the mesh's topology to match the BMesh
            # For now, we'll just log the successful reconstruction
            logger.info(f"Successfully reconstructed BMesh topology for mesh '{blender_mesh.name}'")

            # Clean up
            reconstructed_bmesh.free()

            return blender_mesh

        except Exception as e:
            logger.error(f"Failed to import EXT_bmesh_encoding for mesh '{blender_mesh.name}': {e}")
            return None

    def gather_gltf_extensions(self, export_settings: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Gather extension data for the glTF root.

        This is called to collect extension declarations for the glTF file.
        """
        # Check if extension is enabled and used
        if not getattr(bpy.context.scene, 'enable_ext_bmesh_encoding', True):
            return {}, {}

        # Declare the extension as used
        extensions_used = {
            self.extension_name: {}
        }

        extensions_required = {}  # Not required for this extension

        return extensions_used, extensions_required


# Create singleton instance
ext_bmesh_encoding = EXT_bmesh_encoding()
