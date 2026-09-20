"""Graphics view used as the automaton drawing canvas."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView

from app_automatas.view.canvas.automaton_scene import AutomatonScene


class AutomatonView(QGraphicsView):
    """Scrollable viewport for the automaton scene."""

    def __init__(self, scene: AutomatonScene) -> None:
        super().__init__(scene)
        self.setObjectName("automatonCanvas")
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.set_editor_tool("select")

    def set_editor_tool(self, editor_tool: str) -> None:
        """Update canvas interaction feedback for the selected editor tool."""
        if editor_tool == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            return
        if editor_tool == "state":
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)
            return
        raise ValueError(f"Unsupported editor tool: {editor_tool}")
