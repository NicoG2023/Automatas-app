"""Main desktop window."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from app_automatas.model.state import State
from app_automatas.model.transition import Transition
from app_automatas.theme.manager import apply_theme
from app_automatas.view.canvas.automaton_scene import AutomatonScene
from app_automatas.view.canvas.automaton_view import AutomatonView
from app_automatas.view.canvas.transition_item import TransitionItem
from app_automatas.view.widgets.editor_sidebar import EditorSidebar
from app_automatas.view.widgets.editor_toolbar import EditorToolBar


class MainWindow(QMainWindow):
    """Top-level view for the automaton editor."""

    automaton_type_changed = Signal(str)
    alphabet_changed = Signal(object)
    editor_tool_changed = Signal(str)
    theme_changed = Signal(str)
    clear_requested = Signal()
    canvas_clicked = Signal(float, float)
    state_selected = Signal(object)
    state_moved = Signal(str, float, float)
    state_initial_changed = Signal(str, bool)
    state_accepting_changed = Signal(str, bool)
    state_rename_requested = Signal(str, str)
    state_delete_requested = Signal(str)
    transition_source_changed = Signal(object)
    transition_requested = Signal(str, str)
    transition_selected = Signal(object)
    transition_symbols_changed = Signal(str, str, object)
    transition_delete_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("App de Autómatas")
        self.setMinimumSize(960, 640)
        self.resize(1280, 800)
        self._theme_mode = "light"

        self.scene = AutomatonScene()
        self.canvas = AutomatonView(self.scene)
        self.sidebar = EditorSidebar()
        self.toolbar = EditorToolBar()

        self.sidebar.automaton_type_changed.connect(self.automaton_type_changed.emit)
        self.sidebar.alphabet_changed.connect(self.alphabet_changed.emit)
        self.sidebar.state_initial_changed.connect(self.state_initial_changed.emit)
        self.sidebar.state_accepting_changed.connect(self.state_accepting_changed.emit)
        self.sidebar.state_rename_requested.connect(self.state_rename_requested.emit)
        self.sidebar.state_delete_requested.connect(self.state_delete_requested.emit)
        self.sidebar.transition_symbols_changed.connect(
            self.transition_symbols_changed.emit
        )
        self.sidebar.transition_delete_requested.connect(
            self.transition_delete_requested.emit
        )
        self.toolbar.tool_changed.connect(self.editor_tool_changed.emit)
        self.toolbar.theme_changed.connect(self.theme_changed.emit)
        self.toolbar.clear_requested.connect(self.clear_requested.emit)
        self.scene.canvas_clicked.connect(self.canvas_clicked.emit)
        self.scene.selected_state_changed.connect(self.state_selected.emit)
        self.scene.selected_transition_changed.connect(self.transition_selected.emit)
        self.scene.state_position_changed.connect(self.state_moved.emit)
        self.scene.transition_source_changed.connect(self.transition_source_changed.emit)
        self.scene.transition_requested.connect(self.transition_requested.emit)

        self.addToolBar(self.toolbar)
        self.setCentralWidget(self._build_central_widget())
        self.statusBar().showMessage("Listo")
        self.set_theme("light")

    def _build_central_widget(self) -> QWidget:
        central_widget = QWidget()
        central_widget.setObjectName("centralArea")
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.canvas, 1)
        return central_widget

    def set_automaton_type(self, automaton_type: str) -> None:
        self.sidebar.set_automaton_type(automaton_type)

    def set_alphabet(self, symbols: frozenset[str] | set[str]) -> None:
        self.sidebar.set_alphabet(symbols)

    def set_editor_tool(self, editor_tool: str) -> None:
        self.toolbar.set_editor_tool(editor_tool)
        self.canvas.set_editor_tool(editor_tool)
        self.scene.set_editor_tool(editor_tool)

    def set_theme(self, theme_mode: str) -> None:
        """Apply a theme globally and synchronize canvas items and toolbar."""
        application = QApplication.instance()
        if application is None:
            raise RuntimeError("A QApplication must exist before applying a theme")
        self._theme_mode = theme_mode
        apply_theme(application, theme_mode)
        self.scene.set_theme(theme_mode)
        self.toolbar.set_theme(theme_mode)

    def add_state(self, state: State) -> None:
        self.scene.add_state_item(state, select=True)

    def add_or_refresh_transition(self, transition: Transition) -> TransitionItem:
        return self.scene.add_or_refresh_transition(transition)

    def rebuild_automaton(
        self,
        states: tuple[State, ...],
        transitions: tuple[Transition, ...],
        *,
        selected_state_id: str | None = None,
        selected_transition: tuple[str, str] | None = None,
    ) -> None:
        """Recreate canvas items from the model after structural edits."""
        self.scene.rebuild_automaton(
            states,
            transitions,
            selected_state_id=selected_state_id,
            selected_transition=selected_transition,
        )

    def refresh_state(self, state: State) -> None:
        self.scene.refresh_state(state)
        self.show_selected_state(state)

    def refresh_states(self, states: tuple[State, ...]) -> None:
        self.scene.refresh_states(states)
        selected = next(
            (
                state
                for state in states
                if self.scene.state_item(state.identifier).isSelected()
            ),
            None,
        )
        if selected is not None:
            self.show_selected_state(selected)

    def show_selected_state(self, state: State | None) -> None:
        self.sidebar.show_state(state)
        if state is not None:
            self.sidebar.show_transition(None)

    def show_selected_transition(self, transition: Transition | None) -> None:
        self.sidebar.show_transition(transition)
        if transition is not None:
            self.sidebar.show_state(None)

    def request_transition_symbol(
        self,
        source_id: str,
        target_id: str,
        alphabet: frozenset[str],
    ) -> str | None:
        """Ask the user which existing alphabet symbol belongs to a new edge."""
        if not alphabet:
            return None
        symbols = sorted(alphabet)
        symbol, accepted = QInputDialog.getItem(
            self,
            "Crear transición",
            f"Símbolo para {source_id} → {target_id}:",
            symbols,
            0,
            False,
        )
        return symbol if accepted else None

    def confirm_alphabet_symbol_removal(self, symbols: frozenset[str]) -> bool:
        """Warn before removing symbols currently used by transitions."""
        rendered = ", ".join(sorted(symbols))
        answer = QMessageBox.question(
            self,
            "Modificar alfabeto",
            (
                f"Los símbolos {rendered} están siendo usados por transiciones.\n\n"
                "Si continúas, se eliminarán de las transiciones afectadas y cualquier "
                "transición que quede sin símbolos también será eliminada."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def confirm_state_deletion(self, identifier: str) -> bool:
        """Confirm deletion of a state and every connected transition."""
        answer = QMessageBox.question(
            self,
            "Eliminar estado",
            (
                f"¿Eliminar el estado {identifier}?\n\n"
                "También se eliminarán todas sus transiciones asociadas."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def confirm_transition_deletion(self, source_id: str, target_id: str) -> bool:
        """Confirm deletion of one complete graphical transition."""
        answer = QMessageBox.question(
            self,
            "Eliminar transición",
            f"¿Eliminar la transición {source_id} → {target_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def confirm_clear_automaton(self) -> bool:
        """Confirm clearing the complete current automaton."""
        answer = QMessageBox.question(
            self,
            "Limpiar autómata",
            "¿Eliminar el alfabeto, todos los estados y todas las transiciones?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def show_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
