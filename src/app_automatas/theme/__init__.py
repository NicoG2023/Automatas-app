"""Centralized visual theme system."""

from app_automatas.theme.manager import apply_theme, build_qt_palette
from app_automatas.theme.palette import DARK_PALETTE, LIGHT_PALETTE, ThemePalette, get_palette
from app_automatas.theme.stylesheet import build_stylesheet

__all__ = [
    "DARK_PALETTE",
    "LIGHT_PALETTE",
    "ThemePalette",
    "apply_theme",
    "build_qt_palette",
    "build_stylesheet",
    "get_palette",
]
