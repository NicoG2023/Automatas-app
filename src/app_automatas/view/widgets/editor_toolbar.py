"""Primary toolbar for automaton editing actions."""

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar


class EditorToolBar(QToolBar):
    """Expose the editor actions that later patches will implement."""

    theme_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__("Herramientas")
        self.setObjectName("editorToolbar")
        self.setMovable(False)

        self.select_action = self._add_placeholder_action("Seleccionar")
        self.add_state_action = self._add_placeholder_action("Estado")
        self.add_transition_action = self._add_placeholder_action("Transición")

        self.addSeparator()
        self.clear_action = self._add_placeholder_action("Limpiar")

        self.addSeparator()
        self.theme_action = QAction("Modo oscuro", self)
        self.theme_action.setCheckable(True)
        self.theme_action.setToolTip("Alternar entre el tema claro y el tema oscuro")
        self.theme_action.toggled.connect(self._on_theme_toggled)
        self.addAction(self.theme_action)

    def _add_placeholder_action(self, text: str) -> QAction:
        action = QAction(text, self)
        action.setEnabled(False)
        self.addAction(action)
        return action

    def _on_theme_toggled(self, checked: bool) -> None:
        self.theme_changed.emit("dark" if checked else "light")

    def set_theme(self, theme_mode: str) -> None:
        """Reflect the active theme without emitting another change request."""
        previous_state = self.theme_action.blockSignals(True)
        self.theme_action.setChecked(theme_mode == "dark")
        self.theme_action.blockSignals(previous_state)
