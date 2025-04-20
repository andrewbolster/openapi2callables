"""Top-level package for OpenAPI2Callables."""

__author__ = """Andrew Bolster"""
__email__ = "andrew.bolster@gmail.com"
import importlib.metadata

__version__ = importlib.metadata.version("openapi2callables")

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info(f"OpenAPI2Callables version {__version__}")

from .tools import APITool, LocalTool, Tool  # noqa: E402
