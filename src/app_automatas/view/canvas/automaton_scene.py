"""Graphics scene containing automaton states and, later, transitions."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QTransform
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent

from app_automatas.model.state import State
from app_automatas.view.canvas.state_item import StateItem


class AutomatonScene(QGraphicsScene):
    """Canvas model for graphical automaton items."""

    canvas_clicked = Signal(float, float)
    selected_state_changed = Signal(object)
    state_position_changed = Signal(str, float, float)

    DEFAULT_WIDTH = 1600
    DEFAULT_HEIGHT = 1000

    def __init__(self) -> None:
        super().__init__()
        self.setSceneRect(QRectF(0, 0, self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT))
        self._state_items: dict[str, StateItem] = {}
        self._theme_mode = "light"
        self.selectionChanged.connect(self._on_selection_changed)

    @property
    def theme_mode(self) -> str:
        return self._theme_mode

    def add_state_item(self, state: State, *, select: bool = True) -> StateItem:
        """Create the graphical item corresponding to a model state."""
        if state.identifier in self._state_items:
            raise ValueError(f"State item already exists: {state.identifier}")

        item = StateItem(state, self._theme_mode)
        item.position_changed.connect(self.state_position_changed.emit)
        self.addItem(item)
        self._state_items[state.identifier] = item
        item.setPos(state.x, state.y)

        if select:
            self.clearSelection()
            item.setSelected(True)
        return item

    def state_item(self, identifier: str) -> StateItem:
        try:
            return self._state_items[identifier]
        except KeyError as exc:
            raise KeyError(f"Unknown graphical state: {identifier}") from exc

    def refresh_state(self, state: State) -> None:
        self.state_item(state.identifier).sync_from_state(state)

    def refresh_states(self, states: Iterable[State]) -> None:
        for state in states:
            if state.identifier in self._state_items:
                self._state_items[state.identifier].sync_from_state(state)

    def set_theme(self, theme_mode: str) -> None:
        self._theme_mode = theme_mode
        for item in self._state_items.values():
            item.set_theme(theme_mode)
        self.update()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        clicked_empty_space = (
            event.button() == Qt.MouseButton.LeftButton
            and self.itemAt(event.scenePos(), QTransform()) is None
        )
        position = event.scenePos()
        super().mousePressEvent(event)
        if clicked_empty_space:
            self.canvas_clicked.emit(position.x(), position.y())

    def _on_selection_changed(self) -> None:
        selected_state = next(
            (
                item
                for item in self.selectedItems()
                if isinstance(item, StateItem)
            ),
            None,
        )
        self.selected_state_changed.emit(
            selected_state.state_id if selected_state is not None else None
        )
