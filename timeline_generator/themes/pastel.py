"""Pastel theme - soft, friendly colors."""

from dataclasses import dataclass, field

from .base import Theme, ColorPalette, FontConfig, GradientConfig


@dataclass
class PastelTheme(Theme):
    """Soft pastel theme with gentle colors and rounded shapes."""

    name: str = "pastel"
    display_name: str = "Pastel"

    colors: ColorPalette = field(default_factory=lambda: ColorPalette(
        background="#FFF5F5",
        background_alt="#FFF0F0",
        primary="#F4A4A4",
        primary_light="#F7C4C4",
        primary_dark="#E88888",
        secondary="#A4C8F4",
        secondary_light="#C4D8F7",
        secondary_dark="#88B0E8",
        text_primary="#4A4A6A",
        text_secondary="#8888AA",
        text_light="#FFFFFF",
        success="#A4E8B8",
        warning="#F4D8A4",
        error="#F4A4A4",
        info="#A4C8F4",
        border="#E8E0E0",
        divider="#D8D0D0",
        shadow="rgba(100, 80, 80, 0.08)",
        accents=[
            "#F4A4A4",  # Rose
            "#A4C8F4",  # Sky
            "#A4E8B8",  # Mint
            "#F4D8A4",  # Peach
            "#C8A4F4",  # Lavender
            "#A4F4E8",  # Aqua
            "#F4A4D8",  # Pink
            "#D8F4A4",  # Lime
            "#F4C8A4",  # Apricot
            "#A4A4F4",  # Periwinkle
            "#E8A4F4",  # Orchid
            "#A4F4C8",  # Seafoam
        ],
    ))

    gradient: GradientConfig = field(default_factory=lambda: GradientConfig(
        enabled=True,
        direction="vertical",
        colors=["#FFF5F5", "#F5F0FF", "#F0F5FF"],
        stops=[0.0, 0.5, 1.0],
    ))

    title_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Georgia", size=30.0, bold=True
    ))
    subtitle_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Georgia", size=16.0, italic=True
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

    marker_radius: float = 12.0
    marker_border_width: float = 2.5
    line_width: float = 3.5
    connector_width: float = 2.0

    use_shadows: bool = True
    shadow_blur: float = 8.0
    shadow_offset: tuple[float, float] = (2.0, 3.0)
    corner_radius: float = 14.0

    padding: float = 18.0
    margin: float = 26.0
