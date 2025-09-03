# SPDX-License-Identifier: MIT
"""Logging utilities for EXT_bmesh_encoding addon."""

import logging
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the EXT_bmesh_encoding addon."""
    return logging.getLogger(f"ext_bmesh_encoding.{name}")


def setup_logging(level: Optional[int] = None) -> None:
    """Set up logging for the EXT_bmesh_encoding addon."""
    if level is None:
        level = logging.INFO

    # Configure the logger
    logger = logging.getLogger("ext_bmesh_encoding")
    logger.setLevel(level)

    # Only add handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
