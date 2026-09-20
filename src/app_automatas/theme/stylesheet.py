"""Qt stylesheet generation from semantic application colors."""

from __future__ import annotations

from app_automatas.theme.palette import ThemePalette


def build_stylesheet(colors: ThemePalette) -> str:
    """Build the complete application stylesheet for a palette."""
    return f"""
QMainWindow, QWidget {{
    background-color: {colors.background};
    color: {colors.text_primary};
    font-family: "Inter", "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 14px;
}}

QWidget#editorSidebar {{
    background-color: {colors.surface};
    border: 1px solid {colors.border};
    border-radius: 14px;
}}

QLabel {{
    background-color: transparent;
    color: {colors.text_primary};
}}

QLabel#secondaryText {{
    color: {colors.text_secondary};
}}

QLabel#selectedStateName {{
    color: {colors.accent};
    font-size: 16px;
    font-weight: 700;
}}

QGroupBox {{
    background-color: transparent;
    border: 1px solid {colors.border};
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px 10px 10px 10px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {colors.primary};
    background-color: {colors.surface};
}}

QComboBox, QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    min-height: 34px;
    padding: 4px 10px;
    background-color: {colors.surface};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: 8px;
    selection-background-color: {colors.primary};
    selection-color: #FFFFFF;
}}

QComboBox:hover, QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover,
QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {colors.primary_hover};
}}

QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {colors.primary};
}}

QComboBox:disabled, QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: {colors.disabled_surface};
    color: {colors.disabled_text};
}}

QComboBox::drop-down {{
    width: 28px;
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: {colors.surface};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    selection-background-color: {colors.selection};
    selection-color: {colors.text_primary};
    outline: 0;
    padding: 4px;
}}

QPushButton, QToolButton {{
    min-height: 32px;
    padding: 4px 12px;
    background-color: {colors.surface_alt};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: 8px;
    font-weight: 600;
}}

QPushButton:hover, QToolButton:hover {{
    background-color: {colors.selection};
    border-color: {colors.primary_hover};
}}

QPushButton:pressed, QToolButton:pressed {{
    background-color: {colors.primary_pressed};
    border-color: {colors.primary_pressed};
    color: #FFFFFF;
}}

QPushButton:checked, QToolButton:checked {{
    background-color: {colors.primary};
    border-color: {colors.primary};
    color: #FFFFFF;
}}

QPushButton:disabled, QToolButton:disabled {{
    background-color: {colors.disabled_surface};
    border-color: {colors.border};
    color: {colors.disabled_text};
}}

QToolBar {{
    spacing: 6px;
    padding: 8px 10px;
    background-color: {colors.surface};
    border: none;
    border-bottom: 1px solid {colors.border};
}}

QToolBar::separator {{
    width: 1px;
    margin: 6px 8px;
    background-color: {colors.border};
}}

QStatusBar {{
    background-color: {colors.surface};
    color: {colors.text_secondary};
    border-top: 1px solid {colors.border};
}}

QStatusBar::item {{
    border: none;
}}

QGraphicsView#automatonCanvas {{
    background-color: {colors.canvas};
    border: 1px solid {colors.border};
    border-radius: 14px;
}}

QScrollBar:vertical {{
    width: 12px;
    margin: 2px;
    background: transparent;
}}

QScrollBar::handle:vertical {{
    min-height: 32px;
    background: {colors.border};
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {colors.primary_hover};
}}

QScrollBar:horizontal {{
    height: 12px;
    margin: 2px;
    background: transparent;
}}

QScrollBar::handle:horizontal {{
    min-width: 32px;
    background: {colors.border};
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {colors.primary_hover};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0;
    height: 0;
    border: none;
    background: transparent;
}}

QMenuBar, QMenu {{
    background-color: {colors.surface};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
}}

QMenu::item {{
    padding: 7px 24px 7px 12px;
    border-radius: 5px;
}}

QMenu::item:selected {{
    background-color: {colors.selection};
    color: {colors.text_primary};
}}

QDialog, QMessageBox {{
    background-color: {colors.background};
    color: {colors.text_primary};
}}

QToolTip {{
    padding: 6px 8px;
    background-color: {colors.surface_alt};
    color: {colors.text_primary};
    border: 1px solid {colors.accent};
    border-radius: 6px;
}}

QCheckBox, QRadioButton {{
    spacing: 8px;
    color: {colors.text_primary};
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 17px;
    height: 17px;
    border: 1px solid {colors.border};
    background-color: {colors.surface};
}}

QCheckBox::indicator {{
    border-radius: 4px;
}}

QRadioButton::indicator {{
    border-radius: 9px;
}}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {colors.primary};
    border: 3px solid {colors.accent};
}}
"""
