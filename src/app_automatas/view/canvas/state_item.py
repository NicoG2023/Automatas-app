"""Graphical representation of one finite automaton state."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFontMetricsF, QPainter, QPainterPath, QPen
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
        self._simulation_role: str | None = None
        self._simulation_phase = False

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

    @property
    def simulation_active(self) -> bool:
        """Report whether the state is highlighted as part of the live/success path."""
        return self._simulation_role == "active"

    @property
    def simulation_role(self) -> str | None:
        return self._simulation_role

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

        if self._simulation_role == "active":
            outline = self._colors.success
            fill = self._colors.selection if self._simulation_phase else self._colors.surface
            width = 5.2 if self._simulation_phase else 4.2
        elif self._simulation_role == "success":
            outline = self._colors.success
            fill = self._colors.surface
            width = 4.2
        elif self._simulation_role == "failed":
            outline = self._colors.error
            fill = self._colors.surface_alt
            width = 4.0
        elif self.isSelected():
            outline = self._colors.accent
            fill = self._colors.selection
            width = 3.0
        else:
            outline = self._colors.primary
            fill = self._colors.surface
            width = 3.0
        state_pen = QPen(QColor(outline), width)
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
            painter.setPen(QPen(QColor(outline), 2.0 if self._simulation_role != "active" else 2.6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(inner_rect)

        if self._is_initial:
            self._draw_initial_arrow(painter)

        painter.setPen(QPen(QColor(self._colors.text_primary)))
        font = painter.font()
        metrics = QFontMetricsF(font)
        available_width = self.RADIUS * 2.0 - 12.0
        if metrics.horizontalAdvance(self._identifier) > available_width:
            original_size = font.pointSizeF() if font.pointSizeF() > 0 else 10.0
            ratio = available_width / metrics.horizontalAdvance(self._identifier)
            font.setPointSizeF(max(6.5, original_size * ratio))
            painter.setFont(font)
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

    def set_simulation_role(self, role: str | None) -> None:
        """Apply an active, successful, failed or neutral simulation style."""
        if role not in {None, "active", "success", "failed"}:
            raise ValueError(f"Unsupported simulation role: {role}")

        if role == "active":
            self._simulation_phase = (
                not self._simulation_phase
                if self._simulation_role == "active"
                else True
            )
        else:
            self._simulation_phase = False

        if self._simulation_role == role and role != "active":
            return

        self._simulation_role = role
        self.update()

    def set_simulation_active(self, active: bool) -> None:
        """Backward-compatible helper for the original single-highlight API."""
        self.set_simulation_role("active" if active else None)

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
        arrow_color = self._colors.error if self._simulation_role == "failed" else (self._colors.success if self._simulation_role in {"active", "success"} else self._colors.accent)
        arrow_end = QPointF(-self.RADIUS - 3.0, 0.0)
        arrow_start = QPointF(
            arrow_end.x() - self.INITIAL_ARROW_LENGTH,
            arrow_end.y(),
        )
        painter.setPen(QPen(QColor(arrow_color), 3.0))
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
