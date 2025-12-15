"""Dark theme - modern dark mode design."""

from dataclasses import dataclass, field

from .base import Theme, ColorPalette, FontConfig


@dataclass
class DarkTheme(Theme):
    """Modern dark theme with neon accents."""
    
    name: str = "dark"
    display_name: str = "Dark"
    
    colors: ColorPalette = field(default_factory=lambda: ColorPalette(
        background="#0D1117",
        background_alt="#161B22",
        primary="#58A6FF",
        primary_light="#79C0FF",
        primary_dark="#388BFD",
        secondary="#F78166",
        secondary_light="#FFA198",
        secondary_dark="#EA6045",
        text_primary="#E6EDF3",
        text_secondary="#8B949E",
        text_light="#FFFFFF",
        success="#3FB950",
        warning="#D29922",
        error="#F85149",
        info="#58A6FF",
        border="#30363D",
        divider="#21262D",
        shadow="rgba(0, 0, 0, 0.4)",
        accents=[
            "#58A6FF",  # Blue
            "#F78166",  # Orange
            "#3FB950",  # Green
            "#A371F7",  # Purple
            "#DB61A2",  # Pink
            "#79C0FF",  # Light Blue
            "#FFA657",  # Amber
            "#7EE787",  # Light Green
            "#D2A8FF",  # Lavender
            "#FF7B72",  # Red
            "#56D4DD",  # Cyan
            "#FFDCD7",  # Peach
        ],
    ))
    
    title_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Menlo", size=32.0, bold=True
    ))
    subtitle_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Menlo", size=16.0, italic=False
    ))
    label_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Menlo", size=13.0, bold=True
    ))
    description_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Menlo", size=11.0
    ))
    date_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Menlo", size=10.0
    ))
    
    marker_radius: float = 8.0
    marker_border_width: float = 2.0
    line_width: float = 3.0
    connector_width: float = 1.5
    
    use_shadows: bool = True
    shadow_blur: float = 10.0
    shadow_offset: tuple[float, float] = (0.0, 4.0)
    corner_radius: float = 8.0
    
    padding: float = 16.0
    margin: float = 24.0

