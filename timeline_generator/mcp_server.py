"""
Timeline Generator MCP Server (Legacy/Standard)
================================================

Standard MCP server implementation using the mcp library directly.
This is kept for compatibility with clients that may prefer the standard approach.

For most use cases, use the FastMCP server instead:
    timeline-mcp (default, uses FastMCP)

Usage:
    timeline-mcp-legacy

Author: kbichave
Repository: https://github.com/kbichave/timeline-generator-mcp
"""

from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent

from .mcp.tools import (
    generate_timeline_impl,
    quick_timeline_impl,
    get_config_template_impl,
    list_styles_impl,
    list_themes_impl,
)


# =============================================================================
# Server Instance
# =============================================================================

server = Server("timeline-generator-mcp")


# =============================================================================
# Tool Definitions
# =============================================================================

TOOLS = [
    Tool(
        name="generate_timeline",
        description="""Generate a timeline visualization from TOON, YAML, or JSON configuration.

RECOMMENDED: Use TOON format for 30-60% token savings vs JSON.

USE THIS TOOL WHEN:
- User provides detailed milestone data with dates, titles, descriptions
- User wants specific styling, themes, or custom colors
- User needs Gantt charts with duration/progress
- User wants animated GIF output

RETURNS: Base64-encoded image (PNG, GIF, or SVG)

EXAMPLE CONFIG (TOON - recommended for AI):
```
title: Project Roadmap
style: horizontal
theme: corporate
milestones[2]: date title description highlight
2024-01-15 Kickoff "Project begins" true
2024-06-01 Launch "Go live" false
output:
  format: png
  width: 1920
  height: 800
```""",
        inputSchema={
            "type": "object",
            "properties": {
                "config": {
                    "type": "string",
                    "description": "Timeline configuration in TOON (recommended), YAML, or JSON format.",
                },
                "format": {
                    "type": "string",
                    "enum": ["toon", "yaml", "json"],
                    "default": "toon",
                    "description": "Config format. 'toon' saves 30-60% tokens.",
                },
                "output_format": {
                    "type": "string",
                    "enum": ["png", "gif", "svg"],
                    "default": "png",
                    "description": "Output format.",
                },
            },
            "required": ["config"],
        },
    ),
    Tool(
        name="quick_timeline",
        description="""Quickly generate a timeline from a simple list of milestones.

USE THIS TOOL WHEN:
- User wants a fast, simple timeline
- User provides dates and titles in natural language
- No complex configuration needed

MILESTONE FORMAT: "YYYY-MM-DD:Title"

EXAMPLE:
milestones: ["2024-01-01:Project Start", "2024-06-15:Beta Release"]

RETURNS: Base64-encoded image""",
        inputSchema={
            "type": "object",
            "properties": {
                "milestones": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of milestones in 'DATE:TITLE' format.",
                    "minItems": 1,
                },
                "title": {
                    "type": "string",
                    "default": "Timeline",
                    "description": "Timeline title.",
                },
                "style": {
                    "type": "string",
                    "enum": ["horizontal", "vertical", "gantt", "roadmap", "infographic"],
                    "default": "horizontal",
                    "description": "Visual style.",
                },
                "theme": {
                    "type": "string",
                    "enum": ["minimal", "corporate", "creative", "dark"],
                    "default": "minimal",
                    "description": "Color theme.",
                },
                "output_format": {
                    "type": "string",
                    "enum": ["png", "gif", "svg"],
                    "default": "png",
                    "description": "Output format.",
                },
                "width": {
                    "type": "integer",
                    "default": 1920,
                    "description": "Image width in pixels.",
                },
                "height": {
                    "type": "integer",
                    "default": 800,
                    "description": "Image height in pixels.",
                },
            },
            "required": ["milestones"],
        },
    ),
    Tool(
        name="get_config_template",
        description="""Get a starter configuration template for timeline generation.

USE THIS TOOL WHEN:
- User wants to understand the configuration format
- User needs a starting point for customization

RETURNS: Template in TOON (default) or YAML format""",
        inputSchema={
            "type": "object",
            "properties": {
                "style": {
                    "type": "string",
                    "enum": ["horizontal", "vertical", "gantt", "roadmap", "infographic"],
                    "default": "horizontal",
                    "description": "Get template optimized for this style.",
                },
                "format": {
                    "type": "string",
                    "enum": ["toon", "yaml"],
                    "default": "toon",
                    "description": "Template format.",
                },
            },
        },
    ),
    Tool(
        name="list_styles",
        description="""List all available timeline styles with descriptions and use cases.

USE THIS TOOL WHEN:
- User asks what styles are available
- User is unsure which style to use

RETURNS: Formatted list of styles with descriptions""",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="list_themes",
        description="""List all available visual themes with descriptions.

USE THIS TOOL WHEN:
- User asks about available themes
- User wants to customize colors

RETURNS: Formatted list of themes with color descriptions""",
        inputSchema={"type": "object", "properties": {}},
    ),
]


# =============================================================================
# Server Handlers
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return all available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    """Route tool calls to appropriate handlers."""
    
    if name == "generate_timeline":
        result = generate_timeline_impl(
            config_str=arguments.get("config", ""),
            config_format=arguments.get("format", "toon"),
            output_format=arguments.get("output_format", "png"),
        )
        if result.success:
            return [
                TextContent(type="text", text=result.message),
                ImageContent(type="image", data=result.image_data, mimeType=result.mime_type),
            ]
        else:
            return [TextContent(type="text", text=result.error)]
    
    elif name == "quick_timeline":
        result = quick_timeline_impl(
            milestones=arguments.get("milestones", []),
            title=arguments.get("title", "Timeline"),
            style=arguments.get("style", "horizontal"),
            theme=arguments.get("theme", "minimal"),
            output_format=arguments.get("output_format", "png"),
            width=arguments.get("width", 1920),
            height=arguments.get("height", 800),
        )
        if result.success:
            return [
                TextContent(type="text", text=result.message),
                ImageContent(type="image", data=result.image_data, mimeType=result.mime_type),
            ]
        else:
            return [TextContent(type="text", text=result.error)]
    
    elif name == "get_config_template":
        text = get_config_template_impl(
            style=arguments.get("style", "horizontal"),
            fmt=arguments.get("format", "toon"),
        )
        return [TextContent(type="text", text=text)]
    
    elif name == "list_styles":
        return [TextContent(type="text", text=list_styles_impl())]
    
    elif name == "list_themes":
        return [TextContent(type="text", text=list_themes_impl())]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}. Available: generate_timeline, quick_timeline, get_config_template, list_styles, list_themes"
        )]


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """
    Run the standard MCP server via STDIO transport.
    
    This is the legacy entry point. For most use cases, use FastMCP instead:
        timeline-mcp (default)
    """
    import asyncio
    
    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
