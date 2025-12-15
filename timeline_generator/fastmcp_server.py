"""
Timeline Generator FastMCP Server
=================================

The default MCP server for Timeline Generator, built with FastMCP.
Supports both STDIO (for Cursor/Claude) and HTTP (for web/persistent) transports.

Usage:
    # STDIO mode (default) - for Cursor, Claude Desktop
    timeline-mcp
    
    # HTTP mode - persistent server
    timeline-mcp-http
    
    # Direct uvicorn (production)
    uvicorn timeline_generator.fastmcp_server:http_app --host 0.0.0.0 --port 8000
    
    # With uvx (zero-install)
    uvx timeline-generator-mcp

Author: kbichave
Repository: https://github.com/kbichave/timeline-generator-mcp
"""

from typing import Annotated

from fastmcp import FastMCP

from .mcp.tools import (
    generate_timeline_impl,
    quick_timeline_impl,
    get_config_template_impl,
    list_styles_impl,
    list_themes_impl,
)


# =============================================================================
# FastMCP Server Instance
# =============================================================================

mcp = FastMCP("timeline-generator-mcp")


# =============================================================================
# Tool Definitions
# =============================================================================

@mcp.tool()
def generate_timeline(
    config: Annotated[str, "Timeline configuration in TOON (recommended), YAML, or JSON format. Must include 'milestones' with date and title."],
    format: Annotated[str, "Config format: 'toon' (default, 30-60% fewer tokens), 'yaml', or 'json'"] = "toon",
    output_format: Annotated[str, "Output format: 'png', 'gif', or 'svg'"] = "png",
) -> str:
    """
    Generate a timeline visualization from configuration.

    RECOMMENDED: Use TOON format for 30-60% token savings vs JSON.

    Example TOON config:
    ```
    title: Project Roadmap
    style: horizontal
    theme: corporate
    milestones[2]: date title highlight
    2024-01-15 Kickoff true
    2024-06-01 Launch false
    ```

    Returns: Base64-encoded image with metadata.
    """
    result = generate_timeline_impl(
        config_str=config,
        config_format=format,
        output_format=output_format,
    )
    
    if result.success:
        return f"{result.message}\n\ndata:{result.mime_type};base64,{result.image_data}"
    else:
        return f"Error: {result.error}"


@mcp.tool()
def quick_timeline(
    milestones: Annotated[list[str], "List of milestones in 'DATE:Title' format"],
    title: Annotated[str, "Timeline title"] = "Timeline",
    style: Annotated[str, "Style: horizontal, vertical, gantt, roadmap, infographic"] = "horizontal",
    theme: Annotated[str, "Theme: minimal, corporate, creative, dark"] = "minimal",
    output_format: Annotated[str, "Output format: png, gif, svg"] = "png",
    width: Annotated[int, "Image width in pixels"] = 1920,
    height: Annotated[int, "Image height in pixels"] = 800,
) -> str:
    """
    Quickly generate a timeline from a list of milestones.

    Example:
        quick_timeline(["2024-01-01:Start", "2024-06-01:Launch"])

    Returns: Base64-encoded image with metadata.
    """
    result = quick_timeline_impl(
        milestones=milestones,
        title=title,
        style=style,
        theme=theme,
        output_format=output_format,
        width=width,
        height=height,
    )
    
    if result.success:
        return f"{result.message}\n\ndata:{result.mime_type};base64,{result.image_data}"
    else:
        return f"Error: {result.error}"


@mcp.tool()
def get_config_template(
    style: Annotated[str, "Style: horizontal, vertical, gantt, roadmap, infographic"] = "horizontal",
    format: Annotated[str, "Format: 'toon' (token-efficient) or 'yaml'"] = "toon",
) -> str:
    """
    Get a starter configuration template for timeline generation.

    Returns template in TOON (default, 30-60% fewer tokens) or YAML format.
    """
    return get_config_template_impl(style=style, fmt=format)


@mcp.tool()
def list_styles() -> str:
    """List all available timeline styles with descriptions and use cases."""
    return list_styles_impl()


@mcp.tool()
def list_themes() -> str:
    """List all available visual themes with descriptions."""
    return list_themes_impl()


# =============================================================================
# ASGI HTTP App for uvicorn
# =============================================================================

# Create HTTP app for uvicorn deployment
# Usage: uvicorn timeline_generator.fastmcp_server:http_app --host 0.0.0.0 --port 8000
http_app = mcp.http_app(path="/mcp")


# =============================================================================
# Entry Points
# =============================================================================

def main():
    """
    Run the MCP server in STDIO mode (default).
    
    This is the entry point for:
    - Cursor: timeline-mcp in mcp.json
    - Claude Desktop: timeline-mcp
    - uvx: uvx timeline-generator-mcp
    """
    mcp.run()


def main_http(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the MCP server in HTTP mode for persistent deployment.
    
    This is the entry point for:
    - Web API access
    - Persistent server deployment
    - Production with uvicorn
    
    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to listen on (default: 8000)
    """
    import uvicorn
    
    print(f"Starting Timeline Generator MCP Server (HTTP mode)")
    print(f"Server: http://{host}:{port}/mcp")
    print(f"Health: http://{host}:{port}/health")
    print()
    
    uvicorn.run(
        http_app,
        host=host,
        port=port,
        log_level="info",
    )


def main_sse(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the MCP server in SSE (Server-Sent Events) mode.
    
    This is an alternative transport for clients that prefer SSE.
    """
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()
