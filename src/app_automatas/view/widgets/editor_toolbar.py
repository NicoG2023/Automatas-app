"""Primary toolbar for automaton editing actions."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QSizePolicy, QToolBar, QToolTip, QWidget

from app_automatas.theme.palette import ThemePalette, get_palette


class EditorToolBar(QToolBar):
    """Expose the primary automaton editing actions as compact icon buttons."""

    tool_changed = Signal(str)
    theme_changed = Signal(str)
    clear_requested = Signal()
    validation_requested = Signal()
    conversion_requested = Signal()
    regular_expression_requested = Signal()
    regular_expression_to_nfa_requested = Signal()
    open_requested = Signal()
    save_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Herramientas")
        self.setObjectName("editorToolbar")
        self.setMovable(False)
        self.setIconSize(QSize(30, 30))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._theme_mode = "light"

        self._tool_group = QActionGroup(self)
        self._tool_group.setExclusive(True)

        colors = get_palette(self._theme_mode)
        self.open_action = QAction(_create_open_icon(colors), "Abrir", self)
        self.open_action.setShortcut("Ctrl+O")
        self._configure_action_help(
            self.open_action,
            "Abrir — carga un autómata guardado en formato JSON (Ctrl+O).",
        )
        self.open_action.triggered.connect(self.open_requested.emit)
        self.addAction(self.open_action)
        self._enable_immediate_tooltip(self.open_action)

        self.save_action = QAction(_create_save_icon(colors), "Guardar", self)
        self.save_action.setShortcut("Ctrl+S")
        self._configure_action_help(
            self.save_action,
            "Guardar — guarda el autómata actual en formato JSON (Ctrl+S).",
        )
        self.save_action.triggered.connect(self.save_requested.emit)
        self.addAction(self.save_action)
        self._enable_immediate_tooltip(self.save_action)
        self.addSeparator()

        self.select_action = self._add_tool_action(
            "Seleccionar",
            "select",
            _create_select_icon(colors),
            "Seleccionar — selecciona y mueve estados o transiciones.",
        )
        self.add_state_action = self._add_tool_action(
            "Estado",
            "state",
            _create_state_icon(colors),
            "Estado — crea un nuevo estado al hacer clic en el lienzo.",
        )
        self.add_transition_action = self._add_tool_action(
            "Transición",
            "transition",
            _create_transition_icon(colors),
            "Transición — crea una transición eligiendo primero origen y luego destino.",
        )
        self.select_action.setChecked(True)

        self.addSeparator()
        self.convert_action = QAction(_create_convert_icon(colors), "Convertir AFN a AFD", self)
        self._configure_action_help(
            self.convert_action,
            "Convertir — genera un AFD equivalente mediante construcción de subconjuntos.",
        )
        self.convert_action.triggered.connect(self.conversion_requested.emit)
        self.convert_action.setEnabled(False)
        self.addAction(self.convert_action)
        self._enable_immediate_tooltip(self.convert_action)

        self.regex_action = QAction(
            _create_regex_icon(colors),
            "Autómata a expresión regular",
            self,
        )
        self._configure_action_help(
            self.regex_action,
            "Expresión regular — obtiene paso a paso una expresión equivalente mediante ecuaciones y el lema de Arden.",
        )
        self.regex_action.triggered.connect(self.regular_expression_requested.emit)
        self.addAction(self.regex_action)
        self._enable_immediate_tooltip(self.regex_action)

        self.regex_to_nfa_action = QAction(
            _create_regex_icon(colors),
            "Expresión regular a AFN-λ",
            self,
        )
        self._configure_action_help(
            self.regex_to_nfa_action,
            "Expresión a AFN-λ — aplica inductivamente la parte 1 del teorema de "
            "Kleene y muestra las transiciones vacías λ.",
        )
        self.regex_to_nfa_action.triggered.connect(
            self.regular_expression_to_nfa_requested.emit
        )
        self.addAction(self.regex_to_nfa_action)
        self._enable_immediate_tooltip(self.regex_to_nfa_action)

        self.validate_action = QAction(_create_validate_icon(colors), "Validar", self)
        self._configure_action_help(
            self.validate_action,
            "Validar — comprueba que el autómata esté listo para simular.",
        )
        self.validate_action.triggered.connect(self.validation_requested.emit)
        self.addAction(self.validate_action)
        self._enable_immediate_tooltip(self.validate_action)

        self.clear_action = QAction(_create_clear_icon(colors), "Limpiar", self)
        self._configure_action_help(
            self.clear_action,
            "Limpiar — elimina el autómata actual después de pedir confirmación.",
        )
        self.clear_action.triggered.connect(self.clear_requested.emit)
        self.addAction(self.clear_action)
        self._enable_immediate_tooltip(self.clear_action)

        spacer = QWidget(self)
        spacer.setObjectName("toolbarSpacer")
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        self.theme_action = QAction(_create_theme_icon(False, colors), "Tema", self)
        self.theme_action.setCheckable(True)
        self._configure_action_help(
            self.theme_action,
            "Tema — alterna entre el modo claro y el modo oscuro.",
        )
        self.theme_action.toggled.connect(self._on_theme_toggled)
        self.addAction(self.theme_action)
        self._enable_immediate_tooltip(self.theme_action)

    def _add_tool_action(
        self,
        text: str,
        editor_tool: str,
        icon: QIcon,
        help_text: str,
    ) -> QAction:
        action = QAction(icon, text, self)
        action.setCheckable(True)
        action.setProperty("editorTool", editor_tool)
        self._configure_action_help(action, help_text)
        action.triggered.connect(
            lambda checked, tool=editor_tool: self._on_tool_triggered(tool, checked)
        )
        self._tool_group.addAction(action)
        self.addAction(action)
        self._enable_immediate_tooltip(action)
        return action

    @staticmethod
    def _configure_action_help(action: QAction, text: str) -> None:
        action.setToolTip(text)
        action.setStatusTip(text)

    def _enable_immediate_tooltip(self, action: QAction) -> None:
        button = self.widgetForAction(action)
        if button is not None:
            button.installEventFilter(self)

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        """Show toolbar help immediately instead of waiting for the native delay."""
        if isinstance(watched, QWidget):
            if event.type() == QEvent.Type.Enter and watched.toolTip():
                QToolTip.showText(
                    watched.mapToGlobal(QPoint(watched.width() // 2, watched.height())),
                    watched.toolTip(),
                    watched,
                )
            elif event.type() == QEvent.Type.Leave:
                QToolTip.hideText()
        return super().eventFilter(watched, event)

    def _on_tool_triggered(self, editor_tool: str, checked: bool) -> None:
        if checked:
            self.tool_changed.emit(editor_tool)

    def _on_theme_toggled(self, checked: bool) -> None:
        self._theme_mode = "dark" if checked else "light"
        self._refresh_icons()
        self.theme_changed.emit(self._theme_mode)

    def _refresh_icons(self) -> None:
        colors = get_palette(self._theme_mode)
        self.open_action.setIcon(_create_open_icon(colors))
        self.save_action.setIcon(_create_save_icon(colors))
        self.select_action.setIcon(_create_select_icon(colors))
        self.add_state_action.setIcon(_create_state_icon(colors))
        self.add_transition_action.setIcon(_create_transition_icon(colors))
        self.convert_action.setIcon(_create_convert_icon(colors))
        self.regex_action.setIcon(_create_regex_icon(colors))
        self.validate_action.setIcon(_create_validate_icon(colors))
        self.clear_action.setIcon(_create_clear_icon(colors))
        self.theme_action.setIcon(
            _create_theme_icon(self._theme_mode == "dark", colors)
        )

    def set_conversion_available(self, available: bool) -> None:
        """Enable AFN→AFD conversion only while editing an AFN."""
        self.convert_action.setEnabled(available)

    def set_editor_tool(self, editor_tool: str) -> None:
        """Reflect the active editor tool without emitting another request."""
        actions = {
            "select": self.select_action,
            "state": self.add_state_action,
            "transition": self.add_transition_action,
        }
        try:
            action = actions[editor_tool]
        except KeyError as exc:
            raise ValueError(f"Unsupported editor tool: {editor_tool}") from exc
        previous_state = action.blockSignals(True)
        action.setChecked(True)
        action.blockSignals(previous_state)

    def set_theme(self, theme_mode: str) -> None:
        """Reflect the active theme without emitting another change request."""
        previous_state = self.theme_action.blockSignals(True)
        self._theme_mode = theme_mode
        checked = theme_mode == "dark"
        self.theme_action.setChecked(checked)
        self._refresh_icons()
        self.theme_action.blockSignals(previous_state)


def _icon_canvas() -> tuple[QPixmap, QPainter]:
    pixmap = QPixmap(36, 36)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    return pixmap, painter


def _finish_icon(pixmap: QPixmap, painter: QPainter) -> QIcon:
    painter.end()
    return QIcon(pixmap)



def _create_open_icon(colors: ThemePalette) -> QIcon:
    pixmap, painter = _icon_canvas()
    painter.setPen(QPen(QColor(colors.accent), 2.3))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(5, 11, 26, 18), 3, 3)
    painter.drawLine(QPointF(8, 11), QPointF(12, 7))
    painter.drawLine(QPointF(12, 7), QPointF(19, 7))
    painter.drawLine(QPointF(19, 7), QPointF(22, 11))
    painter.drawLine(QPointF(9, 25), QPointF(27, 16))
    return _finish_icon(pixmap, painter)


def _create_save_icon(colors: ThemePalette) -> QIcon:
    pixmap, painter = _icon_canvas()
    painter.setPen(QPen(QColor(colors.accent), 2.3))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(7, 5, 22, 26), 3, 3)
    painter.drawRect(QRectF(11, 7, 12, 7))
    painter.drawRoundedRect(QRectF(11, 20, 14, 8), 2, 2)
    return _finish_icon(pixmap, painter)

def _create_select_icon(colors: ThemePalette) -> QIcon:
    pixmap, painter = _icon_canvas()
    painter.setPen(QPen(QColor(colors.accent), 1.8))
    painter.setBrush(QColor(colors.accent))
    path = QPainterPath()
    path.moveTo(8, 6)
    path.lineTo(27, 19)
    path.lineTo(19.2, 20.5)
    path.lineTo(25, 30)
    path.lineTo(20.8, 32)
    path.lineTo(15.3, 22.5)
    path.lineTo(9, 28)
    path.closeSubpath()
    painter.drawPath(path)
    return _finish_icon(pixmap, painter)


def _create_state_icon(colors: ThemePalette) -> QIcon:
    pixmap, painter = _icon_canvas()
    painter.setPen(QPen(QColor(colors.accent), 3.0))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QRectF(8, 8, 20, 20))
    return _finish_icon(pixmap, painter)


def _create_transition_icon(colors: ThemePalette) -> QIcon:
    pixmap, painter = _icon_canvas()
    pen = QPen(QColor(colors.accent), 2.6)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QRectF(4, 14, 7, 7))
    painter.drawEllipse(QRectF(25, 14, 7, 7))
    painter.drawLine(QPointF(11, 17.5), QPointF(26, 17.5))
    arrow = QPainterPath()
    arrow.moveTo(26, 17.5)
    arrow.lineTo(21.5, 13.7)
    arrow.moveTo(26, 17.5)
    arrow.lineTo(21.5, 21.3)
    painter.drawPath(arrow)
    return _finish_icon(pixmap, painter)


def _create_convert_icon(colors: ThemePalette) -> QIcon:
    """Create a subset-construction icon for AFN to AFD conversion."""
    pixmap, painter = _icon_canvas()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(colors.accent), 2.2))
    painter.drawEllipse(QRectF(3.5, 8.5, 11, 11))
    painter.drawEllipse(QRectF(7.5, 16.0, 11, 11))

    painter.setPen(QPen(QColor(colors.primary), 2.4))
    painter.drawLine(QPointF(17.5, 18), QPointF(26, 18))
    arrow = QPainterPath()
    arrow.moveTo(26, 18)
    arrow.lineTo(22, 14.5)
    arrow.moveTo(26, 18)
    arrow.lineTo(22, 21.5)
    painter.drawPath(arrow)

    painter.setPen(QPen(QColor(colors.success), 2.6))
    painter.drawEllipse(QRectF(25, 9, 8, 18))
    return _finish_icon(pixmap, painter)


def _create_regex_icon(colors: ThemePalette) -> QIcon:
    """Create an icon for automaton-to-regular-expression conversion."""
    pixmap, painter = _icon_canvas()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(colors.accent), 2.2))
    painter.drawEllipse(QRectF(3.5, 10.5, 10, 10))
    painter.drawEllipse(QRectF(9.5, 20.0, 8, 8))

    painter.setPen(QPen(QColor(colors.primary), 2.4))
    painter.drawLine(QPointF(16, 18), QPointF(24, 18))
    arrow = QPainterPath()
    arrow.moveTo(24, 18)
    arrow.lineTo(20.5, 14.8)
    arrow.moveTo(24, 18)
    arrow.lineTo(20.5, 21.2)
    painter.drawPath(arrow)

    painter.setPen(QPen(QColor(colors.success), 2.0))
    painter.drawLine(QPointF(26, 12), QPointF(31, 12))
    painter.drawLine(QPointF(26, 18), QPointF(33, 18))
    painter.drawLine(QPointF(26, 24), QPointF(30, 24))
    return _finish_icon(pixmap, painter)


def _create_validate_icon(colors: ThemePalette) -> QIcon:
    """Create a check icon for structural automaton validation."""
    pixmap, painter = _icon_canvas()
    pen = QPen(QColor(colors.success), 3.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QRectF(6, 6, 24, 24))
    check = QPainterPath()
    check.moveTo(11, 18)
    check.lineTo(16, 23)
    check.lineTo(26, 13)
    painter.drawPath(check)
    return _finish_icon(pixmap, painter)


def _create_clear_icon(colors: ThemePalette) -> QIcon:
    """Create a trash-can icon for the destructive clear action."""
    pixmap, painter = _icon_canvas()
    pen = QPen(QColor(colors.error), 2.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    painter.drawLine(QPointF(10, 11), QPointF(26, 11))
    painter.drawLine(QPointF(14, 8), QPointF(22, 8))
    painter.drawLine(QPointF(16, 8), QPointF(17, 6))
    painter.drawLine(QPointF(20, 6), QPointF(21, 8))
    painter.drawRoundedRect(QRectF(12, 13, 12, 16), 2.2, 2.2)
    painter.drawLine(QPointF(16, 17), QPointF(16, 25))
    painter.drawLine(QPointF(20, 17), QPointF(20, 25))
    return _finish_icon(pixmap, painter)


def _create_theme_icon(is_dark: bool, colors: ThemePalette) -> QIcon:
    pixmap, painter = _icon_canvas()
    if is_dark:
        painter.setPen(QPen(QColor(colors.accent), 2.0))
        painter.setBrush(QColor(colors.accent))
        painter.drawEllipse(QRectF(13, 13, 10, 10))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        center = QPointF(18, 18)
        for dx, dy in (
            (0, -9),
            (6.4, -6.4),
            (9, 0),
            (6.4, 6.4),
            (0, 9),
            (-6.4, 6.4),
            (-9, 0),
            (-6.4, -6.4),
        ):
            start = QPointF(center.x() + dx * 0.72, center.y() + dy * 0.72)
            end = QPointF(center.x() + dx, center.y() + dy)
            painter.drawLine(start, end)
    else:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(colors.primary))
        painter.drawEllipse(QRectF(9, 8, 20, 20))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.drawEllipse(QRectF(16, 5, 18, 20))
    return _finish_icon(pixmap, painter)
