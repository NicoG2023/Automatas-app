from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QTableWidget

from app_automatas.controller.app_controller import AppController
from app_automatas.model.dfa import DFA
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


def test_conversion_action_is_enabled_only_for_nfa(qapp: QApplication) -> None:
    model = EditorSession()
    view = MainWindow()
    controller = AppController(model=model, view=view)

    assert not view.toolbar.convert_action.isEnabled()

    view.sidebar.automaton_type_combo.setCurrentText("AFN")
    qapp.processEvents()

    assert model.automaton_type == "AFN"
    assert view.toolbar.convert_action.isEnabled()

    controller.deleteLater()
    view.close()


def test_conversion_action_opens_independent_generated_dfa(qapp: QApplication) -> None:
    model = EditorSession(automaton_type="AFN")
    automaton = model.automaton
    automaton.set_alphabet(["a"])
    automaton.add_state("q0", is_initial=True, x=120, y=160)
    automaton.add_state("q1", is_accepting=True, x=360, y=160)
    automaton.add_transition("q0", "q0", "a")
    automaton.add_transition("q0", "q1", "a")

    view = MainWindow()
    controller = AppController(model=model, view=view)
    source_ids = tuple(state.identifier for state in automaton.states)

    view.toolbar.convert_action.trigger()
    qapp.processEvents()

    assert len(view.conversion_dialogs) == 1
    dialog = view.conversion_dialogs[0]
    assert isinstance(dialog.generated_automaton, DFA)
    assert dialog.windowTitle() == "AFD generado desde AFN"
    assert tuple(state.identifier for state in automaton.states) == source_ids
    assert dialog.transition_table.columnCount() == 2
    assert dialog.transition_table.horizontalHeaderItem(0).text() == "Estado"
    assert dialog.transition_table.horizontalHeaderItem(1).text() == "a"
    assert dialog.transition_table.rowCount() == len(dialog.generated_automaton.states)
    assert "AFD generado" in view.statusBar().currentMessage()

    dialog.close()
    qapp.processEvents()
    controller.deleteLater()
    view.close()


def test_conversion_process_walks_through_five_steps(qapp: QApplication) -> None:
    model = EditorSession(automaton_type="AFN")
    automaton = model.automaton
    automaton.set_alphabet(["a", "b"])
    automaton.add_state("q0", is_initial=True, is_accepting=True)
    automaton.add_state("q1")
    automaton.add_state("q2")
    automaton.add_state("q3")
    automaton.add_transition("q0", "q1", "a")
    automaton.add_transition("q0", "q2", "a")
    automaton.add_transition("q1", "q0", "b")
    automaton.add_transition("q2", "q3", "b")
    automaton.add_transition("q3", "q0", "a")

    view = MainWindow()
    controller = AppController(model=model, view=view)

    view.toolbar.convert_action.trigger()
    qapp.processEvents()
    dialog = view.conversion_dialogs[0]

    assert dialog.process_button.isEnabled()
    dialog.process_button.click()
    qapp.processEvents()

    process_dialog = dialog.process_dialog
    assert process_dialog is not None
    assert process_dialog.current_step == 1
    assert process_dialog.pages.count() == 5

    original_table = process_dialog.findChild(
        QTableWidget, "conversionProcessOriginalTable"
    )
    expanded_table = process_dialog.findChild(
        QTableWidget, "conversionProcessExpandedTable"
    )
    renamed_table = process_dialog.findChild(
        QTableWidget, "conversionProcessRenamedTable"
    )
    assert original_table is not None
    assert expanded_table is not None
    assert renamed_table is not None
    assert original_table.rowCount() == 4
    assert expanded_table.rowCount() == 7
    assert renamed_table.item(0, 0).text() == "→* k0"

    assert original_table.columnCount() == 3
    assert original_table.item(0, 1).text() == "{q1,q2}"
    assert original_table.item(0, 2).text() == "∅"
    assert expanded_table.item(4, 1).text() == "∅"
    assert expanded_table.item(4, 2).text() == "{q0,q3}"
    assert expanded_table.item(5, 1).text() == "{q0,q1,q2}"
    assert renamed_table.item(0, 1).text() == "k4"
    assert renamed_table.item(0, 2).text() == "∅"
    assert original_table.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert original_table.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert expanded_table.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert expanded_table.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert renamed_table.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert renamed_table.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff

    for expected_step in range(2, 5):
        process_dialog.next_button.click()
        qapp.processEvents()
        assert process_dialog.current_step == expected_step

    assert process_dialog.current_step == 4
    assert {state.identifier for state in process_dialog.process.complete_dfa.states} == {
        "k0", "k1", "k2", "k3", "k4", "k5", "k6"
    }
    assert process_dialog.complete_scene is not None
    assert process_dialog.next_button.isEnabled()

    process_dialog.next_button.click()
    qapp.processEvents()
    assert process_dialog.current_step == 5
    assert process_dialog.process.reachable_names == ("k0", "k4", "k5", "k6")
    assert set(process_dialog.process.unreachable_names) == {"k1", "k2", "k3"}
    assert {state.identifier for state in process_dialog.process.reachable_dfa.states} == {
        "k0", "k4", "k5", "k6"
    }
    assert process_dialog.final_scene is not None
    assert not process_dialog.next_button.isEnabled()

    process_dialog.close()
    dialog.close()
    qapp.processEvents()
    controller.deleteLater()
    view.close()


