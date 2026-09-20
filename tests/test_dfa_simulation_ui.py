from PySide6.QtWidgets import QApplication

from app_automatas.controller.app_controller import AppController
from app_automatas.model.editor_session import EditorSession
from app_automatas.view.main_window import MainWindow


def _build_editor() -> tuple[EditorSession, MainWindow, AppController]:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)
    return model, view, controller


def _install_simple_dfa(model: EditorSession, view: MainWindow) -> None:
    automaton = model.automaton
    automaton.set_alphabet(["a"])
    automaton.add_state("q0", is_initial=True, x=180, y=180)
    automaton.add_state("q1", is_accepting=True, x=420, y=180)
    automaton.add_transition("q0", "q1", "a")
    view.set_alphabet(automaton.alphabet)
    view.rebuild_automaton(automaton.states, automaton.transitions)


def test_simulation_panel_is_available_for_dfa(qapp: QApplication) -> None:
    model, view, controller = _build_editor()

    assert model.automaton_type == "AFD"
    assert view.simulation_panel.input_edit.isEnabled()
    assert view.simulation_panel.start_button.isEnabled()
    assert not view.simulation_panel.next_button.isEnabled()

    controller.deleteLater()
    view.close()


def test_simulation_panel_is_available_for_nfa(qapp: QApplication) -> None:
    model, view, controller = _build_editor()

    view.sidebar.automaton_type_combo.setCurrentText("AFN")
    qapp.processEvents()

    assert model.automaton_type == "AFN"
    assert view.simulation_panel.input_edit.isEnabled()
    assert view.simulation_panel.start_button.isEnabled()
    assert view.simulation_panel.state_caption.text() == "Estados activos:"
    assert view.simulation_panel.transition_caption.text() == "Transiciones:"

    controller.deleteLater()
    view.close()


def test_manual_dfa_simulation_updates_panel_and_canvas(qapp: QApplication) -> None:
    model, view, controller = _build_editor()
    _install_simple_dfa(model, view)

    view.simulation_start_requested.emit("a")
    qapp.processEvents()

    assert view.simulation_panel.result_label.text() == "Lista"
    assert view.simulation_panel.state_value.text() == "q0"
    assert view.simulation_panel.symbol_value.text() == "a"
    assert view.simulation_panel.remaining_value.text() == "a"
    assert view.scene.state_item("q0").simulation_active
    assert not view.scene.state_item("q1").simulation_active

    view.simulation_next_requested.emit()
    qapp.processEvents()

    assert view.simulation_panel.result_label.text() == "Aceptada"
    assert view.simulation_panel.state_value.text() == "q1"
    assert view.simulation_panel.processed_value.text() == "a"
    assert view.simulation_panel.remaining_value.text() == "Vacía"
    assert view.simulation_panel.transition_value.text() == "q0 → q1"
    assert view.scene.state_item("q1").simulation_active
    assert view.scene.transition_item("q0", "q1").simulation_active
    assert view.statusBar().currentMessage() == "Cadena aceptada"

    controller.deleteLater()
    view.close()


def test_reset_returns_highlight_to_initial_state(qapp: QApplication) -> None:
    model, view, controller = _build_editor()
    _install_simple_dfa(model, view)
    view.simulation_start_requested.emit("a")
    view.simulation_next_requested.emit()
    qapp.processEvents()

    view.simulation_reset_requested.emit()
    qapp.processEvents()

    assert view.simulation_panel.result_label.text() == "Lista"
    assert view.simulation_panel.state_value.text() == "q0"
    assert view.simulation_panel.processed_value.text() == "Vacía"
    assert view.simulation_panel.remaining_value.text() == "a"
    assert view.scene.state_item("q0").simulation_active
    assert not view.scene.transition_item("q0", "q1").simulation_active

    controller.deleteLater()
    view.close()


def test_play_and_pause_toggle_controls(qapp: QApplication) -> None:
    model, view, controller = _build_editor()
    _install_simple_dfa(model, view)
    view.simulation_start_requested.emit("a")
    qapp.processEvents()

    view.simulation_play_requested.emit()
    qapp.processEvents()

    assert view.simulation_panel.pause_button.isEnabled()
    assert not view.simulation_panel.play_button.isEnabled()
    assert not view.simulation_panel.input_edit.isEnabled()

    view.simulation_pause_requested.emit()
    qapp.processEvents()

    assert not view.simulation_panel.pause_button.isEnabled()
    assert view.simulation_panel.play_button.isEnabled()
    assert view.simulation_panel.input_edit.isEnabled()

    controller.deleteLater()
    view.close()
