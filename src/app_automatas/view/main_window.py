"""Main desktop window."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget

from app_automatas.theme.manager import apply_theme
from app_automatas.view.canvas.automaton_scene import AutomatonScene
from app_automatas.view.canvas.automaton_view import AutomatonView
from app_automatas.view.widgets.editor_sidebar import EditorSidebar
from app_automatas.view.widgets.editor_toolbar import EditorToolBar


class MainWindow(QMainWindow):
    """Top-level view for the automaton editor."""

    automaton_type_changed = Signal(str)
    theme_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("App de Autómatas")
        self.setMinimumSize(960, 640)
        self.resize(1280, 800)

        self.scene = AutomatonScene()
        self.canvas = AutomatonView(self.scene)
        self.sidebar = EditorSidebar()
        self.toolbar = EditorToolBar()

        self.sidebar.automaton_type_changed.connect(self.automaton_type_changed.emit)
        self.toolbar.theme_changed.connect(self.theme_changed.emit)

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

    def set_theme(self, theme_mode: str) -> None:
        """Apply a theme globally and synchronize the toolbar toggle."""
        application = QApplication.instance()
        if application is None:
            raise RuntimeError("A QApplication must exist before applying a theme")
        apply_theme(application, theme_mode)
        self.toolbar.set_theme(theme_mode)

    def show_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
