"""Graphical representation of one finite automaton transition."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsPolygonItem,
    QGraphicsSimpleTextItem,
)

from app_automatas.model.transition import Transition
from app_automatas.theme.palette import get_palette
from app_automatas.view.canvas.state_item import StateItem


class TransitionItem(QGraphicsPathItem):
    """Selectable directed edge connecting two graphical states."""

    ARROW_SIZE = 11.0
    CURVE_OFFSET = 48.0
    LOOP_WIDTH = 72.0
    LOOP_HEIGHT = 92.0

    def __init__(
        self,
        transition: Transition,
        source_item: StateItem,
        target_item: StateItem,
        theme_mode: str = "light",
    ) -> None:
        super().__init__()
        self._transition = transition
        self._source_item = source_item
        self._target_item = target_item
        self._colors = get_palette(theme_mode)
        self._curved = False

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(1)

        self._arrow_item = QGraphicsPolygonItem(self)
        self._arrow_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._arrow_item.setZValue(1)

        self._label_item = QGraphicsSimpleTextItem(self)
        self._label_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._label_item.setZValue(2)

        self.sync_from_transition(transition)

    @property
    def source_id(self) -> str:
        return self._transition.source.identifier

    @property
    def target_id(self) -> str:
        return self._transition.target.identifier

    @property
    def symbols(self) -> frozenset[str]:
        return frozenset(self._transition.symbols)

    def shape(self) -> QPainterPath:
        """Provide a generous click target without drawing a thicker edge."""
        stroker = QPainterPathStroker()
        stroker.setWidth(14.0)
        return stroker.createStroke(self.path())

    def set_curved(self, curved: bool) -> None:
        """Offset the edge when the reverse directed edge also exists."""
        if self._curved == curved:
            return
        self._curved = curved
        self.update_geometry()

    def sync_from_transition(self, transition: Transition) -> None:
        """Refresh the label and edge geometry from the domain transition."""
        self._transition = transition
        self._label_item.setText(", ".join(sorted(transition.symbols)))
        self.update_geometry()

    def set_theme(self, theme_mode: str) -> None:
        self._colors = get_palette(theme_mode)
        self._apply_child_colors()
        self.update()

    def update_geometry(self) -> None:
        """Recalculate line, arrow and label after either state moves."""
        if self._source_item is self._target_item:
            path, arrow_tip, arrow_direction, label_pos = self._loop_geometry()
        else:
            path, arrow_tip, arrow_direction, label_pos = self._edge_geometry()

        self.setPath(path)
        self._arrow_item.setPolygon(self._arrow_polygon(arrow_tip, arrow_direction))
        self._label_item.setPos(label_pos)
        self._apply_child_colors()
        self.update()

    def itemChange(
        self,
        change: QGraphicsItem.GraphicsItemChange,
        value: object,
    ) -> object:  # noqa: N802 - Qt API name
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._apply_style(bool(value))
        return result

    def _edge_geometry(self) -> tuple[QPainterPath, QPointF, QPointF, QPointF]:
        source = self._source_item.pos()
        target = self._target_item.pos()
        center_vector = target - source
        distance = math.hypot(center_vector.x(), center_vector.y())
        if distance == 0:
            return self._loop_geometry()

        normal = QPointF(-center_vector.y() / distance, center_vector.x() / distance)
        midpoint = (source + target) / 2.0
        control = midpoint + normal * (self.CURVE_OFFSET if self._curved else 0.0)

        source_direction = self._normalized(control - source)
        target_direction = self._normalized(target - control)
        start = source + source_direction * StateItem.RADIUS
        end = target - target_direction * StateItem.RADIUS

        path = QPainterPath(start)
        path.quadTo(control, end)

        label_anchor = self._quadratic_point(start, control, end, 0.5)
        label_rect = self._label_item.boundingRect()
        label_pos = QPointF(
            label_anchor.x() - label_rect.width() / 2.0,
            label_anchor.y() - label_rect.height() / 2.0 - 10.0,
        )
        return path, end, target_direction, label_pos

    def _loop_geometry(self) -> tuple[QPainterPath, QPointF, QPointF, QPointF]:
        center = self._source_item.pos()
        radius = StateItem.RADIUS
        start = center + QPointF(-radius * 0.72, -radius * 0.70)
        end = center + QPointF(radius * 0.72, -radius * 0.70)
        control1 = center + QPointF(-self.LOOP_WIDTH, -self.LOOP_HEIGHT)
        control2 = center + QPointF(self.LOOP_WIDTH, -self.LOOP_HEIGHT)

        path = QPainterPath(start)
        path.cubicTo(control1, control2, end)

        direction = self._normalized(end - control2)
        label_rect = self._label_item.boundingRect()
        label_pos = QPointF(
            center.x() - label_rect.width() / 2.0,
            center.y() - self.LOOP_HEIGHT - label_rect.height() - 4.0,
        )
        return path, end, direction, label_pos

    def _arrow_polygon(self, tip: QPointF, direction: QPointF) -> QPolygonF:
        unit = self._normalized(direction)
        perpendicular = QPointF(-unit.y(), unit.x())
        base = tip - unit * self.ARROW_SIZE
        half_width = self.ARROW_SIZE * 0.55
        return QPolygonF(
            [
                tip,
                base + perpendicular * half_width,
                base - perpendicular * half_width,
            ]
        )

    def _apply_child_colors(self) -> None:
        self._apply_style(self.isSelected())

    def _apply_style(self, selected: bool) -> None:
        color = self._colors.accent if selected else self._colors.primary
        width = 3.2 if selected else 2.4
        self.setPen(
            QPen(
                QColor(color),
                width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        self._arrow_item.setPen(QPen(QColor(color), 1.0))
        self._arrow_item.setBrush(QBrush(QColor(color)))
        self._label_item.setBrush(QBrush(QColor(self._colors.text_primary)))

    @staticmethod
    def _normalized(vector: QPointF) -> QPointF:
        length = math.hypot(vector.x(), vector.y())
        if length == 0:
            return QPointF(1.0, 0.0)
        return QPointF(vector.x() / length, vector.y() / length)

    @staticmethod
    def _quadratic_point(
        start: QPointF,
        control: QPointF,
        end: QPointF,
        t: float,
    ) -> QPointF:
        inverse = 1.0 - t
        return start * (inverse * inverse) + control * (2.0 * inverse * t) + end * (t * t)
