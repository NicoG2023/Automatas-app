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
