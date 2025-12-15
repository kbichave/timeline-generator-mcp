"""Corporate theme - professional and business-focused."""

from dataclasses import dataclass, field

from .base import Theme, ColorPalette, FontConfig


@dataclass
class CorporateTheme(Theme):
    """Professional corporate theme with blue tones."""
    
    name: str = "corporate"
    display_name: str = "Corporate"
    
    colors: ColorPalette = field(default_factory=lambda: ColorPalette(
        background="#FFFFFF",
        background_alt="#F0F4F8",
        primary="#1E3A5F",
        primary_light="#2E5A8F",
        primary_dark="#0D1F33",
        secondary="#4A90D9",
        secondary_light="#7AB8F5",
        secondary_dark="#2A70B9",
        text_primary="#1A1A2E",
        text_secondary="#4A5568",
        text_light="#FFFFFF",
        success="#28A745",
        warning="#FFC107",
        error="#DC3545",
        info="#17A2B8",
        border="#CBD5E0",
        divider="#A0AEC0",
        shadow="rgba(30, 58, 95, 0.15)",
        accents=[
            "#1E3A5F",  # Navy
            "#4A90D9",  # Corporate Blue
            "#2E7D32",  # Forest Green
            "#6B21A8",  # Purple
            "#0891B2",  # Teal
            "#B45309",  # Bronze
            "#BE185D",  # Magenta
            "#059669",  # Emerald
        ],
    ))
    
    title_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Georgia", size=34.0, bold=True
    ))
    subtitle_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Georgia", size=18.0, italic=True
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
    shadow_blur: float = 6.0
    shadow_offset: tuple[float, float] = (3.0, 3.0)
    corner_radius: float = 6.0
    
    padding: float = 18.0
    margin: float = 28.0

