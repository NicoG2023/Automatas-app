from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app_automatas.controller.app_controller import AppController
from app_automatas.model.editor_session import EditorSession
from app_automatas.theme.palette import DARK_PALETTE, LIGHT_PALETTE
from app_automatas.view.main_window import MainWindow


def test_main_window_bootstraps_editor_shell(qapp: QApplication) -> None:
    window = MainWindow()

    assert window.windowTitle() == "App de Autómatas"
    assert window.minimumWidth() == 960
    assert window.minimumHeight() == 640
    assert window.scene.sceneRect().width() == 1600
    assert window.scene.sceneRect().height() == 1000
    assert window.sidebar.automaton_type_combo.currentText() == "AFD"
    assert not window.toolbar.theme_action.isChecked()
    assert LIGHT_PALETTE.primary in qapp.styleSheet()

    window.close()


def test_controller_updates_model_when_type_changes(qapp: QApplication) -> None:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)

    view.sidebar.automaton_type_combo.setCurrentText("AFN")
    qapp.processEvents()

    assert model.automaton_type == "AFN"
    assert view.statusBar().currentMessage() == "Modo de edición: AFN"

    controller.deleteLater()
    view.close()


def test_controller_applies_dark_theme(qapp: QApplication) -> None:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)

    view.toolbar.theme_action.setChecked(True)
    qapp.processEvents()

    highlight = qapp.palette().color(QPalette.ColorRole.Highlight)
    assert model.theme_mode == "dark"
    assert view.toolbar.theme_action.isChecked()
    assert DARK_PALETTE.primary in qapp.styleSheet()
    assert highlight == QColor(DARK_PALETTE.primary)
    assert view.statusBar().currentMessage() == "Tema oscuro activado"

    controller.deleteLater()
    view.close()


def test_validation_action_reports_blocking_issues(qapp: QApplication) -> None:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)
    captured: dict[str, object] = {}

    def capture_result(
        automaton_type: str,
        is_valid: bool,
        messages: tuple[str, ...],
    ) -> None:
        captured["automaton_type"] = automaton_type
        captured["is_valid"] = is_valid
        captured["messages"] = messages

    view.show_validation_result = capture_result  # type: ignore[method-assign]
    view.toolbar.validate_action.trigger()
    qapp.processEvents()

    assert captured["automaton_type"] == "AFD"
    assert captured["is_valid"] is False
    assert "Selecciona un estado inicial." in captured["messages"]
    assert "problemas por corregir" in view.statusBar().currentMessage()

    controller.deleteLater()
    view.close()


def test_validation_action_accepts_incomplete_dfa(qapp: QApplication) -> None:
    model = EditorSession()
    model.automaton.set_alphabet(["a", "b"])
    model.automaton.add_state("q0", is_initial=True)
    model.automaton.add_state("q1", is_accepting=True)
    model.automaton.add_transition("q0", "q1", "a")
    view = MainWindow()
    controller = AppController(model=model, view=view)
    captured: dict[str, object] = {}

    def capture_result(
        automaton_type: str,
        is_valid: bool,
        messages: tuple[str, ...],
    ) -> None:
        captured["automaton_type"] = automaton_type
        captured["is_valid"] = is_valid
        captured["messages"] = messages

    view.show_validation_result = capture_result  # type: ignore[method-assign]
    view.toolbar.validate_action.trigger()
    qapp.processEvents()

    assert captured == {
        "automaton_type": "AFD",
        "is_valid": True,
        "messages": (),
    }
    assert view.statusBar().currentMessage() == "Autómata válido: listo para simular"

    controller.deleteLater()
    view.close()
