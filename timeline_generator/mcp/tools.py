"""
Timeline Generator MCP Tools - Shared Backbone
===============================================

Core tool implementations shared between FastMCP and standard MCP servers.
These are pure functions that can be called from any MCP server implementation.

Author: kbichave
Repository: https://github.com/kbichave/timeline-generator-mcp
"""

import base64
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..models import TimelineStyle, ThemeName, OutputFormat, TimelineConfig
from ..parser import parse_yaml, parse_json, parse_toon, parse_quick_milestones, create_config_from_quick
from ..themes import THEMES
from ..renderers import (
    HorizontalRenderer,
    VerticalRenderer,
    GanttRenderer,
    RoadmapRenderer,
    InfographicRenderer,
)
from ..output.image import ImageExporter
from ..output.video import VideoExporter


# =============================================================================
# Data Classes for Results
# =============================================================================

@dataclass
class TimelineResult:
    """Result of timeline generation."""
    success: bool
    message: str
    image_data: Optional[str] = None  # Base64-encoded
    mime_type: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def get_renderer(config: TimelineConfig, theme):
    """Get the appropriate renderer for the timeline style."""
    renderers = {
        TimelineStyle.HORIZONTAL: HorizontalRenderer,
        TimelineStyle.VERTICAL: VerticalRenderer,
        TimelineStyle.GANTT: GanttRenderer,
        TimelineStyle.ROADMAP: RoadmapRenderer,
        TimelineStyle.INFOGRAPHIC: InfographicRenderer,
    }
    renderer_class = renderers.get(config.style, HorizontalRenderer)
    return renderer_class(config, theme)


def get_theme(name: str):
    """Get a theme instance by name."""
    theme_class = THEMES.get(name, THEMES["minimal"])
    return theme_class()


# =============================================================================
# Configuration Templates
# =============================================================================

TOON_TEMPLATES = {
    "horizontal": '''# Horizontal Timeline (TOON format - 40% fewer tokens)
title: Project Timeline
subtitle: Key milestones
scale: monthly
style: horizontal
theme: corporate
milestones[3]: date title description highlight
2024-01-15 "Project Kickoff" "Initial planning" true
2024-03-01 "Phase 1 Complete" "Requirements done" false
2024-06-01 Launch "Go live" true
output:
  format: png
  width: 1920
  height: 800''',

    "gantt": '''# Gantt Chart (TOON format)
title: Sprint Plan
scale: weekly
style: gantt
theme: dark
milestones[3]: date title end_date progress category
2024-01-01 Planning 2024-01-14 100 "Phase 1"
2024-01-15 Development 2024-02-28 75 "Phase 1"
2024-03-01 Testing 2024-03-15 25 "Phase 2"
output:
  format: png
  width: 1920
  height: 900''',

    "vertical": '''# Vertical Timeline (TOON format)
title: Company History
scale: yearly
style: vertical
theme: minimal
milestones[3]: date title description highlight
2020-01-01 Founded "Company established" true
2021-06-01 "Series A" "$10M funding" false
2023-01-01 "100 Employees" "Growth milestone" false
output:
  format: png
  width: 1200
  height: 1600''',

    "roadmap": '''# Product Roadmap (TOON format)
title: Product Roadmap 2024
scale: quarterly
style: roadmap
theme: creative
categories[3]:
Frontend
Backend
Infrastructure
milestones[3]: date title category highlight
2024-01-01 "New Dashboard" Frontend false
2024-02-01 "API v2" Backend false
2024-03-01 "Cloud Migration" Infrastructure true
output:
  format: png
  width: 1920
  height: 1200''',

    "infographic": '''# Infographic Timeline (TOON format)
# Use badge field for custom text in circles (e.g., month names)
# Use fonts to control badge and title sizes
title: My Journey
scale: yearly
style: infographic
theme: creative
fonts:
  badge: 28
  title: 16
milestones[3]: date badge title
2020-01-01 "2020" "Started Learning"
2021-06-01 "Jun" "First Job"
2023-01-01 "Q1" "Tech Lead"
output:
  format: gif
  width: 1600
  height: 1200
  fps: 20
  duration: 5
  transparent: true''',
}

