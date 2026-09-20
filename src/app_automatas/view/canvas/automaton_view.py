"""Graphics view used as the automaton drawing canvas."""

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QMouseEvent, QPainter, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsView

from app_automatas.view.canvas.automaton_scene import AutomatonScene


class AutomatonView(QGraphicsView):
    """Scrollable viewport for the automaton scene."""

    def __init__(self, scene: AutomatonScene) -> None:
        super().__init__(scene)
        self.setObjectName("automatonCanvas")
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._editor_tool = "select"
        self._panning = False
        self._pan_start = QPoint()
        self._pan_restore_cursor = Qt.CursorShape.ArrowCursor
        self._zoom_enabled = False
        self._auto_fit_enabled = False
        self._zoom_factor = 1.0
        self.set_editor_tool("select")


    def enable_zoom_mode(self, *, auto_fit: bool = False) -> None:
        """Enable wheel zoom and hide scrollbars while preserving canvas panning."""
        self._zoom_enabled = True
        self._auto_fit_enabled = auto_fit
        self._zoom_factor = 1.0
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        if auto_fit:
            self._fit_scene_in_view()

    def enable_zoom_only_mode(self) -> None:
        """Backward-compatible alias for fitted zoom viewers."""
        self.enable_zoom_mode(auto_fit=True)

    def reset_zoom(self) -> None:
        """Reset the viewer scale to the fitted baseline."""
        self._zoom_factor = 1.0
        self._fit_scene_in_view()

    def _fit_scene_in_view(self) -> None:
        if not self._auto_fit_enabled:
            return
        scene = self.scene()
        if scene is None:
            return
        rect = scene.itemsBoundingRect()
        if rect.isNull() or rect.width() <= 0 or rect.height() <= 0:
            rect = QRectF(-120, -120, 240, 240)
        else:
            rect = rect.adjusted(-80, -80, 80, 80)
        self.setSceneRect(rect)
        self.resetTransform()
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        if self._zoom_factor != 1.0:
            self.scale(self._zoom_factor, self._zoom_factor)

    def set_editor_tool(self, editor_tool: str) -> None:
        """Update canvas interaction feedback for the selected editor tool."""
        self._editor_tool = editor_tool
        if self._panning:
            return
        if editor_tool == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            return
        if editor_tool == "state":
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)
            return
        if editor_tool == "transition":
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
            return
        raise ValueError(f"Unsupported editor tool: {editor_tool}")

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.MiddleButton:
            self._start_panning(event.position().toPoint())
            event.accept()
            return

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._editor_tool == "select"
            and self.itemAt(event.position().toPoint()) is None
        ):
            self._start_panning(event.position().toPoint())
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._panning:
            delta = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._panning and event.button() in {
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.MiddleButton,
        }:
            self._stop_panning()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _start_panning(self, position: QPoint) -> None:
        self._panning = True
        self._pan_start = position
        self._pan_restore_cursor = self.viewport().cursor().shape()
        self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)

    def _stop_panning(self) -> None:
        self._panning = False
        self.viewport().setCursor(self._pan_restore_cursor)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if self._zoom_enabled:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            new_zoom = max(0.5, min(3.0, self._zoom_factor * factor))
            factor = new_zoom / self._zoom_factor
            self._zoom_factor = new_zoom
            self.scale(factor, factor)
            event.accept()
            return
        super().wheelEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._auto_fit_enabled:
            self._fit_scene_in_view()