def test_toolbar_exposes_json_open_and_save_actions(qapp: QApplication) -> None:
    window = MainWindow()

    assert window.toolbar.open_action.isEnabled()
    assert window.toolbar.save_action.isEnabled()
    assert window.toolbar.open_action.shortcut().toString() == "Ctrl+O"
    assert window.toolbar.save_action.shortcut().toString() == "Ctrl+S"
    assert "JSON" in window.toolbar.open_action.toolTip()
    assert "JSON" in window.toolbar.save_action.toolTip()

    window.close()


def test_controller_saves_current_automaton_to_json(qapp: QApplication, tmp_path) -> None:
    model = EditorSession()
    model.automaton.set_alphabet(["a"])
    model.automaton.add_state("q0", is_initial=True, x=100, y=200)
    view = MainWindow()
    controller = AppController(model=model, view=view)
    path = tmp_path / "guardado.json"
    view.request_save_automaton_path = lambda: str(path)  # type: ignore[method-assign]

    view.toolbar.save_action.trigger()
    qapp.processEvents()

    assert path.exists()
    assert '"automaton_type": "AFD"' in path.read_text(encoding="utf-8")
    assert view.statusBar().currentMessage() == "Autómata guardado en guardado.json"

    controller.deleteLater()
    view.close()


def test_controller_opens_json_and_replaces_editor_document(qapp: QApplication, tmp_path) -> None:
    from app_automatas.model.nfa import NFA
    from app_automatas.services.persistence import save_automaton

    saved = NFA({"a"})
    saved.add_state("inicio", is_initial=True, x=130, y=190)
    saved.add_state("fin", is_accepting=True, x=410, y=190)
    saved.add_transition("inicio", "fin", "a")
    path = save_automaton(tmp_path / "afn.json", saved)

    model = EditorSession()
    model.automaton.add_state("temporal")
    view = MainWindow()
    controller = AppController(model=model, view=view)
    view.request_open_automaton_path = lambda: str(path)  # type: ignore[method-assign]
    view.confirm_replace_automaton = lambda: True  # type: ignore[method-assign]

    view.toolbar.open_action.trigger()
    qapp.processEvents()

    assert model.automaton_type == "AFN"
    assert model.editor_tool == "select"
    assert tuple(state.identifier for state in model.automaton.states) == ("inicio", "fin")
    assert model.automaton.destinations("inicio", "a") == frozenset({"fin"})
    assert view.sidebar.automaton_type_combo.currentText() == "AFN"
    assert view.scene.state_item("inicio") is not None
    assert view.scene.state_item("fin") is not None
    assert view.statusBar().currentMessage() == "Autómata abierto: afn.json"

    controller.deleteLater()
    view.close()
