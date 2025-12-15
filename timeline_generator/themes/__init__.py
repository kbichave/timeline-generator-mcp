"""Theme system for timeline styling."""

from .base import Theme
from .minimal import MinimalTheme
from .corporate import CorporateTheme
from .creative import CreativeTheme
from .dark import DarkTheme

THEMES = {
    "minimal": MinimalTheme,
    "corporate": CorporateTheme,
    "creative": CreativeTheme,
    "dark": DarkTheme,
}

__all__ = [
    "Theme",
    "MinimalTheme",
    "CorporateTheme",
    "CreativeTheme",
    "DarkTheme",
    "THEMES",
]

