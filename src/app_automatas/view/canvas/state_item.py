"""Graphical representation of one finite automaton state."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QStyleOptionGraphicsItem,
    QWidget,
)

from app_automatas.model.state import State
from app_automatas.theme.palette import ThemePalette, get_palette


class StateItem(QGraphicsObject):
    """Movable and selectable canvas item backed by a model state."""

    position_changed = Signal(str, float, float)

    RADIUS = 32.0
    ACCEPTING_INSET = 6.0
    INITIAL_ARROW_LENGTH = 28.0
    INITIAL_ARROW_HEAD = 8.0
    BOUNDING_MARGIN = 6.0

    def __init__(self, state: State, theme_mode: str = "light") -> None:
        super().__init__()
        self._identifier = state.identifier
        self._is_initial = state.is_initial
        self._is_accepting = state.is_accepting
        self._colors = get_palette(theme_mode)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setZValue(10)
        self.setToolTip(state.identifier)

    @property
    def state_id(self) -> str:
        return self._identifier

    @property
    def is_initial(self) -> bool:
        return self._is_initial

    @property
    def is_accepting(self) -> bool:
        return self._is_accepting

    def boundingRect(self) -> QRectF:  # noqa: N802 - Qt API name
        left = -self.RADIUS - self.INITIAL_ARROW_LENGTH - self.BOUNDING_MARGIN
        top = -self.RADIUS - self.BOUNDING_MARGIN
        right = self.RADIUS + self.BOUNDING_MARGIN
        bottom = self.RADIUS + self.BOUNDING_MARGIN
        return QRectF(left, top, right - left, bottom - top)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addEllipse(self._state_rect())
        return path

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        del option, widget
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outline = self._colors.accent if self.isSelected() else self._colors.primary
        fill = self._colors.selection if self.isSelected() else self._colors.surface
        state_pen = QPen(QColor(outline), 3.0)
        painter.setPen(state_pen)
        painter.setBrush(QBrush(QColor(fill)))
        painter.drawEllipse(self._state_rect())

        if self._is_accepting:
            inner_rect = self._state_rect().adjusted(
                self.ACCEPTING_INSET,
                self.ACCEPTING_INSET,
                -self.ACCEPTING_INSET,
                -self.ACCEPTING_INSET,
            )
            painter.setPen(QPen(QColor(outline), 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(inner_rect)

        if self._is_initial:
            self._draw_initial_arrow(painter)

        painter.setPen(QPen(QColor(self._colors.text_primary)))
        painter.drawText(
            self._state_rect(),
            Qt.AlignmentFlag.AlignCenter,
            self._identifier,
        )

    def sync_from_state(self, state: State) -> None:
        """Refresh visual flags after the model state changes."""
        if state.identifier != self._identifier:
            self._identifier = state.identifier
            self.setToolTip(state.identifier)
        self._is_initial = state.is_initial
        self._is_accepting = state.is_accepting
        self.update()

    def set_theme(self, theme_mode: str) -> None:
        self._colors = get_palette(theme_mode)
        self.update()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:  # noqa: N802
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            value = self._clamp_position(value)
        result = super().itemChange(change, value)

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            position = self.pos()
            self.position_changed.emit(
                self._identifier,
                position.x(),
                position.y(),
            )
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()

        return result

    def _state_rect(self) -> QRectF:
        diameter = self.RADIUS * 2.0
        return QRectF(-self.RADIUS, -self.RADIUS, diameter, diameter)

    def _clamp_position(self, value: object) -> QPointF:
        if not isinstance(value, QPointF) or self.scene() is None:
            return self.pos()

        scene_rect = self.scene().sceneRect()
        bounds = self.boundingRect()
        minimum_x = scene_rect.left() - bounds.left()
        maximum_x = scene_rect.right() - bounds.right()
        minimum_y = scene_rect.top() - bounds.top()
        maximum_y = scene_rect.bottom() - bounds.bottom()
        return QPointF(
            min(max(value.x(), minimum_x), maximum_x),
            min(max(value.y(), minimum_y), maximum_y),
        )

    def _draw_initial_arrow(self, painter: QPainter) -> None:
        arrow_end = QPointF(-self.RADIUS - 3.0, 0.0)
        arrow_start = QPointF(
            arrow_end.x() - self.INITIAL_ARROW_LENGTH,
            arrow_end.y(),
        )
        painter.setPen(QPen(QColor(self._colors.accent), 3.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(arrow_start, arrow_end)
        painter.drawLine(
            arrow_end,
            QPointF(
                arrow_end.x() - self.INITIAL_ARROW_HEAD,
                arrow_end.y() - self.INITIAL_ARROW_HEAD / 1.5,
            ),
        )
        painter.drawLine(
            arrow_end,
            QPointF(
                arrow_end.x() - self.INITIAL_ARROW_HEAD,
                arrow_end.y() + self.INITIAL_ARROW_HEAD / 1.5,
            ),
        )
