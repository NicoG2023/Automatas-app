"""Graphics view used as the automaton drawing canvas."""

from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView

from app_automatas.view.canvas.automaton_scene import AutomatonScene


class AutomatonView(QGraphicsView):
    """Scrollable viewport for the automaton scene."""

    def __init__(self, scene: AutomatonScene) -> None:
        super().__init__(scene)
        self.setObjectName("automatonCanvas")
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
