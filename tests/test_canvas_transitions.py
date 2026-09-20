from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QGraphicsView

from app_automatas.controller.app_controller import AppController
from app_automatas.model.editor_session import EditorSession
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


def test_transition_tool_is_enabled_and_changes_canvas_mode(qapp: QApplication) -> None:
    model, view, controller = _build_editor()

    view.toolbar.add_transition_action.trigger()
    qapp.processEvents()

    assert model.editor_tool == "transition"
    assert view.toolbar.add_transition_action.isChecked()
    assert view.canvas.dragMode() == QGraphicsView.DragMode.NoDrag

    controller.deleteLater()
    view.close()


def test_alphabet_can_be_defined_from_sidebar(qapp: QApplication) -> None:
    model, view, controller = _build_editor()

    view.sidebar.alphabet_input.setText("a, b, 0")
    view.sidebar.apply_alphabet_button.click()
    qapp.processEvents()

    assert model.automaton.alphabet == frozenset({"a", "b", "0"})
    assert view.sidebar.alphabet_input.text() == "0, a, b"

    controller.deleteLater()
    view.close()


def test_epsilon_is_rejected_from_alphabet(qapp: QApplication) -> None:
    model, view, controller = _build_editor()

    view.sidebar.alphabet_input.setText("a, ε")
    view.sidebar.apply_alphabet_button.click()
    qapp.processEvents()

    assert model.automaton.alphabet == frozenset()
    assert view.sidebar.alphabet_input.text() == ""
    assert "no admite" in view.statusBar().currentMessage()

    controller.deleteLater()
    view.close()


def test_transition_creation_adds_model_and_graphics_item(
    qapp: QApplication,
    monkeypatch,
) -> None:
    model, view, controller = _build_editor()
    view.alphabet_changed.emit(["a", "b"])
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    monkeypatch.setattr(view, "request_transition_symbol", lambda *_: "a")

    view.toolbar.add_transition_action.trigger()
    view.transition_requested.emit("q0", "q1")
    qapp.processEvents()

    assert len(model.automaton.transitions) == 1
    transition = model.automaton.transitions[0]
    assert transition.symbols == {"a"}
    item = view.scene.transition_item("q0", "q1")
    assert item.symbols == frozenset({"a"})
    assert not item.path().isEmpty()

    controller.deleteLater()
    view.close()


def test_symbols_between_same_pair_share_one_edge(
    qapp: QApplication,
    monkeypatch,
) -> None:
    model, view, controller = _build_editor()
    view.alphabet_changed.emit(["a", "b"])
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    symbols = iter(["a", "b"])
    monkeypatch.setattr(view, "request_transition_symbol", lambda *_: next(symbols))

    view.transition_requested.emit("q0", "q1")
    view.transition_requested.emit("q0", "q1")
    qapp.processEvents()

    assert len(model.automaton.transitions) == 1
    assert model.automaton.transitions[0].symbols == {"a", "b"}
    assert view.scene.transition_item("q0", "q1").symbols == frozenset({"a", "b"})

    controller.deleteLater()
    view.close()


def test_dfa_rejects_same_symbol_to_different_destination(
    qapp: QApplication,
    monkeypatch,
) -> None:
    model, view, controller = _build_editor()
    view.alphabet_changed.emit(["a"])
    _add_states(
        model,
        view,
        qapp,
        (180.0, 180.0),
        (430.0, 160.0),
        (430.0, 340.0),
    )
    monkeypatch.setattr(view, "request_transition_symbol", lambda *_: "a")

    view.transition_requested.emit("q0", "q1")
    view.transition_requested.emit("q0", "q2")
    qapp.processEvents()

    assert len(model.automaton.transitions) == 1
    assert model.automaton.destinations("q0", "a") == frozenset({"q1"})
    assert "ya tiene una transición" in view.statusBar().currentMessage()

    controller.deleteLater()
    view.close()


def test_nfa_allows_same_symbol_to_multiple_destinations(
    qapp: QApplication,
    monkeypatch,
) -> None:
    model, view, controller = _build_editor()
    view.sidebar.automaton_type_combo.setCurrentText("AFN")
    view.alphabet_changed.emit(["a"])
    _add_states(
        model,
        view,
        qapp,
        (180.0, 180.0),
        (430.0, 160.0),
        (430.0, 340.0),
    )
    monkeypatch.setattr(view, "request_transition_symbol", lambda *_: "a")

    view.transition_requested.emit("q0", "q1")
    view.transition_requested.emit("q0", "q2")
    qapp.processEvents()

    assert len(model.automaton.transitions) == 2
    assert model.automaton.destinations("q0", "a") == frozenset({"q1", "q2"})
    assert view.scene.transition_item("q0", "q1").symbols == frozenset({"a"})
    assert view.scene.transition_item("q0", "q2").symbols == frozenset({"a"})

    controller.deleteLater()
    view.close()


def test_self_loop_is_drawn(qapp: QApplication, monkeypatch) -> None:
    model, view, controller = _build_editor()
    view.alphabet_changed.emit(["a"])
    _add_states(model, view, qapp, (320.0, 300.0))
    monkeypatch.setattr(view, "request_transition_symbol", lambda *_: "a")

    view.transition_requested.emit("q0", "q0")
    qapp.processEvents()

    item = view.scene.transition_item("q0", "q0")
    assert not item.path().isEmpty()
    assert item.path().boundingRect().top() < view.scene.state_item("q0").pos().y()

    controller.deleteLater()
    view.close()


def test_moving_state_recalculates_connected_transition(
    qapp: QApplication,
    monkeypatch,
) -> None:
    model, view, controller = _build_editor()
    view.alphabet_changed.emit(["a"])
    _add_states(model, view, qapp, (180.0, 180.0), (430.0, 260.0))
    monkeypatch.setattr(view, "request_transition_symbol", lambda *_: "a")
    view.transition_requested.emit("q0", "q1")
    qapp.processEvents()

    transition_item = view.scene.transition_item("q0", "q1")
    before = transition_item.path().boundingRect()
    view.scene.state_item("q1").setPos(QPointF(650.0, 420.0))
    qapp.processEvents()
    after = transition_item.path().boundingRect()

    assert before != after
    assert model.automaton.get_state("q1").x == 650.0
    assert model.automaton.get_state("q1").y == 420.0

    controller.deleteLater()
    view.close()


def test_bidirectional_transitions_use_distinct_curves(
    qapp: QApplication,
    monkeypatch,
) -> None:
    model, view, controller = _build_editor()
    view.alphabet_changed.emit(["a", "b"])
    _add_states(model, view, qapp, (180.0, 220.0), (500.0, 220.0))
    symbols = iter(["a", "b"])
    monkeypatch.setattr(view, "request_transition_symbol", lambda *_: next(symbols))

    view.transition_requested.emit("q0", "q1")
    view.transition_requested.emit("q1", "q0")
    qapp.processEvents()

    forward = view.scene.transition_item("q0", "q1").path().boundingRect()
    reverse = view.scene.transition_item("q1", "q0").path().boundingRect()
    assert forward != reverse

    controller.deleteLater()
    view.close()
