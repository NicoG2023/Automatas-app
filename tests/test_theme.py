import pytest

from app_automatas.theme.palette import DARK_PALETTE, LIGHT_PALETTE, get_palette
from app_automatas.theme.stylesheet import build_stylesheet


def test_palette_lookup_returns_supported_themes() -> None:
    assert get_palette("light") is LIGHT_PALETTE
    assert get_palette("dark") is DARK_PALETTE


def test_palette_lookup_rejects_unknown_theme() -> None:
    with pytest.raises(ValueError, match="Unsupported theme"):
        get_palette("sepia")


def test_stylesheet_uses_primary_and_accent_colors() -> None:
    stylesheet = build_stylesheet(LIGHT_PALETTE)

    assert LIGHT_PALETTE.primary in stylesheet
    assert LIGHT_PALETTE.accent in stylesheet
    assert LIGHT_PALETTE.canvas in stylesheet
