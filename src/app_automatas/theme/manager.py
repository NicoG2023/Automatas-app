"""Apply centralized themes to the Qt application."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app_automatas.theme.palette import ThemePalette, get_palette
from app_automatas.theme.stylesheet import build_stylesheet


def build_qt_palette(colors: ThemePalette) -> QPalette:
    """Map semantic colors to Qt palette roles to avoid system accent leakage."""
    palette = QPalette()
    assignments = {
        QPalette.ColorRole.Window: colors.background,
        QPalette.ColorRole.WindowText: colors.text_primary,
        QPalette.ColorRole.Base: colors.surface,
        QPalette.ColorRole.AlternateBase: colors.surface_alt,
        QPalette.ColorRole.ToolTipBase: colors.surface_alt,
        QPalette.ColorRole.ToolTipText: colors.text_primary,
        QPalette.ColorRole.Text: colors.text_primary,
        QPalette.ColorRole.Button: colors.surface_alt,
        QPalette.ColorRole.ButtonText: colors.text_primary,
        QPalette.ColorRole.BrightText: "#FFFFFF",
        QPalette.ColorRole.Highlight: colors.primary,
        QPalette.ColorRole.HighlightedText: "#FFFFFF",
        QPalette.ColorRole.PlaceholderText: colors.text_secondary,
        QPalette.ColorRole.Link: colors.primary,
        QPalette.ColorRole.LinkVisited: colors.primary_pressed,
    }
    for role, color in assignments.items():
        palette.setColor(role, QColor(color))

    accent_role = getattr(QPalette.ColorRole, "Accent", None)
    if accent_role is not None:
        palette.setColor(accent_role, QColor(colors.primary))

    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor(colors.disabled_text),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(colors.disabled_text),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Button,
        QColor(colors.disabled_surface),
    )
    return palette


def apply_theme(application: QApplication, theme_name: str) -> None:
    """Apply a supported theme to every Qt component in the application."""
    colors = get_palette(theme_name)
    application.setStyle("Fusion")
    application.setPalette(build_qt_palette(colors))
    application.setStyleSheet(build_stylesheet(colors))
