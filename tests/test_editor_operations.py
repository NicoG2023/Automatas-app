import pytest
from PySide6.QtWidgets import QApplication

from app_automatas.controller.app_controller import AppController
from app_automatas.model.editor_session import EditorSession
from app_automatas.model.exceptions import UnknownStateError, UnknownTransitionError
from app_automatas.view.main_window import MainWindow


def _build_editor() -> tuple[EditorSession, MainWindow, AppController]:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)
    return model, view, controller


def _add_states(
    model: EditorSession,
    view: MainWindow,
    qapp: QApplication,
    *positions: tuple[float, float],
) -> None:
    view.toolbar.add_state_action.trigger()
    for x, y in positions:
        view.canvas_clicked.emit(x, y)
    qapp.processEvents()
    assert len(model.automaton.states) == len(positions)


def _add_transition(
    model: EditorSession,
    view: MainWindow,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    *,
    alphabet: list[str],
    symbol: str,
) -> None:
    view.alphabet_changed.emit(alphabet)
    monkeypatch.setattr(view, "request_transition_symbol", lambda *_: symbol)
    view.transition_requested.emit("q0", "q1")
    qapp.processEvents()
    assert len(model.automaton.transitions) == 1


def test_selected_state_can_be_renamed_with_connected_transition(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, view, controller = _build_editor()
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    _add_transition(
        model,
        view,
        qapp,
        monkeypatch,
        alphabet=["a"],
        symbol="a",
    )

    view.scene.clearSelection()
    view.scene.state_item("q0").setSelected(True)
    qapp.processEvents()
    view.sidebar.state_name_input.setText("inicio")
    view.sidebar.rename_state_button.click()
    qapp.processEvents()

    assert model.automaton.get_state("inicio").identifier == "inicio"
    with pytest.raises(UnknownStateError):
        model.automaton.get_state("q0")
    assert model.automaton.get_transition("inicio", "q1").source.identifier == "inicio"
    assert view.scene.state_item("inicio").isSelected()
    assert view.scene.transition_item("inicio", "q1").symbols == frozenset({"a"})
    assert view.sidebar.selected_state_label.text() == "inicio"

    controller.deleteLater()
    view.close()


def test_duplicate_state_name_is_rejected(qapp: QApplication) -> None:
    model, view, controller = _build_editor()
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))

    view.scene.clearSelection()
    view.scene.state_item("q0").setSelected(True)
    qapp.processEvents()
    view.sidebar.state_name_input.setText("q1")
    view.sidebar.rename_state_button.click()
    qapp.processEvents()

    assert [state.identifier for state in model.automaton.states] == ["q0", "q1"]
    assert view.sidebar.state_name_input.text() == "q0"
    assert "Ya existe" in view.statusBar().currentMessage()

    controller.deleteLater()
    view.close()


