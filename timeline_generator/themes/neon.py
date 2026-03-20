"""Neon theme - vibrant glowing design on dark background."""

from dataclasses import dataclass, field

from .base import Theme, ColorPalette, FontConfig, GradientConfig


@dataclass
class NeonTheme(Theme):
    """Vibrant neon theme with glowing accents on dark background."""

    name: str = "neon"
    display_name: str = "Neon"

    colors: ColorPalette = field(default_factory=lambda: ColorPalette(
        background="#0A0A1A",
        background_alt="#12122A",
        primary="#00F5FF",
        primary_light="#33F7FF",
        primary_dark="#00C4CC",
        secondary="#FF00FF",
        secondary_light="#FF33FF",
        secondary_dark="#CC00CC",
        text_primary="#E0E0FF",
        text_secondary="#8888BB",
        text_light="#FFFFFF",
        success="#00FF88",
        warning="#FFD700",
        error="#FF3366",
        info="#00F5FF",
        border="#1A1A3A",
        divider="#2A2A4A",
        shadow="rgba(0, 245, 255, 0.15)",
        accents=[
            "#00F5FF",  # Cyan
            "#FF00FF",  # Magenta
            "#00FF88",  # Green
            "#FFD700",  # Gold
            "#FF3366",  # Pink
            "#7B68EE",  # Purple
            "#FF6600",  # Orange
            "#00FFCC",  # Turquoise
            "#FF1493",  # Deep Pink
            "#ADFF2F",  # Lime
            "#FF4500",  # Red-Orange
            "#8A2BE2",  # Blue-Violet
        ],
    ))

    gradient: GradientConfig = field(default_factory=lambda: GradientConfig(
        enabled=True,
        direction="radial",
        colors=["#12122A", "#0A0A1A", "#050510"],
        stops=[0.0, 0.6, 1.0],
    ))

    title_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Menlo", size=34.0, bold=True
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

    marker_radius: float = 10.0
    marker_border_width: float = 2.5
    line_width: float = 3.0
    connector_width: float = 2.0

    use_shadows: bool = True
    shadow_blur: float = 12.0
    shadow_offset: tuple[float, float] = (0.0, 2.0)
    corner_radius: float = 10.0

    padding: float = 16.0
    margin: float = 24.0
