"""Top-level controller for the automaton editor."""

from __future__ import annotations

from PySide6.QtCore import QObject

from app_automatas.model.editor_session import EditorSession
from app_automatas.view.main_window import MainWindow


class AppController(QObject):
    """Coordinate the editor model and main window."""

    def __init__(self, model: EditorSession, view: MainWindow) -> None:
        super().__init__()
        self._model = model
        self._view = view

        self._view.automaton_type_changed.connect(self._on_automaton_type_changed)
        self._view.editor_tool_changed.connect(self._on_editor_tool_changed)
        self._view.theme_changed.connect(self._on_theme_changed)
        self._view.canvas_clicked.connect(self._on_canvas_clicked)
        self._view.state_selected.connect(self._on_state_selected)
        self._view.state_moved.connect(self._on_state_moved)
        self._view.state_initial_changed.connect(self._on_state_initial_changed)
        self._view.state_accepting_changed.connect(self._on_state_accepting_changed)
        self._sync_view()

    def show(self) -> None:
        """Display the main window."""
        self._view.show()

    def _sync_view(self) -> None:
        self._view.set_automaton_type(self._model.automaton_type)
        self._view.set_theme(self._model.theme_mode)
        self._view.set_editor_tool(self._model.editor_tool)
        self._view.show_status(f"Modo de edición: {self._model.automaton_type}")

    def _on_automaton_type_changed(self, automaton_type: str) -> None:
        try:
            self._model.set_automaton_type(automaton_type)
        except ValueError:
            self._view.set_automaton_type(self._model.automaton_type)
            self._view.show_status(
                "No se puede cambiar el tipo mientras el autómata tenga estados"
            )
            return
        self._view.show_status(f"Modo de edición: {self._model.automaton_type}")

    def _on_editor_tool_changed(self, editor_tool: str) -> None:
        self._model.set_editor_tool(editor_tool)
        self._view.set_editor_tool(self._model.editor_tool)
        label = "Seleccionar" if editor_tool == "select" else "Estado"
        self._view.show_status(f"Herramienta activa: {label}")

    def _on_theme_changed(self, theme_mode: str) -> None:
        self._model.set_theme_mode(theme_mode)
        self._view.set_theme(self._model.theme_mode)
        theme_label = "oscuro" if self._model.theme_mode == "dark" else "claro"
        self._view.show_status(f"Tema {theme_label} activado")

    def _on_canvas_clicked(self, x: float, y: float) -> None:
        if self._model.editor_tool != "state":
            return
        state = self._model.automaton.add_state(x=x, y=y)
        self._view.add_state(state)
        self._view.show_status(f"Estado {state.identifier} creado")

    def _on_state_selected(self, identifier: object) -> None:
        if identifier is None:
            self._view.show_selected_state(None)
            return
        if not isinstance(identifier, str):
            return
        state = self._model.automaton.get_state(identifier)
        self._view.show_selected_state(state)
        self._view.show_status(f"Estado seleccionado: {state.identifier}")

    def _on_state_moved(self, identifier: str, x: float, y: float) -> None:
        state = self._model.automaton.get_state(identifier)
        state.set_position(x, y)

    def _on_state_initial_changed(self, identifier: str, checked: bool) -> None:
        state = self._model.automaton.get_state(identifier)
        if checked:
            self._model.automaton.set_initial_state(identifier)
        elif state.is_initial:
            self._model.automaton.set_initial_state(None)

        self._view.refresh_states(self._model.automaton.states)
        self._view.show_selected_state(state)
        self._view.show_status(
            f"{state.identifier} "
            + ("es el estado inicial" if state.is_initial else "ya no es el estado inicial")
        )

    def _on_state_accepting_changed(self, identifier: str, checked: bool) -> None:
        self._model.automaton.set_accepting(identifier, checked)
        state = self._model.automaton.get_state(identifier)
        self._view.refresh_state(state)
        self._view.show_status(
            f"{state.identifier} "
            + ("marcado como estado de aceptación" if checked else "ya no es de aceptación")
        )
