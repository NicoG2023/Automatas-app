"""Centralized color palettes for the application themes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ThemePalette:
    """Semantic colors shared by every application component."""

    background: str
    surface: str
    surface_alt: str
    canvas: str
    border: str
    text_primary: str
    text_secondary: str
    primary: str
    primary_hover: str
    primary_pressed: str
    accent: str
    accent_hover: str
    success: str
    warning: str
    error: str
    selection: str
    disabled_surface: str
    disabled_text: str


LIGHT_PALETTE = ThemePalette(
    background="#F6F1FA",
    surface="#F1EAF8",
    surface_alt="#E9DDF5",
    canvas="#FCFAFD",
    border="#D1C1E0",
    text_primary="#241A2B",
    text_secondary="#6E6476",
    primary="#6F3FA0",
    primary_hover="#7E4CAF",
    primary_pressed="#5B2F88",
    accent="#C99A2E",
    accent_hover="#B7861E",
    success="#2F7D57",
    warning="#A66A16",
    error="#A33A46",
    selection="#E9DCF4",
    disabled_surface="#E8E1EC",
    disabled_text="#9A909F",
)

DARK_PALETTE = ThemePalette(
    background="#17121C",
    surface="#211929",
    surface_alt="#2B2134",
    canvas="#1B1521",
    border="#493A55",
    text_primary="#F4EEF8",
    text_secondary="#C2B5C9",
    primary="#A66BDD",
    primary_hover="#B47CE8",
    primary_pressed="#8A54BE",
    accent="#D8B456",
    accent_hover="#E2C36C",
    success="#62B789",
    warning="#D49A45",
    error="#D86A76",
    selection="#443052",
    disabled_surface="#31283A",
    disabled_text="#817488",
)

PALETTES: dict[str, ThemePalette] = {
    "light": LIGHT_PALETTE,
    "dark": DARK_PALETTE,
}


def get_palette(theme_name: str) -> ThemePalette:
    """Return a palette by name, rejecting unknown themes explicitly."""
    try:
        return PALETTES[theme_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported theme: {theme_name}") from exc
