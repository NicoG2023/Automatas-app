"""Graphics scene reserved for automaton states and transitions."""

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsScene


class AutomatonScene(QGraphicsScene):
    """Canvas model for graphical automaton items."""

    DEFAULT_WIDTH = 1600
    DEFAULT_HEIGHT = 1000

    def __init__(self) -> None:
        super().__init__()
        self.setSceneRect(QRectF(0, 0, self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT))
