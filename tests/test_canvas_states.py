from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QGraphicsView

from app_automatas.controller.app_controller import AppController
from app_automatas.model.editor_session import EditorSession
from app_automatas.theme.palette import DARK_PALETTE
from app_automatas.view.main_window import MainWindow


def _build_editor() -> tuple[EditorSession, MainWindow, AppController]:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)
    return model, view, controller


def test_state_tool_is_available_and_select_is_default(qapp: QApplication) -> None:
    model, view, controller = _build_editor()

    assert model.editor_tool == "select"
    assert view.toolbar.select_action.isEnabled()
    assert view.toolbar.select_action.isChecked()
    assert view.toolbar.add_state_action.isEnabled()
    assert view.toolbar.add_transition_action.isEnabled()
    assert view.canvas.dragMode() == QGraphicsView.DragMode.RubberBandDrag

    controller.deleteLater()
    view.close()


def test_state_tool_creates_consecutive_states_on_canvas(qapp: QApplication) -> None:
    model, view, controller = _build_editor()

    view.toolbar.add_state_action.trigger()
    view.canvas_clicked.emit(200.0, 160.0)
    view.canvas_clicked.emit(420.0, 260.0)
    qapp.processEvents()

    assert [state.identifier for state in model.automaton.states] == ["q0", "q1"]
    assert model.automaton.get_state("q0").x == 200.0
    assert model.automaton.get_state("q0").y == 160.0
    assert view.scene.state_item("q0").pos() == QPointF(200.0, 160.0)
    assert view.scene.state_item("q1").isSelected()

    controller.deleteLater()
    view.close()


def test_select_tool_does_not_create_state_on_empty_canvas(qapp: QApplication) -> None:
    model, view, controller = _build_editor()

    view.canvas_clicked.emit(200.0, 160.0)
    qapp.processEvents()

    assert model.automaton.states == ()

    controller.deleteLater()
    view.close()


def test_moving_graphical_state_updates_model_position(qapp: QApplication) -> None:
    model, view, controller = _build_editor()
    view.toolbar.add_state_action.trigger()
    view.canvas_clicked.emit(200.0, 160.0)
    qapp.processEvents()

    item = view.scene.state_item("q0")
    item.setPos(515.0, 345.0)
    qapp.processEvents()

    state = model.automaton.get_state("q0")
    assert state.x == 515.0
    assert state.y == 345.0

    controller.deleteLater()
    view.close()


def test_selected_state_can_be_initial_and_accepting(qapp: QApplication) -> None:
    model, view, controller = _build_editor()
    view.toolbar.add_state_action.trigger()
    view.canvas_clicked.emit(200.0, 160.0)
    qapp.processEvents()

    view.sidebar.initial_checkbox.setChecked(True)
    view.sidebar.accepting_checkbox.setChecked(True)
    qapp.processEvents()

    state = model.automaton.get_state("q0")
    item = view.scene.state_item("q0")
    assert state.is_initial
    assert state.is_accepting
    assert item.is_initial
    assert item.is_accepting
    assert view.sidebar.selected_state_label.text() == "q0"

    controller.deleteLater()
    view.close()


def test_selecting_new_initial_state_refreshes_previous_item(qapp: QApplication) -> None:
    model, view, controller = _build_editor()
    view.toolbar.add_state_action.trigger()
    view.canvas_clicked.emit(200.0, 160.0)
    qapp.processEvents()
    view.sidebar.initial_checkbox.setChecked(True)

    view.canvas_clicked.emit(420.0, 260.0)
    qapp.processEvents()
    view.sidebar.initial_checkbox.setChecked(True)
    qapp.processEvents()

    first = model.automaton.get_state("q0")
    second = model.automaton.get_state("q1")
    assert not first.is_initial
    assert second.is_initial
    assert not view.scene.state_item("q0").is_initial
    assert view.scene.state_item("q1").is_initial

    controller.deleteLater()
    view.close()


def test_theme_change_propagates_to_canvas_items(qapp: QApplication) -> None:
    model, view, controller = _build_editor()
    view.toolbar.add_state_action.trigger()
    view.canvas_clicked.emit(200.0, 160.0)
    qapp.processEvents()

    view.toolbar.theme_action.setChecked(True)
    qapp.processEvents()

    assert model.theme_mode == "dark"
    assert view.scene.theme_mode == "dark"
    assert DARK_PALETTE.primary in qapp.styleSheet()

    controller.deleteLater()
    view.close()


def test_automaton_type_change_is_rejected_after_creating_state(qapp: QApplication) -> None:
    model, view, controller = _build_editor()
    view.toolbar.add_state_action.trigger()
    view.canvas_clicked.emit(200.0, 160.0)
    qapp.processEvents()

    view.sidebar.automaton_type_combo.setCurrentText("AFN")
    qapp.processEvents()

    assert model.automaton_type == "AFD"
    assert view.sidebar.automaton_type_combo.currentText() == "AFD"
    assert "No se puede cambiar" in view.statusBar().currentMessage()

    controller.deleteLater()
    view.close()
