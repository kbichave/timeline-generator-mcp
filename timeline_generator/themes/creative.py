"""Creative theme - bold colors and playful design."""

from dataclasses import dataclass, field

from .base import Theme, ColorPalette, FontConfig


@dataclass
class CreativeTheme(Theme):
    """Bold, creative theme with vibrant colors."""
    
    name: str = "creative"
    display_name: str = "Creative"
    
    colors: ColorPalette = field(default_factory=lambda: ColorPalette(
        background="#FFF8E7",
        background_alt="#FFE4B5",
        primary="#FF6B6B",
        primary_light="#FF8E8E",
        primary_dark="#E74C3C",
        secondary="#4ECDC4",
        secondary_light="#7EE8E2",
        secondary_dark="#2EAD9A",
        text_primary="#2C3E50",
        text_secondary="#5D6D7E",
        text_light="#FFFFFF",
        success="#2ECC71",
        warning="#F39C12",
        error="#E74C3C",
        info="#3498DB",
        border="#D5DBDB",
        divider="#AEB6BF",
        shadow="rgba(255, 107, 107, 0.2)",
        accents=[
            "#FF6B6B",  # Coral
            "#4ECDC4",  # Turquoise
            "#FFE66D",  # Yellow
            "#95E1D3",  # Mint
            "#F38181",  # Salmon
            "#AA96DA",  # Lavender
            "#FCBAD3",  # Pink
            "#A8D8EA",  # Sky Blue
            "#FFB347",  # Orange
            "#77DD77",  # Pastel Green
            "#FF85A2",  # Rose
            "#89CFF0",  # Baby Blue
        ],
    ))
    
    title_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Comic Sans MS", size=38.0, bold=True
    ))
    subtitle_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Arial", size=18.0, italic=True
    ))
    label_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Arial", size=15.0, bold=True
    ))
    description_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Arial", size=13.0
    ))
    date_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Arial", size=12.0, bold=True
    ))
    
    marker_radius: float = 14.0
    marker_border_width: float = 3.0
    line_width: float = 5.0
    connector_width: float = 2.5
    
    use_shadows: bool = True
    shadow_blur: float = 8.0
    shadow_offset: tuple[float, float] = (4.0, 4.0)
    corner_radius: float = 16.0
    
    padding: float = 20.0
    margin: float = 30.0