def test_deleting_state_removes_connected_transitions(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, view, controller = _build_editor()
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    _add_transition(
        model,
        view,
        qapp,
        monkeypatch,
        alphabet=["a"],
        symbol="a",
    )
    monkeypatch.setattr(view, "confirm_state_deletion", lambda *_: True)

    view.scene.clearSelection()
    view.scene.state_item("q0").setSelected(True)
    qapp.processEvents()
    view.sidebar.delete_state_button.click()
    qapp.processEvents()

    with pytest.raises(UnknownStateError):
        model.automaton.get_state("q0")
    assert model.automaton.transitions == ()
    with pytest.raises(KeyError):
        view.scene.state_item("q0")
    with pytest.raises(KeyError):
        view.scene.transition_item("q0", "q1")
    assert view.scene.state_item("q1") is not None

    controller.deleteLater()
    view.close()


def test_selected_transition_can_replace_its_symbols(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, view, controller = _build_editor()
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    _add_transition(
        model,
        view,
        qapp,
        monkeypatch,
        alphabet=["a", "b", "c"],
        symbol="a",
    )

    view.scene.clearSelection()
    view.scene.transition_item("q0", "q1").setSelected(True)
    qapp.processEvents()

    assert view.sidebar.selected_transition_label.text() == "q0 → q1"
    view.sidebar.transition_symbols_input.setText("b, c")
    view.sidebar.apply_transition_button.click()
    qapp.processEvents()

    transition = model.automaton.get_transition("q0", "q1")
    assert transition.symbols == {"b", "c"}
    assert view.scene.transition_item("q0", "q1").symbols == frozenset({"b", "c"})
    assert view.sidebar.transition_symbols_input.text() == "b, c"

    controller.deleteLater()
    view.close()


def test_empty_transition_symbol_edit_is_rejected(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, view, controller = _build_editor()
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    _add_transition(
        model,
        view,
        qapp,
        monkeypatch,
        alphabet=["a"],
        symbol="a",
    )

    view.scene.clearSelection()
    view.scene.transition_item("q0", "q1").setSelected(True)
    qapp.processEvents()
    view.sidebar.transition_symbols_input.clear()
    view.sidebar.apply_transition_button.click()
    qapp.processEvents()

    assert model.automaton.get_transition("q0", "q1").symbols == {"a"}
    assert view.sidebar.transition_symbols_input.text() == "a"
    assert "al menos un símbolo" in view.statusBar().currentMessage()

    controller.deleteLater()
    view.close()


def test_transition_can_be_deleted_from_sidebar(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, view, controller = _build_editor()
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    _add_transition(
        model,
        view,
        qapp,
        monkeypatch,
        alphabet=["a"],
        symbol="a",
    )
    monkeypatch.setattr(view, "confirm_transition_deletion", lambda *_: True)

    view.scene.clearSelection()
    view.scene.transition_item("q0", "q1").setSelected(True)
    qapp.processEvents()
    view.sidebar.delete_transition_button.click()
    qapp.processEvents()

    with pytest.raises(UnknownTransitionError):
        model.automaton.get_transition("q0", "q1")
    with pytest.raises(KeyError):
        view.scene.transition_item("q0", "q1")
    assert view.sidebar.selected_transition_label.text() == "Ninguna"

    controller.deleteLater()
    view.close()


def test_confirmed_alphabet_removal_updates_and_deletes_affected_edges(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, view, controller = _build_editor()
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    _add_transition(
        model,
        view,
        qapp,
        monkeypatch,
        alphabet=["a", "b"],
        symbol="a",
    )
    monkeypatch.setattr(view, "confirm_alphabet_symbol_removal", lambda *_: True)

    view.sidebar.alphabet_input.setText("b")
    view.sidebar.apply_alphabet_button.click()
    qapp.processEvents()

    assert model.automaton.alphabet == frozenset({"b"})
    assert model.automaton.transitions == ()
    assert view.sidebar.alphabet_input.text() == "b"
    with pytest.raises(KeyError):
        view.scene.transition_item("q0", "q1")

    controller.deleteLater()
    view.close()


def test_cancelled_alphabet_removal_keeps_document_unchanged(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, view, controller = _build_editor()
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    _add_transition(
        model,
        view,
        qapp,
        monkeypatch,
        alphabet=["a", "b"],
        symbol="a",
    )
    monkeypatch.setattr(view, "confirm_alphabet_symbol_removal", lambda *_: False)

    view.sidebar.alphabet_input.setText("b")
    view.sidebar.apply_alphabet_button.click()
    qapp.processEvents()

    assert model.automaton.alphabet == frozenset({"a", "b"})
    assert model.automaton.get_transition("q0", "q1").symbols == {"a"}
    assert view.sidebar.alphabet_input.text() == "a, b"
    assert "cancelada" in view.statusBar().currentMessage()

    controller.deleteLater()
    view.close()


def test_clear_action_resets_entire_document_and_state_counter(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, view, controller = _build_editor()
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    _add_transition(
        model,
        view,
        qapp,
        monkeypatch,
        alphabet=["a"],
        symbol="a",
    )
    monkeypatch.setattr(view, "confirm_clear_automaton", lambda: True)

    view.toolbar.clear_action.trigger()
    qapp.processEvents()

    assert model.automaton.alphabet == frozenset()
    assert model.automaton.states == ()
    assert model.automaton.transitions == ()
    assert view.sidebar.alphabet_input.text() == ""
    with pytest.raises(KeyError):
        view.scene.state_item("q0")

    view.toolbar.add_state_action.trigger()
    view.canvas_clicked.emit(300.0, 240.0)
    qapp.processEvents()
    assert [state.identifier for state in model.automaton.states] == ["q0"]

    controller.deleteLater()
    view.close()
