"""Ocean theme - deep blues and aquatic tones."""

from dataclasses import dataclass, field

from .base import Theme, ColorPalette, FontConfig, GradientConfig


@dataclass
class OceanTheme(Theme):
    """Deep ocean theme with aquatic blue-green tones."""

    name: str = "ocean"
    display_name: str = "Ocean"

    colors: ColorPalette = field(default_factory=lambda: ColorPalette(
        background="#0B2545",
        background_alt="#13315C",
        primary="#48BFE3",
        primary_light="#72CAEA",
        primary_dark="#2596BE",
        secondary="#56CFE1",
        secondary_light="#80D9E8",
        secondary_dark="#2FB5CC",
        text_primary="#E0F0FF",
        text_secondary="#8CBAD8",
        text_light="#FFFFFF",
        success="#38B000",
        warning="#F4A261",
        error="#E76F51",
        info="#48BFE3",
        border="#1B3A5C",
        divider="#254A6E",
        shadow="rgba(0, 20, 50, 0.3)",
        accents=[
            "#48BFE3",  # Sky Blue
            "#56CFE1",  # Turquoise
            "#64DFDF",  # Teal
            "#72EFDD",  # Seafoam
            "#80FFDB",  # Aquamarine
            "#5390D9",  # Steel Blue
            "#6930C3",  # Purple
            "#7400B8",  # Violet
            "#F4A261",  # Sandy
            "#E76F51",  # Coral
            "#2A9D8F",  # Deep Teal
            "#E9C46A",  # Gold
        ],
    ))

    gradient: GradientConfig = field(default_factory=lambda: GradientConfig(
        enabled=True,
        direction="vertical",
        colors=["#0B2545", "#13315C", "#0B2545"],
        stops=[0.0, 0.5, 1.0],
    ))

    title_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Georgia", size=32.0, bold=True
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

    marker_radius: float = 10.0
    marker_border_width: float = 2.5
    line_width: float = 3.5
    connector_width: float = 2.0

    use_shadows: bool = True
    shadow_blur: float = 10.0
    shadow_offset: tuple[float, float] = (1.0, 3.0)
    corner_radius: float = 10.0

    padding: float = 18.0
    margin: float = 26.0
