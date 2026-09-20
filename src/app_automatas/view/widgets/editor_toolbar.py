"""Primary toolbar for automaton editing actions."""

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QToolBar


class EditorToolBar(QToolBar):
    """Expose the primary automaton editing actions."""

    tool_changed = Signal(str)
    theme_changed = Signal(str)
    clear_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Herramientas")
        self.setObjectName("editorToolbar")
        self.setMovable(False)

        self._tool_group = QActionGroup(self)
        self._tool_group.setExclusive(True)
        self.select_action = self._add_tool_action("Seleccionar", "select")
        self.add_state_action = self._add_tool_action("Estado", "state")
        self.add_transition_action = self._add_tool_action("Transición", "transition")
        self.select_action.setChecked(True)

        self.addSeparator()
        self.clear_action = QAction("Limpiar", self)
        self.clear_action.setToolTip("Eliminar todo el autómata actual")
        self.clear_action.triggered.connect(self.clear_requested.emit)
        self.addAction(self.clear_action)

        self.addSeparator()
        self.theme_action = QAction("Modo oscuro", self)
        self.theme_action.setCheckable(True)
        self.theme_action.setToolTip("Alternar entre el tema claro y el tema oscuro")
        self.theme_action.toggled.connect(self._on_theme_toggled)
        self.addAction(self.theme_action)

    def _add_tool_action(self, text: str, editor_tool: str) -> QAction:
        action = QAction(text, self)
        action.setCheckable(True)
        action.setProperty("editorTool", editor_tool)
        tooltips = {
            "select": "Seleccionar y mover estados o transiciones",
            "state": "Crear estados haciendo clic en el lienzo",
            "transition": "Crear una transición seleccionando origen y destino",
        }
        action.setToolTip(tooltips[editor_tool])
        action.triggered.connect(
            lambda checked, tool=editor_tool: self._on_tool_triggered(tool, checked)
        )
        self._tool_group.addAction(action)
        self.addAction(action)
        return action

    def _on_tool_triggered(self, editor_tool: str, checked: bool) -> None:
        if checked:
            self.tool_changed.emit(editor_tool)

    def _on_theme_toggled(self, checked: bool) -> None:
        self.theme_changed.emit("dark" if checked else "light")

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
        self.theme_action.setChecked(theme_mode == "dark")
        self.theme_action.blockSignals(previous_state)
