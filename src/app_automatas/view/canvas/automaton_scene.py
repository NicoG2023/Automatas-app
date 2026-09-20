"""Graphics scene containing automaton states and transitions."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QTransform
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsSceneMouseEvent

from app_automatas.model.state import State
from app_automatas.model.transition import Transition
from app_automatas.view.canvas.state_item import StateItem
from app_automatas.view.canvas.transition_item import TransitionItem


class AutomatonScene(QGraphicsScene):
    """Canvas model for graphical automaton items."""

    canvas_clicked = Signal(float, float)
    selected_state_changed = Signal(object)
    selected_transition_changed = Signal(object)
    state_position_changed = Signal(str, float, float)
    transition_source_changed = Signal(object)
    transition_requested = Signal(str, str)

    DEFAULT_WIDTH = 1600
    DEFAULT_HEIGHT = 1000

    def __init__(self) -> None:
        super().__init__()
        self.setSceneRect(QRectF(0, 0, self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT))
        self._state_items: dict[str, StateItem] = {}
        self._transition_items: dict[tuple[str, str], TransitionItem] = {}
        self._theme_mode = "light"
        self._editor_tool = "select"
        self._transition_source_id: str | None = None
        self.selectionChanged.connect(self._on_selection_changed)

    @property
    def theme_mode(self) -> str:
        return self._theme_mode

    @property
    def transition_source_id(self) -> str | None:
        return self._transition_source_id

    def add_state_item(self, state: State, *, select: bool = True) -> StateItem:
        """Create the graphical item corresponding to a model state."""
        if state.identifier in self._state_items:
            raise ValueError(f"State item already exists: {state.identifier}")

        item = StateItem(state, self._theme_mode)
        item.position_changed.connect(self._refresh_transitions_for_state)
        item.position_changed.connect(self.state_position_changed.emit)
        self.addItem(item)
        self._state_items[state.identifier] = item
        item.setPos(state.x, state.y)

        if select:
            self.clearSelection()
            item.setSelected(True)
        return item

    def add_or_refresh_transition(self, transition: Transition) -> TransitionItem:
        """Create one edge per state pair or refresh its grouped symbols."""
        key = (transition.source.identifier, transition.target.identifier)
        item = self._transition_items.get(key)
        if item is None:
            item = TransitionItem(
                transition,
                self.state_item(transition.source.identifier),
                self.state_item(transition.target.identifier),
                self._theme_mode,
            )
            self.addItem(item)
            self._transition_items[key] = item
        else:
            item.sync_from_transition(transition)

        self._update_pair_curvature(transition.source.identifier, transition.target.identifier)
        return item

    def rebuild_automaton(
        self,
        states: Iterable[State],
        transitions: Iterable[Transition],
        *,
        selected_state_id: str | None = None,
        selected_transition: tuple[str, str] | None = None,
    ) -> None:
        """Recreate all graphics items from the current domain model."""
        self.clear_automaton()
        for state in states:
            self.add_state_item(state, select=False)
        for transition in transitions:
            self.add_or_refresh_transition(transition)

        if selected_state_id is not None and selected_state_id in self._state_items:
            self._state_items[selected_state_id].setSelected(True)
        elif selected_transition is not None:
            transition_item = self._transition_items.get(selected_transition)
            if transition_item is not None:
                transition_item.setSelected(True)

    def clear_automaton(self) -> None:
        """Remove all editor items while keeping scene configuration intact."""
        self._transition_source_id = None
        self.clearSelection()
        for item in tuple(self._transition_items.values()):
            if item.scene() is self:
                self.removeItem(item)
        for item in tuple(self._state_items.values()):
            if item.scene() is self:
                self.removeItem(item)
        self._transition_items.clear()
        self._state_items.clear()
        self.transition_source_changed.emit(None)
        self.selected_state_changed.emit(None)
        self.selected_transition_changed.emit(None)

    def state_item(self, identifier: str) -> StateItem:
        try:
            return self._state_items[identifier]
        except KeyError as exc:
            raise KeyError(f"Unknown graphical state: {identifier}") from exc

    def transition_item(self, source_id: str, target_id: str) -> TransitionItem:
        try:
            return self._transition_items[(source_id, target_id)]
        except KeyError as exc:
            raise KeyError(f"Unknown graphical transition: {source_id} -> {target_id}") from exc

    def refresh_state(self, state: State) -> None:
        self.state_item(state.identifier).sync_from_state(state)

    def refresh_states(self, states: Iterable[State]) -> None:
        for state in states:
            if state.identifier in self._state_items:
                self._state_items[state.identifier].sync_from_state(state)

    def set_editor_tool(self, editor_tool: str) -> None:
        """Update scene behavior and cancel incomplete transition creation."""
        if editor_tool not in {"select", "state", "transition"}:
            raise ValueError(f"Unsupported editor tool: {editor_tool}")
        self._editor_tool = editor_tool
        if editor_tool != "transition":
            self.cancel_transition_selection()

    def cancel_transition_selection(self) -> None:
        if self._transition_source_id is None:
            return
        self._transition_source_id = None
        self.clearSelection()
        self.transition_source_changed.emit(None)

    def set_theme(self, theme_mode: str) -> None:
        self._theme_mode = theme_mode
        for item in self._state_items.values():
            item.set_theme(theme_mode)
        for item in self._transition_items.values():
            item.set_theme(theme_mode)
        self.update()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._editor_tool == "transition":
            state_item = self._state_item_at(event.scenePos())
            if state_item is None:
                self.cancel_transition_selection()
                event.accept()
                return
            self._handle_transition_state_click(state_item)
            event.accept()
            return

        clicked_empty_space = (
            event.button() == Qt.MouseButton.LeftButton
            and self.itemAt(event.scenePos(), QTransform()) is None
        )
        position = event.scenePos()
        super().mousePressEvent(event)
        if clicked_empty_space:
            self.canvas_clicked.emit(position.x(), position.y())

    def _handle_transition_state_click(self, item: StateItem) -> None:
        if self._transition_source_id is None:
            self._transition_source_id = item.state_id
            self.clearSelection()
            item.setSelected(True)
            self.transition_source_changed.emit(item.state_id)
            return

        source_id = self._transition_source_id
        target_id = item.state_id
        self._transition_source_id = None
        self.clearSelection()
        self.transition_source_changed.emit(None)
        self.transition_requested.emit(source_id, target_id)

    def _state_item_at(self, position: object) -> StateItem | None:
        item = self.itemAt(position, QTransform())
        current: QGraphicsItem | None = item
        while current is not None:
            if isinstance(current, StateItem):
                return current
            current = current.parentItem()
        return None

    def _refresh_transitions_for_state(self, identifier: str, x: float, y: float) -> None:
        del x, y
        for (source_id, target_id), transition_item in self._transition_items.items():
            if identifier in {source_id, target_id}:
                transition_item.update_geometry()

    def _update_pair_curvature(self, source_id: str, target_id: str) -> None:
        if source_id == target_id:
            return
        direct = self._transition_items.get((source_id, target_id))
        reverse = self._transition_items.get((target_id, source_id))
        if direct is not None:
            direct.set_curved(reverse is not None)
        if reverse is not None:
            reverse.set_curved(direct is not None)

    def _on_selection_changed(self) -> None:
        selected_state = next(
            (item for item in self.selectedItems() if isinstance(item, StateItem)),
            None,
        )
        selected_transition = next(
            (item for item in self.selectedItems() if isinstance(item, TransitionItem)),
            None,
        )

        self.selected_state_changed.emit(
            selected_state.state_id if selected_state is not None else None
        )
        self.selected_transition_changed.emit(
            (selected_transition.source_id, selected_transition.target_id)
            if selected_transition is not None
            else None
        )
