from PySide6.QtWidgets import QApplication

from app_automatas.controller.app_controller import AppController
from app_automatas.model.editor_session import EditorSession
from app_automatas.view.main_window import MainWindow


def _build_nfa_editor() -> tuple[EditorSession, MainWindow, AppController]:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)
    view.sidebar.automaton_type_combo.setCurrentText("AFN")
    return model, view, controller


def _install_branching_nfa(model: EditorSession, view: MainWindow) -> None:
    automaton = model.automaton
    automaton.set_alphabet(["a", "b"])
    automaton.add_state("q0", is_initial=True, x=180, y=220)
    automaton.add_state("q1", x=420, y=140)
    automaton.add_state("q2", x=420, y=300)
    automaton.add_state("q3", is_accepting=True, x=680, y=140)
    automaton.add_transition("q0", "q1", "a")
    automaton.add_transition("q0", "q2", "a")
    automaton.add_transition("q1", "q3", "b")
    view.set_alphabet(automaton.alphabet)
    view.rebuild_automaton(automaton.states, automaton.transitions)


def test_nfa_step_shows_multiple_active_states_and_transitions(qapp: QApplication) -> None:
    model, view, controller = _build_nfa_editor()
    _install_branching_nfa(model, view)

    view.simulation_start_requested.emit("ab")
    view.simulation_next_requested.emit()
    qapp.processEvents()

    assert view.simulation_panel.result_label.text() == "En curso"
    assert view.simulation_panel.state_value.text() == "{q1, q2}"
    assert view.simulation_panel.transition_value.text() == "q0 → q1; q0 → q2"
    assert view.scene.state_item("q1").simulation_active
    assert view.scene.state_item("q2").simulation_active
    assert not view.scene.state_item("q0").simulation_active
    assert view.scene.transition_item("q0", "q1").simulation_active
    assert view.scene.transition_item("q0", "q2").simulation_active

    controller.deleteLater()
    view.close()


def test_nfa_dead_branch_is_discarded_while_live_branch_finishes(qapp: QApplication) -> None:
    model, view, controller = _build_nfa_editor()
    _install_branching_nfa(model, view)

    view.simulation_start_requested.emit("ab")
    view.simulation_next_requested.emit()
    view.simulation_next_requested.emit()
    qapp.processEvents()

    assert view.simulation_panel.result_label.text() == "Aceptada"
    assert view.simulation_panel.state_value.text() == "{q3}"
    assert view.simulation_panel.transition_value.text() == "q1 → q3"
    assert view.scene.state_item("q3").simulation_active
    assert not view.scene.state_item("q2").simulation_active
    assert view.scene.state_item("q0").simulation_role == "success"
    assert view.scene.state_item("q1").simulation_role == "success"
    assert view.scene.state_item("q2").simulation_role == "failed"
    assert view.scene.transition_item("q0", "q1").simulation_role == "success"
    assert view.scene.transition_item("q0", "q2").simulation_role == "failed"
    assert view.scene.transition_item("q1", "q3").simulation_role == "active"
    assert view.statusBar().currentMessage() == "Cadena aceptada"

    controller.deleteLater()
    view.close()


def test_nfa_rejects_when_all_branches_die(qapp: QApplication) -> None:
    model, view, controller = _build_nfa_editor()
    _install_branching_nfa(model, view)

    view.simulation_start_requested.emit("aa")
    view.simulation_next_requested.emit()
    view.simulation_next_requested.emit()
    qapp.processEvents()

    assert view.simulation_panel.result_label.text() == "Rechazada"
    assert view.simulation_panel.state_value.text() == "Ninguno"
    assert "Ningún recorrido" in view.simulation_panel.reason_value.text()
    assert view.statusBar().currentMessage() == "Cadena rechazada"

    controller.deleteLater()
    view.close()
