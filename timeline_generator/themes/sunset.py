"""Sunset theme - warm gradient with golden and amber tones."""

from dataclasses import dataclass, field

from .base import Theme, ColorPalette, FontConfig, GradientConfig


@dataclass
class SunsetTheme(Theme):
    """Warm sunset theme with golden hour colors."""

    name: str = "sunset"
    display_name: str = "Sunset"

    colors: ColorPalette = field(default_factory=lambda: ColorPalette(
        background="#1A0A2E",
        background_alt="#2D1B4E",
        primary="#FF6B35",
        primary_light="#FF8F5E",
        primary_dark="#E04A14",
        secondary="#F7C948",
        secondary_light="#F9D66E",
        secondary_dark="#D4A82C",
        text_primary="#FFE8D6",
        text_secondary="#C8A882",
        text_light="#FFFFFF",
        success="#A7C957",
        warning="#F7C948",
        error="#FF4444",
        info="#6C63FF",
        border="#3D2B5A",
        divider="#4E3B6E",
        shadow="rgba(20, 5, 35, 0.3)",
        accents=[
            "#FF6B35",  # Orange
            "#F7C948",  # Gold
            "#FF4365",  # Crimson
            "#6C63FF",  # Indigo
            "#A7C957",  # Lime
            "#FF8C42",  # Tangerine
            "#E84855",  # Red
            "#FFB627",  # Amber
            "#C77DFF",  # Violet
            "#FF6392",  # Rose
            "#2EC4B6",  # Teal
            "#FF9F1C",  # Marigold
        ],
    ))

    gradient: GradientConfig = field(default_factory=lambda: GradientConfig(
        enabled=True,
        direction="vertical",
        colors=["#2D1B4E", "#1A0A2E", "#0F0620"],
        stops=[0.0, 0.6, 1.0],
    ))

    title_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Georgia", size=34.0, bold=True
    ))
    subtitle_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Georgia", size=17.0, italic=True
    ))
    label_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Arial", size=14.0, bold=True
    ))
    description_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Arial", size=12.0
    ))
    date_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Arial", size=11.0
    ))

    marker_radius: float = 10.0
    marker_border_width: float = 2.5
    line_width: float = 4.0
    connector_width: float = 2.0

    use_shadows: bool = True
    shadow_blur: float = 10.0
    shadow_offset: tuple[float, float] = (2.0, 3.0)
    corner_radius: float = 10.0

    padding: float = 18.0
    margin: float = 26.0
