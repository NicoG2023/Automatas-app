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

QWidget#centralArea {{
    background-color: {colors.background};
}}

QScrollArea#sidebarScrollArea {{
    background-color: {colors.surface};
    border: 1px solid {colors.border};
    border-radius: 16px;
}}

QScrollArea#sidebarScrollArea > QWidget > QWidget,
QScrollArea#sidebarScrollArea QWidget#qt_scrollarea_viewport {{
    background-color: {colors.surface};
    border-radius: 16px;
}}

QWidget#editorSidebar {{
    background-color: {colors.surface};
    border: none;
    border-radius: 14px;
}}

QLabel {{
    background-color: transparent;
    color: {colors.text_primary};
}}

QLabel#secondaryText {{
    color: {colors.text_secondary};
}}

QLabel#selectedStateName, QLabel#selectedTransitionName {{
    color: {colors.accent};
    font-size: 16px;
    font-weight: 700;
}}

QGroupBox {{
    background-color: transparent;
    border: 1px solid {colors.border};
    border-radius: 12px;
    margin-top: 16px;
    padding: 18px 12px 12px 12px;
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
    min-height: 36px;
    padding: 4px 10px;
    background-color: {colors.canvas};
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
    min-height: 36px;
    padding: 6px 12px;
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
    spacing: 8px;
    padding: 10px 12px;
    background-color: {colors.surface_alt};
    border: none;
    border-bottom: 1px solid {colors.border};
}}

QToolBar::separator {{
    width: 1px;
    margin: 6px 8px;
    background-color: {colors.border};
}}

QToolBar QToolButton {{
    min-width: 48px;
    min-height: 48px;
    padding: 5px;
    border-radius: 10px;
}}

QWidget#toolbarSpacer {{
    background-color: transparent;
    border: none;
}}

QStatusBar {{
    background-color: {colors.surface};
    color: {colors.text_secondary};
    border-top: 1px solid {colors.border};
}}

QStatusBar::item {{
    border: none;
}}


QWidget#simulationPanel {{
    background-color: {colors.surface};
    border: 1px solid {colors.border};
    border-radius: 14px;
}}

QLabel#simulationTitle, QLabel#conversionTitle, QLabel#conversionTableTitle, QLabel#conversionProcessTitle, QLabel#regularExpressionProcessTitle {{
    color: {colors.primary};
    font-size: 16px;
    font-weight: 700;
}}

QWidget#conversionTablePanel {{
    background-color: {colors.surface};
    border: 1px solid {colors.border};
    border-radius: 14px;
}}

QSplitter#conversionSplitter::handle {{
    width: 8px;
    background-color: transparent;
}}

QTableWidget#conversionTransitionTable {{
    background-color: {colors.canvas};
    alternate-background-color: {colors.surface_alt};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: 10px;
    gridline-color: {colors.border};
    selection-background-color: {colors.selection};
    selection-color: {colors.text_primary};
}}

QTableWidget#conversionTransitionTable QHeaderView::section {{
    background-color: {colors.surface_alt};
    color: {colors.primary};
    border: none;
    border-right: 1px solid {colors.border};
    border-bottom: 1px solid {colors.border};
    padding: 8px 10px;
    font-weight: 700;
}}

QTableWidget#conversionTransitionTable::item {{
    padding: 7px 9px;
}}

QTableWidget#conversionProcessOriginalTable,
QTableWidget#conversionProcessExpandedTable,
QTableWidget#conversionProcessRenamedTable {{
    background-color: {colors.canvas};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: 10px;
    gridline-color: {colors.border};
}}

QTableWidget#conversionProcessOriginalTable QHeaderView::section,
QTableWidget#conversionProcessExpandedTable QHeaderView::section,
QTableWidget#conversionProcessRenamedTable QHeaderView::section {{
    background-color: {colors.surface_alt};
    color: {colors.primary};
    border: none;
    border-right: 1px solid {colors.border};
    border-bottom: 1px solid {colors.border};
    padding: 16px 24px;
    font-weight: 700;
    font-size: 22px;
}}

QTableWidget#conversionProcessOriginalTable::item,
QTableWidget#conversionProcessExpandedTable::item,
QTableWidget#conversionProcessRenamedTable::item {{
    padding: 18px 28px;
    font-size: 21px;
}}

QLabel#conversionMappingText {{
    padding: 10px 12px;
    background-color: {colors.surface_alt};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: 9px;
}}

QLabel#conversionReachabilityNote {{
    padding: 10px 12px;
    background-color: {colors.selection};
    color: {colors.primary};
    border: 1px solid {colors.border};
    border-radius: 9px;
    font-weight: 600;
}}

QPushButton#conversionProcessButton,
QPushButton#conversionProcessPrimaryButton {{
    background-color: {colors.primary};
    border-color: {colors.primary};
    color: #FFFFFF;
}}

QPushButton#conversionProcessButton:hover,
QPushButton#conversionProcessPrimaryButton:hover {{
    background-color: {colors.primary_hover};
    border-color: {colors.primary_hover};
}}

QTextBrowser#regularExpressionInitialSystem,
QTextBrowser#regularExpressionSubstitutionStep,
QTextBrowser#regularExpressionArdenStep,
QTextBrowser#regularExpressionFinalResult,
QTextBrowser#regularExpressionSummary {{
    padding: 18px;
    background-color: {colors.canvas};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: 12px;
    font-size: 17px;
}}

QTextBrowser#regularExpressionFinalResult {{
    border: 2px solid {colors.accent};
}}

QPushButton#regularExpressionProcessPrimaryButton {{
    background-color: {colors.primary};
    border-color: {colors.primary};
    color: #FFFFFF;
}}

QPushButton#regularExpressionProcessPrimaryButton:hover {{
    background-color: {colors.primary_hover};
    border-color: {colors.primary_hover};
}}

QPushButton#regularExpressionSummaryButton {{
    color: {colors.primary};
    background-color: {colors.selection};
    border-color: {colors.border};
}}

QPushButton#regularExpressionSummaryButton:hover {{
    background-color: {colors.surface_alt};
    border-color: {colors.primary};
}}

QLabel#simulationResult {{
    padding: 5px 10px;
    border-radius: 8px;
    font-weight: 700;
    background-color: {colors.surface_alt};
    color: {colors.text_secondary};
}}

QLabel#simulationResult[simulationStatus="ready"],
QLabel#simulationResult[simulationStatus="running"] {{
    color: {colors.primary};
    background-color: {colors.selection};
}}

QLabel#simulationResult[simulationStatus="accepted"] {{
    color: {colors.success};
    background-color: {colors.surface_alt};
}}

QLabel#simulationResult[simulationStatus="rejected"] {{
    color: {colors.error};
    background-color: {colors.surface_alt};
}}

QLabel#simulationValue {{
    min-height: 24px;
    padding: 4px 8px;
    border: 1px solid {colors.border};
    border-radius: 7px;
    background-color: {colors.canvas};
    color: {colors.text_primary};
}}

QPushButton#simulationPrimaryButton {{
    background-color: {colors.primary};
    border-color: {colors.primary};
    color: #FFFFFF;
}}

QPushButton#simulationPrimaryButton:hover {{
    background-color: {colors.primary_hover};
    border-color: {colors.primary_hover};
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
    background-color: transparent;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 17px;
    height: 17px;
    border: 1px solid {colors.border};
    background-color: {colors.canvas};
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
