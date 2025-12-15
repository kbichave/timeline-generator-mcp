"""Base theme class defining the theme interface."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FontConfig:
    """Font configuration."""
    
    family: str = "Sans"
    size: float = 14.0
    bold: bool = False
    italic: bool = False


@dataclass
class ColorPalette:
    """Color palette for a theme."""
    
    # Background colors
    background: str = "#FFFFFF"
    background_alt: str = "#F5F5F5"
    
    # Primary colors
    primary: str = "#2196F3"
    primary_light: str = "#64B5F6"
    primary_dark: str = "#1976D2"
    
    # Secondary colors
    secondary: str = "#FF9800"
    secondary_light: str = "#FFB74D"
    secondary_dark: str = "#F57C00"
    
    # Text colors
    text_primary: str = "#212121"
    text_secondary: str = "#757575"
    text_light: str = "#FFFFFF"
    
    # Semantic colors
    success: str = "#4CAF50"
    warning: str = "#FFC107"
    error: str = "#F44336"
    info: str = "#2196F3"
    
    # Neutral colors
    border: str = "#E0E0E0"
    divider: str = "#BDBDBD"
    shadow: str = "rgba(0, 0, 0, 0.1)"
    
    # Accent colors for milestones
    accents: list[str] = field(default_factory=lambda: [
        "#E91E63",  # Pink
        "#9C27B0",  # Purple
        "#673AB7",  # Deep Purple
        "#3F51B5",  # Indigo
        "#2196F3",  # Blue
        "#00BCD4",  # Cyan
        "#009688",  # Teal
        "#4CAF50",  # Green
        "#8BC34A",  # Light Green
        "#CDDC39",  # Lime
        "#FFC107",  # Amber
        "#FF9800",  # Orange
    ])
    
    def get_accent(self, index: int) -> str:
        """Get an accent color by index (cycles through available accents)."""
        return self.accents[index % len(self.accents)]


@dataclass
class Theme:
    """Base theme configuration."""
    
    name: str = "base"
    display_name: str = "Base Theme"
    
    # Colors
    colors: ColorPalette = field(default_factory=ColorPalette)
    
    # Typography
    title_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Sans", size=32.0, bold=True
    ))
    subtitle_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Sans", size=18.0, italic=True
    ))
    label_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Sans", size=14.0, bold=True
    ))
    description_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Sans", size=12.0
    ))
    date_font: FontConfig = field(default_factory=lambda: FontConfig(
        family="Sans", size=11.0
    ))
    
    # Shapes and sizes
    marker_radius: float = 8.0
    marker_border_width: float = 2.0
    line_width: float = 3.0
    connector_width: float = 1.5
    
    # Effects
    use_shadows: bool = True
    shadow_blur: float = 4.0
    shadow_offset: tuple[float, float] = (2.0, 2.0)
    corner_radius: float = 8.0
    
    # Spacing
    padding: float = 16.0
    margin: float = 24.0
    
    # Animation (for GIF generation)
    animation_duration: float = 0.5  # Per element
    animation_easing: str = "ease-out"
    
    def hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
        """Convert hex color to RGBA tuple (0-1 range for Cairo)."""
        if hex_color.startswith("rgba"):
            # Parse rgba string
            import re
            match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)", hex_color)
            if match:
                r, g, b, a = match.groups()
                return int(r) / 255, int(g) / 255, int(b) / 255, float(a)
        
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            return r, g, b, alpha
        return 0, 0, 0, alpha
    
    def apply_font(self, ctx, font_config: FontConfig) -> None:
        """Apply font configuration to Cairo context."""
        import cairo
        
        slant = cairo.FONT_SLANT_ITALIC if font_config.italic else cairo.FONT_SLANT_NORMAL
        weight = cairo.FONT_WEIGHT_BOLD if font_config.bold else cairo.FONT_WEIGHT_NORMAL
        
        ctx.select_font_face(font_config.family, slant, weight)
        ctx.set_font_size(font_config.size)
    
    def apply_color_overrides(self, color_config) -> None:
        """Apply custom color overrides from config.
        
        Args:
            color_config: ColorConfig object with optional color overrides.
        """
        if color_config is None:
            return
        
        if color_config.background:
            self.colors.background = color_config.background
            self.colors.background_alt = color_config.background
        if color_config.text:
            self.colors.text_primary = color_config.text
        if color_config.accent:
            self.colors.primary = color_config.accent
            self.colors.primary_light = color_config.accent
            self.colors.primary_dark = color_config.accent
        if color_config.secondary:
            self.colors.secondary = color_config.secondary
        if color_config.highlight:
            self.colors.warning = color_config.highlight
        if color_config.axis:
            self.colors.border = color_config.axis
            self.colors.divider = color_config.axis