YAML_TEMPLATES = {
    "horizontal": '''title: "Project Timeline"
subtitle: "Key milestones"
scale: monthly
style: horizontal
theme: corporate
milestones:
  - date: "2024-01-15"
    title: "Project Kickoff"
    description: "Initial planning"
    highlight: true
  - date: "2024-03-01"
    title: "Phase 1 Complete"
    description: "Requirements done"
  - date: "2024-06-01"
    title: "Launch"
    description: "Go live"
    highlight: true
output:
  format: png
  width: 1920
  height: 800''',

    "gantt": '''title: "Sprint Plan"
scale: weekly
style: gantt
theme: dark
milestones:
  - date: "2024-01-01"
    title: "Planning"
    end_date: "2024-01-14"
    progress: 100
    category: "Phase 1"
  - date: "2024-01-15"
    title: "Development"
    end_date: "2024-02-28"
    progress: 75
    category: "Phase 1"
output:
  format: png
  width: 1920
  height: 900''',

    "vertical": '''title: "Company History"
scale: yearly
style: vertical
theme: minimal
milestones:
  - date: "2020-01-01"
    title: "Founded"
    description: "Company established"
    highlight: true
  - date: "2021-06-01"
    title: "Series A"
    description: "$10M funding"
output:
  format: png
  width: 1200
  height: 1600''',

    "roadmap": '''title: "Product Roadmap 2024"
scale: quarterly
style: roadmap
theme: creative
categories:
  - "Frontend"
  - "Backend"
  - "Infrastructure"
milestones:
  - date: "2024-01-01"
    title: "New Dashboard"
    category: "Frontend"
  - date: "2024-02-01"
    title: "API v2"
    category: "Backend"
output:
  format: png
  width: 1920
  height: 1200''',

    "infographic": '''title: "My Journey"
scale: yearly
style: infographic
theme: creative
fonts:
  badge: 28
  title: 16
milestones:
  - date: "2020-01-01"
    title: "Started Learning"
    badge: "2020"
  - date: "2021-06-01"
    title: "First Job"
    badge: "Jun"
    highlight: true
  - date: "2022-01-01"
    title: "Promoted"
    badge: "Q1"
output:
  format: gif
  width: 1600
  height: 1200
  transparent: true''',
}


# =============================================================================
# Tool Implementations
# =============================================================================

