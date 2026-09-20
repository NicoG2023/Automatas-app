"""Top-level controller for the editor shell."""

from __future__ import annotations

from PySide6.QtCore import QObject

from app_automatas.model.editor_session import EditorSession
from app_automatas.view.main_window import MainWindow


class AppController(QObject):
    """Coordinate the initial editor model and main window."""

    def __init__(self, model: EditorSession, view: MainWindow) -> None:
        super().__init__()
        self._model = model
        self._view = view

        self._view.automaton_type_changed.connect(self._on_automaton_type_changed)
        self._view.theme_changed.connect(self._on_theme_changed)
        self._sync_view()

    def show(self) -> None:
        """Display the main window."""
        self._view.show()

    def _sync_view(self) -> None:
        self._view.set_automaton_type(self._model.automaton_type)
        self._view.set_theme(self._model.theme_mode)
        self._view.show_status(f"Modo de edición: {self._model.automaton_type}")

    def _on_automaton_type_changed(self, automaton_type: str) -> None:
        self._model.set_automaton_type(automaton_type)
        self._view.show_status(f"Modo de edición: {self._model.automaton_type}")

    def _on_theme_changed(self, theme_mode: str) -> None:
        self._model.set_theme_mode(theme_mode)
        self._view.set_theme(self._model.theme_mode)
        theme_label = "oscuro" if self._model.theme_mode == "dark" else "claro"
        self._view.show_status(f"Tema {theme_label} activado")
