from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTextBrowser

from app_automatas.controller.app_controller import AppController
from app_automatas.model.editor_session import EditorSession
from app_automatas.view.main_window import MainWindow


def _build_cc3_editor() -> tuple[EditorSession, MainWindow, AppController]:
    model = EditorSession(automaton_type="AFN")
    automaton = model.automaton
    automaton.set_alphabet(["a", "b"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    automaton.add_state("q2", is_accepting=True)
    automaton.add_state("q3", is_accepting=True)
    automaton.add_state("q4")
    automaton.add_transition("q0", "q1", "b")
    automaton.add_transition("q1", "q1", "b")
    automaton.add_transition("q1", "q2", "a")
    automaton.add_transition("q2", "q3", "b")
    automaton.add_transition("q3", "q4", "a")
    automaton.add_transition("q4", "q3", "b")
    automaton.add_transition("q4", "q1", "b")

    view = MainWindow()
    controller = AppController(model=model, view=view)
    return model, view, controller


def test_regex_action_opens_cc3_process_dialog(qapp: QApplication) -> None:
    _model, view, controller = _build_cc3_editor()

    view.toolbar.regex_action.trigger()
    qapp.processEvents()

    assert len(view.regular_expression_dialogs) == 1
    dialog = view.regular_expression_dialogs[0]
    assert dialog.windowTitle() == "Autómata → expresión regular"
    assert dialog.current_step == 1
    assert dialog.pages.count() == len(dialog.solution.steps) + 2
    assert dialog.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint

    initial = dialog.findChild(QTextBrowser, "regularExpressionInitialSystem")
    assert initial is not None
    assert "A0 = bA1" in initial.toPlainText()
    assert "A1 = bA1 ∪ aA2" in initial.toPlainText()
    assert "A2 = bA3 ∪ λ" in initial.toPlainText()
    assert "q4 → q3 → q2 → q1 → q0" in initial.toPlainText()

    dialog.next_button.click()
    qapp.processEvents()
    substitution = dialog.pages.currentWidget().findChild(
        QTextBrowser, "regularExpressionSubstitutionStep"
    )
    assert substitution is not None
    assert "A3 = aA4 ∪ λ" in substitution.toPlainText()
    assert "A4 = bA3 ∪ bA1" in substitution.toPlainText()
    assert "A3 = abA3 ∪ abA1 ∪ λ" in substitution.toPlainText()

    dialog.next_button.click()
    qapp.processEvents()
    arden = dialog.pages.currentWidget().findChild(
        QTextBrowser, "regularExpressionArdenStep"
    )
    assert arden is not None
    arden_text = " ".join(arden.toPlainText().split())
    assert "A = ab, X = A3, B = abA1 ∪ λ" in arden_text
    assert "X = AX ∪ B" in arden_text
    assert "X = A*B" in arden_text

    while dialog.next_button.isEnabled():
        dialog.next_button.click()
        qapp.processEvents()

    result = dialog.findChild(QTextBrowser, "regularExpressionFinalResult")
    assert result is not None
    assert dialog.solution.expression.render() in result.toPlainText()
    assert "Expresión regular equivalente" in result.toPlainText()
    assert dialog.solution.render_result() == (
        "A0 = b(b ∪ ab(ab)+)*((ab)+ ∪ a)"
    )

    dialog.summary_button.click()
    qapp.processEvents()
    assert dialog._summary_dialog is not None
    summary = dialog._summary_dialog.findChild(
        QTextBrowser, "regularExpressionSummary"
    )
    assert summary is not None
    assert "Sistema inicial" in summary.toPlainText()
    assert "Aplicar el lema de Arden en A3" in summary.toPlainText()
    assert "A0 = b(b ∪ ab(ab)+)*((ab)+ ∪ a)" in summary.toPlainText()
    dialog._summary_dialog.close()
    qapp.processEvents()

    dialog.close()
    qapp.processEvents()
    assert view.regular_expression_dialogs == ()
    controller.deleteLater()
    view.close()


def test_regex_action_works_for_dfa(qapp: QApplication) -> None:
    model = EditorSession()
    automaton = model.automaton
    automaton.set_alphabet(["a"])
    automaton.add_state("q0", is_initial=True, is_accepting=True)
    automaton.add_transition("q0", "q0", "a")
    view = MainWindow()
    controller = AppController(model=model, view=view)

    view.toolbar.regex_action.trigger()
    qapp.processEvents()

    dialog = view.regular_expression_dialogs[0]
    assert dialog.solution.render_result() == "A0 = a*"

    dialog.close()
    qapp.processEvents()
    controller.deleteLater()
    view.close()


def test_regex_action_reports_invalid_automaton_without_opening_dialog(
    qapp: QApplication,
) -> None:
    model = EditorSession()
    model.automaton.add_state("q0")
    view = MainWindow()
    controller = AppController(model=model, view=view)
    captured: dict[str, tuple[str, ...]] = {}

    view.show_regular_expression_error = (  # type: ignore[method-assign]
        lambda messages: captured.setdefault("messages", messages)
    )

    view.toolbar.regex_action.trigger()
    qapp.processEvents()

    assert view.regular_expression_dialogs == ()
    assert "Selecciona un estado inicial." in captured["messages"]
    assert "Corrige el autómata" in view.statusBar().currentMessage()

    controller.deleteLater()
    view.close()


def test_kleene_action_replaces_editor_with_equivalent_nfa(
    qapp: QApplication,
) -> None:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)
    view.request_regular_expression = lambda: ("ab ∪ ba", True)  # type: ignore[method-assign]

    view.toolbar.regex_to_nfa_action.trigger()
    qapp.processEvents()

    assert model.automaton_type == "AFN-λ"
    assert model.automaton.initial_state is not None
    assert model.automaton.alphabet == frozenset({"a", "b"})
    assert view.sidebar.automaton_type_combo.currentText() == "AFN-λ"
    assert view.toolbar.convert_action.isEnabled()
    assert "AFN-λ generado con Kleene" in view.statusBar().currentMessage()
    lambda_edges = [
        edge
        for transition in model.automaton.transitions
        if "λ" in transition.symbols
        for edge in (view.scene.transition_item(
            transition.source.identifier,
            transition.target.identifier,
        ),)
    ]
    assert lambda_edges
    assert all("λ" in edge._label_item.text() for edge in lambda_edges)
    assert len(model.automaton.states) == 9
    assert {state.identifier for state in model.automaton.accepting_states} == {
        "q4",
        "q8",
    }
    assert model.automaton.get_state("q1").y < model.automaton.get_state("q5").y

    controller.deleteLater()
    view.close()


def test_kleene_action_draws_the_reference_star_union_automaton(
    qapp: QApplication,
) -> None:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)
    view.request_regular_expression = lambda: ("a*(ab ∪ ba)*", True)  # type: ignore[method-assign]

    view.toolbar.regex_to_nfa_action.trigger()
    qapp.processEvents()

    automaton = model.automaton
    expected_edges = {
        ("q0", "q0"): {"a"},
        ("q0", "q1"): {"λ"},
        ("q1", "q2"): {"λ"},
        ("q2", "q3"): {"a"},
        ("q3", "q4"): {"λ"},
        ("q4", "q5"): {"b"},
        ("q1", "q6"): {"λ"},
        ("q6", "q7"): {"b"},
        ("q7", "q8"): {"λ"},
        ("q8", "q9"): {"a"},
        ("q5", "q1"): {"λ"},
        ("q9", "q1"): {"λ"},
    }
    assert len(automaton.states) == 10
    assert {state.identifier for state in automaton.accepting_states} == {
        "q1",
        "q5",
        "q9",
    }
    assert {
        (transition.source.identifier, transition.target.identifier):
        transition.symbols
        for transition in automaton.transitions
    } == expected_edges
    assert all(
        view.scene.transition_item(
            transition.source.identifier,
            transition.target.identifier,
        )._label_item.text()
        == ", ".join(sorted(transition.symbols))
        for transition in automaton.transitions
    )

    controller.deleteLater()
    view.close()


def test_kleene_action_reports_invalid_expression(
    qapp: QApplication,
) -> None:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)
    view.request_regular_expression = lambda: ("a|", True)  # type: ignore[method-assign]
    captured: list[str] = []
    view.show_regular_expression_to_nfa_error = captured.append  # type: ignore[method-assign]

    view.toolbar.regex_to_nfa_action.trigger()
    qapp.processEvents()

    assert model.automaton.is_empty
    assert captured
    assert "posición" in captured[0]
    assert "sintaxis" in view.statusBar().currentMessage()

    controller.deleteLater()
    view.close()
