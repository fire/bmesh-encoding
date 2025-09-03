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

            # Log registration status for debugging
            EXT_bmesh_encoding._log_registration_status()

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

    @staticmethod
    def _log_registration_status():
        """Log the current registration status of the extension hooks."""
        try:
            # Check if glTF modules are available
            try:
                from io_scene_gltf2 import export_gltf2, import_gltf2
                gltf_available = True
            except ImportError:
                gltf_available = False
                logger.warning("glTF modules not available for extension registration check")
                return

            # Check export extension registration
            export_registered = False
            if hasattr(export_gltf2, 'registered_extensions'):
                export_registered = ext_bmesh_encoding in export_gltf2.registered_extensions
            elif hasattr(export_gltf2, 'extensions'):
                export_registered = ext_bmesh_encoding in export_gltf2.extensions

            # Check import extension registration
            import_registered = False
            if hasattr(import_gltf2, 'registered_extensions'):
                import_registered = ext_bmesh_encoding in import_gltf2.registered_extensions
            elif hasattr(import_gltf2, 'extensions'):
                import_registered = ext_bmesh_encoding in import_gltf2.extensions

            logger.info("EXT_bmesh_encoding registration status:")
            logger.info(f"  glTF modules available: {gltf_available}")
            logger.info(f"  Export extension registered: {export_registered}")
            logger.info(f"  Import extension registered: {import_registered}")

            if export_registered and import_registered:
                logger.info("✅ EXT_bmesh_encoding extension hooks are properly registered")
            else:
                logger.warning("❌ EXT_bmesh_encoding extension hooks registration incomplete")
                if not export_registered:
                    logger.warning("  - Export extension NOT registered")
                if not import_registered:
                    logger.warning("  - Import extension NOT registered")

        except Exception as e:
            logger.error(f"Failed to check extension registration status: {e}")

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
        logger.debug(f"EXT_bmesh_encoding import_mesh called for mesh '{blender_mesh.name}'")
        logger.debug(f"gltf2_object type: {type(gltf2_object)}")
        logger.debug(f"blender_mesh type: {type(blender_mesh)}")
        logger.debug(f"import_settings keys: {list(import_settings.keys()) if import_settings else 'None'}")

        # Check if the primitive has our extension
        if not hasattr(gltf2_object, 'extensions') or not gltf2_object.extensions:
            logger.debug(f"No extensions found on gltf2_object for mesh '{blender_mesh.name}'")
            logger.debug(f"gltf2_object attributes: {dir(gltf2_object) if hasattr(gltf2_object, '__dict__') else 'No __dict__'}")
            return None

        logger.debug(f"Extensions found: {list(gltf2_object.extensions.keys())}")

        extension_data = gltf2_object.extensions.get(self.extension_name)
        if not extension_data:
            logger.debug(f"EXT_bmesh_encoding extension not found in extensions for mesh '{blender_mesh.name}'")
            return None

        logger.info(f"Found EXT_bmesh_encoding extension for mesh '{blender_mesh.name}'")
        logger.debug(f"Extension data keys: {list(extension_data.keys()) if isinstance(extension_data, dict) else type(extension_data)}")

        # Log mesh topology before reconstruction
        logger.debug(f"Original mesh topology - vertices: {len(blender_mesh.vertices)}, polygons: {len(blender_mesh.polygons)}")
        if blender_mesh.polygons:
            face_sizes = [len(poly.vertices) for poly in blender_mesh.polygons]
            logger.debug(f"Original face sizes: {face_sizes}")
            logger.debug(f"Face size distribution: triangles={face_sizes.count(3)}, quads={face_sizes.count(4)}, ngons={sum(1 for size in face_sizes if size > 4)}")

        try:
            # Decode the extension data to reconstruct BMesh topology
            logger.debug("Starting BMesh reconstruction from extension data...")
            reconstructed_bmesh = self.decoder.decode_extension_to_bmesh(extension_data, gltf2_object)

            if not reconstructed_bmesh:
                logger.warning(f"Failed to reconstruct BMesh from EXT_bmesh_encoding for mesh '{blender_mesh.name}'")
                logger.debug("decode_extension_to_bmesh returned None")
                return None

            logger.info(f"Successfully reconstructed BMesh: {len(reconstructed_bmesh.verts)} verts, {len(reconstructed_bmesh.edges)} edges, {len(reconstructed_bmesh.faces)} faces")

            # Log reconstructed topology
            if reconstructed_bmesh.faces:
                reconstructed_face_sizes = [len(face.verts) for face in reconstructed_bmesh.faces]
                logger.debug(f"Reconstructed face sizes: {reconstructed_face_sizes}")
                logger.debug(f"Reconstructed face distribution: triangles={reconstructed_face_sizes.count(3)}, quads={reconstructed_face_sizes.count(4)}, ngons={sum(1 for size in reconstructed_face_sizes if size > 4)}")

            # Apply the reconstructed BMesh to preserve original topology
            logger.debug("Applying reconstructed BMesh to Blender mesh...")
            success = self.decoder.apply_bmesh_to_blender_mesh(reconstructed_bmesh, blender_mesh)

            # Clean up the BMesh
            reconstructed_bmesh.free()
            logger.debug("BMesh cleaned up")

            if success:
                logger.info(f"Successfully applied EXT_bmesh_encoding topology to mesh '{blender_mesh.name}'")

                # Log final mesh topology
                logger.debug(f"Final mesh topology - vertices: {len(blender_mesh.vertices)}, polygons: {len(blender_mesh.polygons)}")
                if blender_mesh.polygons:
                    final_face_sizes = [len(poly.vertices) for poly in blender_mesh.polygons]
                    logger.debug(f"Final face sizes: {final_face_sizes}")
                    logger.debug(f"Final face distribution: triangles={final_face_sizes.count(3)}, quads={final_face_sizes.count(4)}, ngons={sum(1 for size in final_face_sizes if size > 4)}")

                return blender_mesh
            else:
                logger.error(f"Failed to apply reconstructed topology to mesh '{blender_mesh.name}'")
                logger.debug("apply_bmesh_to_blender_mesh returned False")
                return None

        except Exception as e:
            logger.error(f"Failed to import EXT_bmesh_encoding for mesh '{blender_mesh.name}': {e}")
            logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
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
