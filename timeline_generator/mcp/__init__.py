"""
Timeline Generator MCP Package
==============================

Shared backbone for MCP server implementations.
"""

from .tools import (
    generate_timeline_impl,
    quick_timeline_impl,
    get_config_template_impl,
    list_styles_impl,
    list_themes_impl,
    TOON_TEMPLATES,
    YAML_TEMPLATES,
)

__all__ = [
    "generate_timeline_impl",
    "quick_timeline_impl",
    "get_config_template_impl",
    "list_styles_impl",
    "list_themes_impl",
    "TOON_TEMPLATES",
    "YAML_TEMPLATES",
]

