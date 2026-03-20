"""Theme system for timeline styling."""

from .base import Theme, GradientConfig
from .minimal import MinimalTheme
from .corporate import CorporateTheme
from .creative import CreativeTheme
from .dark import DarkTheme
from .neon import NeonTheme
from .pastel import PastelTheme
from .ocean import OceanTheme
from .sunset import SunsetTheme

THEMES = {
    "minimal": MinimalTheme,
    "corporate": CorporateTheme,
    "creative": CreativeTheme,
    "dark": DarkTheme,
    "neon": NeonTheme,
    "pastel": PastelTheme,
    "ocean": OceanTheme,
    "sunset": SunsetTheme,
}

__all__ = [
    "Theme",
    "GradientConfig",
    "MinimalTheme",
    "CorporateTheme",
    "CreativeTheme",
    "DarkTheme",
    "NeonTheme",
    "PastelTheme",
    "OceanTheme",
    "SunsetTheme",
    "THEMES",
]
