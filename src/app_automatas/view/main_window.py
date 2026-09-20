"""Main desktop window."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget

from app_automatas.model.state import State
from app_automatas.theme.manager import apply_theme
from app_automatas.view.canvas.automaton_scene import AutomatonScene
from app_automatas.view.canvas.automaton_view import AutomatonView
from app_automatas.view.widgets.editor_sidebar import EditorSidebar
from app_automatas.view.widgets.editor_toolbar import EditorToolBar


class MainWindow(QMainWindow):
    """Top-level view for the automaton editor."""

    automaton_type_changed = Signal(str)
    editor_tool_changed = Signal(str)
    theme_changed = Signal(str)
    canvas_clicked = Signal(float, float)
    state_selected = Signal(object)
    state_moved = Signal(str, float, float)
    state_initial_changed = Signal(str, bool)
    state_accepting_changed = Signal(str, bool)

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
        self.sidebar.state_initial_changed.connect(self.state_initial_changed.emit)
        self.sidebar.state_accepting_changed.connect(self.state_accepting_changed.emit)
        self.toolbar.tool_changed.connect(self.editor_tool_changed.emit)
        self.toolbar.theme_changed.connect(self.theme_changed.emit)
        self.scene.canvas_clicked.connect(self.canvas_clicked.emit)
        self.scene.selected_state_changed.connect(self.state_selected.emit)
        self.scene.state_position_changed.connect(self.state_moved.emit)

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

    def set_editor_tool(self, editor_tool: str) -> None:
        self.toolbar.set_editor_tool(editor_tool)
        self.canvas.set_editor_tool(editor_tool)

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

    def refresh_state(self, state: State) -> None:
        self.scene.refresh_state(state)
        self.show_selected_state(state)

    def refresh_states(self, states: tuple[State, ...]) -> None:
        self.scene.refresh_states(states)
        selected = next((state for state in states if self.scene.state_item(state.identifier).isSelected()), None)
        if selected is not None:
            self.show_selected_state(selected)

    def show_selected_state(self, state: State | None) -> None:
        self.sidebar.show_state(state)

    def show_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
