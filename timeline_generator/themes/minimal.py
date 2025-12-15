"""Minimal theme - clean and simple."""

from dataclasses import dataclass, field

from .base import Theme, ColorPalette, FontConfig


@dataclass
class MinimalTheme(Theme):
    """Clean, minimal theme with subtle colors and clean lines."""
    
    name: str = "minimal"
    display_name: str = "Minimal"
    
    colors: ColorPalette = field(default_factory=lambda: ColorPalette(
        background="#FFFFFF",
        background_alt="#FAFAFA",
        primary="#333333",
        primary_light="#666666",
        primary_dark="#111111",
        secondary="#888888",
        secondary_light="#AAAAAA",
        secondary_dark="#666666",
        text_primary="#222222",
        text_secondary="#666666",
        text_light="#FFFFFF",
        success="#2E7D32",
        warning="#F9A825",
        error="#C62828",
        info="#1565C0",
        border="#E8E8E8",
        divider="#D0D0D0",
        shadow="rgba(0, 0, 0, 0.05)",
        accents=[
            "#333333",
            "#555555",
            "#777777",
            "#999999",
            "#BBBBBB",
            "#444444",
            "#666666",
            "#888888",
        ],
    ))
    
    title_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Helvetica", size=28.0, bold=False
    ))
    subtitle_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Helvetica", size=16.0, italic=False
    ))
    label_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Helvetica", size=13.0, bold=False
    ))
    description_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Helvetica", size=11.0
    ))
    date_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Helvetica", size=10.0
    ))
    
    marker_radius: float = 6.0
    marker_border_width: float = 1.5
    line_width: float = 2.0
    connector_width: float = 1.0
    
    use_shadows: bool = False
    corner_radius: float = 4.0
    
    padding: float = 12.0
    margin: float = 20.0