def generate_timeline_impl(
    config_str: str,
    config_format: str = "toon",
    output_format: str = "png",
    width: Optional[int] = None,
    height: Optional[int] = None,
    transparent: bool = False,
    accent_color: Optional[str] = None,
    fps: int = 30,
    duration: float = 5.0,
    text_wrap: Optional[bool] = None,
) -> TimelineResult:
    """
    Generate a timeline from full configuration.
    
    Args:
        config_str: Configuration in TOON, YAML, or JSON format
        config_format: Format of config_str ('toon', 'yaml', 'json')
        output_format: Output format ('png', 'gif', 'svg')
        width: Override width (optional)
        height: Override height (optional)
        transparent: Use transparent background
        accent_color: Custom accent color (hex)
        fps: Frames per second for GIF
        duration: Animation duration for GIF
        text_wrap: Enable/disable text wrapping for long titles/descriptions
        
    Returns:
        TimelineResult with success status and image data
    """
    if not config_str.strip():
        return TimelineResult(
            success=False,
            message="Configuration required",
            error="'config' parameter is required. Provide a TOON, YAML, or JSON configuration string."
        )
    
    try:
        # Parse configuration based on format
        if config_format == "json":
            config = parse_json(config_str)
        elif config_format == "toon":
            config = parse_toon(config_str)
        else:
            config = parse_yaml(config_str)
        
        # Apply overrides
        config.output.format = OutputFormat(output_format)
        if width:
            config.output.width = width
        if height:
            config.output.height = height
        if transparent:
            config.output.transparent = transparent
        if fps:
            config.output.fps = fps
        if duration:
            config.output.duration = duration
        if text_wrap is not None:
            config.text_wrap = text_wrap
        
        # Get theme and apply custom colors
        theme_instance = get_theme(config.theme.value)
        if config.colors:
            theme_instance.apply_color_overrides(config.colors)
        if accent_color:
            from ..models import ColorConfig
            if not config.colors:
                config.colors = ColorConfig()
            config.colors.accent = accent_color
            theme_instance.apply_color_overrides(config.colors)
        
        # Create renderer and generate
        renderer = get_renderer(config, theme_instance)
        
        with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        if output_format in ("png", "svg"):
            exporter = ImageExporter(renderer)
            exporter.export(tmp_path, OutputFormat(output_format))
        else:
            exporter = VideoExporter(renderer)
            exporter.export_gif(tmp_path, fps=fps, duration=duration)
        
        # Read and encode
        with open(tmp_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        tmp_path.unlink()
        
        mime_type = {
            "png": "image/png",
            "gif": "image/gif",
            "svg": "image/svg+xml"
        }[output_format]
        
        return TimelineResult(
            success=True,
            message=f"Generated {output_format.upper()} timeline: '{config.title}' with {len(config.milestones)} milestones ({config.style.value} style, {config.theme.value} theme)",
            image_data=image_data,
            mime_type=mime_type,
        )
    
    except Exception as e:
        return TimelineResult(
            success=False,
            message="Generation failed",
            error=f"Error generating timeline: {str(e)}\n\nTip: Use 'get_config_template' tool to see the correct format."
        )


def quick_timeline_impl(
    milestones: list[str],
    title: str = "Timeline",
    style: str = "horizontal",
    theme: str = "minimal",
    output_format: str = "png",
    width: int = 1920,
    height: int = 800,
    transparent: bool = False,
    accent_color: Optional[str] = None,
    fps: int = 30,
    duration: float = 5.0,
    text_wrap: bool = True,
) -> TimelineResult:
    """
    Generate a timeline quickly from inline milestones.
    
    Args:
        milestones: List of 'DATE:TITLE' strings
        title: Timeline title
        style: Timeline style
        theme: Color theme
        output_format: Output format
        width: Image width
        height: Image height
        transparent: Use transparent background
        accent_color: Custom accent color
        fps: Frames per second for GIF
        duration: Animation duration for GIF
        text_wrap: Enable text wrapping for long titles/descriptions
        
    Returns:
        TimelineResult with success status and image data
    """
    if not milestones:
        return TimelineResult(
            success=False,
            message="Milestones required",
            error="'milestones' array is required. Format: ['2024-01-01:Title', '2024-06-01:Another Title']"
        )
    
    try:
        parsed_milestones = parse_quick_milestones(milestones)
        
        config = create_config_from_quick(
            milestones=parsed_milestones,
            title=title,
            style=style,
            theme=theme,
            output_format=output_format,
            width=width,
            height=height,
            transparent=transparent,
            text_wrap=text_wrap,
        )
        
        # Apply accent color if provided
        if accent_color:
            from ..models import ColorConfig
            config.colors = ColorConfig(accent=accent_color)
        
        theme_instance = get_theme(config.theme.value)
        if config.colors:
            theme_instance.apply_color_overrides(config.colors)
        
        renderer = get_renderer(config, theme_instance)
        
        with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        if output_format in ("png", "svg"):
            exporter = ImageExporter(renderer)
            exporter.export(tmp_path, OutputFormat(output_format))
        else:
            exporter = VideoExporter(renderer)
            exporter.export_gif(tmp_path, fps=fps, duration=duration)
        
        with open(tmp_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        tmp_path.unlink()
        
        mime_type = {
            "png": "image/png",
            "gif": "image/gif",
            "svg": "image/svg+xml"
        }[output_format]
        
        return TimelineResult(
            success=True,
            message=f"Generated {style} timeline: '{title}' with {len(parsed_milestones)} milestones",
            image_data=image_data,
            mime_type=mime_type,
        )
    
    except Exception as e:
        return TimelineResult(
            success=False,
            message="Generation failed",
            error=f"Error: {str(e)}\n\nExpected format: ['YYYY-MM-DD:Title', ...]\nExample: ['2024-01-01:Project Start', '2024-06-01:Launch']"
        )


def get_config_template_impl(style: str = "horizontal", fmt: str = "toon") -> str:
    """
    Get a configuration template.
    
    Args:
        style: Timeline style
        fmt: Output format ('toon' or 'yaml')
        
    Returns:
        Template string with documentation
    """
    if fmt == "toon":
        template = TOON_TEMPLATES.get(style, TOON_TEMPLATES["horizontal"])
        format_note = "TOON format (30-60% fewer tokens than JSON)"
        code_type = ""
    else:
        template = YAML_TEMPLATES.get(style, YAML_TEMPLATES["horizontal"])
        format_note = "YAML format"
        code_type = "yaml"
    
    return f"**{style.title()} Timeline Template** ({format_note})\n\n```{code_type}\n{template}\n```\n\nUse with `generate_timeline` tool. Set format='{fmt}' parameter."


def list_styles_impl() -> str:
    """Get detailed style information."""
    return """# Available Timeline Styles

## horizontal
**Best for:** Project phases, event sequences, presentations
- Left-to-right layout
- Milestones above and below the axis
- Smart collision detection for overlapping labels
- Supports 5-15 milestones comfortably

## vertical  
**Best for:** Company history, long chronologies, resumes
- Top-to-bottom layout
- Alternating left/right cards
- Great for many milestones (10-30+)
- Ideal for scrolling views

## gantt
**Best for:** Sprint planning, project schedules, task tracking
- Duration bars with start/end dates
- Progress percentage indicators
- Category grouping
- Professional PM style

## roadmap
**Best for:** Product roadmaps, feature planning, quarterly goals
- Swimlane layout by category
- Multiple parallel tracks
- Great for showing work across teams
- Supports categories/departments

## infographic
**Best for:** Personal milestones, storytelling, social media
- Creative flowing layout
- Large visual markers
- Animated reveal works great
- Eye-catching design

---
Tip: Use `get_config_template` with a style name to see example configuration."""


def list_themes_impl() -> str:
    """Get detailed theme information."""
    return """# Available Themes

## minimal
- **Colors:** Grayscale palette
- **Style:** Clean, understated, professional
- **Best for:** Documentation, formal reports, printing

## corporate
- **Colors:** Navy blue, professional blues
- **Style:** Business-ready, trustworthy
- **Best for:** Business presentations, stakeholder updates

## creative
- **Colors:** Coral, turquoise, vibrant palette
- **Style:** Bold, energetic, playful
- **Best for:** Marketing, social media, creative projects

## dark
- **Colors:** Dark background with neon accents
- **Style:** Modern, sleek, tech-forward
- **Best for:** Developer docs, tech presentations, dark mode UIs

---
Custom Colors: Override any theme with the `colors` config:
```yaml
colors:
  accent: "#FF5733"
  background: "#1a1a2e"
  text: "#FFFFFF"
```"""

