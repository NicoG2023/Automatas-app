"""Main desktop window."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.model.state import State
from app_automatas.model.transition import Transition
from app_automatas.services.regular_equations import RegularEquationSolution
from app_automatas.theme.manager import apply_theme
from app_automatas.view.canvas.automaton_scene import AutomatonScene
from app_automatas.view.canvas.automaton_view import AutomatonView
from app_automatas.view.canvas.transition_item import TransitionItem
from app_automatas.view.dialogs.conversion_dialog import ConversionDialog
from app_automatas.view.dialogs.regular_expression_process_dialog import (
    RegularExpressionProcessDialog,
)
from app_automatas.view.widgets.editor_sidebar import EditorSidebar
from app_automatas.view.widgets.editor_toolbar import EditorToolBar
from app_automatas.view.widgets.simulation_panel import SimulationPanel


class MainWindow(QMainWindow):
    """Top-level view for the automaton editor."""

    automaton_type_changed = Signal(str)
    alphabet_changed = Signal(object)
    editor_tool_changed = Signal(str)
    theme_changed = Signal(str)
    clear_requested = Signal()
    validation_requested = Signal()
    conversion_requested = Signal()
    regular_expression_requested = Signal()
    regular_expression_to_nfa_requested = Signal()
    open_requested = Signal()
    save_requested = Signal()
    canvas_clicked = Signal(float, float)
    state_selected = Signal(object)
    state_moved = Signal(str, float, float)
    state_initial_changed = Signal(str, bool)
    state_accepting_changed = Signal(str, bool)
    state_rename_requested = Signal(str, str)
    state_delete_requested = Signal(str)
    transition_source_changed = Signal(object)
    transition_requested = Signal(str, str)
    transition_selected = Signal(object)
    transition_symbols_changed = Signal(str, str, object)
    transition_delete_requested = Signal(str, str)
    simulation_start_requested = Signal(str)
    simulation_next_requested = Signal()
    simulation_play_requested = Signal()
    simulation_pause_requested = Signal()
    simulation_reset_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("App de Autómatas")
        self.setMinimumSize(960, 640)
        self.resize(1280, 800)
        self._theme_mode = "light"
        self._conversion_dialogs: list[ConversionDialog] = []
        self._regular_expression_dialogs: list[RegularExpressionProcessDialog] = []

        self.scene = AutomatonScene()
        self.canvas = AutomatonView(self.scene)
        self.canvas.enable_zoom_mode(auto_fit=False)
        self.sidebar = EditorSidebar()
        self.sidebar_scroll_area = self._build_sidebar_scroll_area()
        self.toolbar = EditorToolBar()
        self.simulation_panel = SimulationPanel()

        self.sidebar.automaton_type_changed.connect(self.automaton_type_changed.emit)
        self.sidebar.alphabet_changed.connect(self.alphabet_changed.emit)
        self.sidebar.state_initial_changed.connect(self.state_initial_changed.emit)
        self.sidebar.state_accepting_changed.connect(self.state_accepting_changed.emit)
        self.sidebar.state_rename_requested.connect(self.state_rename_requested.emit)
        self.sidebar.state_delete_requested.connect(self.state_delete_requested.emit)
        self.sidebar.transition_symbols_changed.connect(
            self.transition_symbols_changed.emit
        )
        self.sidebar.transition_delete_requested.connect(
            self.transition_delete_requested.emit
        )
        self.toolbar.tool_changed.connect(self.editor_tool_changed.emit)
        self.toolbar.theme_changed.connect(self.theme_changed.emit)
        self.toolbar.clear_requested.connect(self.clear_requested.emit)
        self.toolbar.validation_requested.connect(self.validation_requested.emit)
        self.toolbar.conversion_requested.connect(self.conversion_requested.emit)
        self.toolbar.regular_expression_requested.connect(
            self.regular_expression_requested.emit
        )
        self.toolbar.regular_expression_to_nfa_requested.connect(
            self.regular_expression_to_nfa_requested.emit
        )
        self.toolbar.open_requested.connect(self.open_requested.emit)
        self.toolbar.save_requested.connect(self.save_requested.emit)
        self.simulation_panel.start_requested.connect(self.simulation_start_requested.emit)
        self.simulation_panel.next_requested.connect(self.simulation_next_requested.emit)
        self.simulation_panel.play_requested.connect(self.simulation_play_requested.emit)
        self.simulation_panel.pause_requested.connect(self.simulation_pause_requested.emit)
        self.simulation_panel.reset_requested.connect(self.simulation_reset_requested.emit)
        self.scene.canvas_clicked.connect(self.canvas_clicked.emit)
        self.scene.selected_state_changed.connect(self.state_selected.emit)
        self.scene.selected_transition_changed.connect(self.transition_selected.emit)
        self.scene.state_position_changed.connect(self.state_moved.emit)
        self.scene.transition_source_changed.connect(self.transition_source_changed.emit)
        self.scene.transition_requested.connect(self.transition_requested.emit)

        self.addToolBar(self.toolbar)
        self.setCentralWidget(self._build_central_widget())
        self.statusBar().showMessage("Listo")
        self.set_theme("light")


    def _build_sidebar_scroll_area(self) -> QScrollArea:
        scroll_area = QScrollArea()
        scroll_area.setObjectName("sidebarScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(self.sidebar)
        return scroll_area

    def _build_central_widget(self) -> QWidget:
        central_widget = QWidget()
        central_widget.setObjectName("centralArea")
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(self.sidebar_scroll_area)

        editor_area = QWidget()
        editor_area.setObjectName("editorArea")
        editor_layout = QVBoxLayout(editor_area)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(12)
        editor_layout.addWidget(self.canvas, 1)
        editor_layout.addWidget(self.simulation_panel)
        layout.addWidget(editor_area, 1)
        return central_widget

    def set_automaton_type(self, automaton_type: str) -> None:
        self.sidebar.set_automaton_type(automaton_type)

    def set_alphabet(self, symbols: frozenset[str] | set[str]) -> None:
        self.sidebar.set_alphabet(symbols)

    def set_editor_tool(self, editor_tool: str) -> None:
        self.toolbar.set_editor_tool(editor_tool)
        self.canvas.set_editor_tool(editor_tool)
        self.scene.set_editor_tool(editor_tool)

    def set_simulation_automaton_type(self, automaton_type: str) -> None:
        self.simulation_panel.set_automaton_type(automaton_type)

    def set_conversion_available(self, available: bool) -> None:
        self.toolbar.set_conversion_available(available)

    @property
    def conversion_dialogs(self) -> tuple[ConversionDialog, ...]:
        return tuple(self._conversion_dialogs)

    def show_converted_automaton(
        self,
        automaton: DFA,
        source_nfa: NFA | None = None,
    ) -> ConversionDialog:
        """Open the generated DFA in an independent movable canvas."""
        dialog = ConversionDialog(
            automaton,
            self._theme_mode,
            self,
            source_nfa=source_nfa,
        )
        self._conversion_dialogs.append(dialog)
        dialog.finished.connect(
            lambda _result, current=dialog: self._remove_conversion_dialog(current)
        )
        dialog.show()
        return dialog

    def _remove_conversion_dialog(self, dialog: ConversionDialog) -> None:
        if dialog in self._conversion_dialogs:
            self._conversion_dialogs.remove(dialog)

    @property
    def regular_expression_dialogs(self) -> tuple[RegularExpressionProcessDialog, ...]:
        return tuple(self._regular_expression_dialogs)

    def show_regular_expression_process(
        self,
        solution: RegularEquationSolution,
    ) -> RegularExpressionProcessDialog:
        """Open the pedagogical automaton-to-regex process in its own dialog."""
        dialog = RegularExpressionProcessDialog(solution, self)
        self._regular_expression_dialogs.append(dialog)
        dialog.finished.connect(
            lambda _result, current=dialog: self._remove_regular_expression_dialog(
                current
            )
        )
        dialog.show()
        return dialog

    def _remove_regular_expression_dialog(
        self,
        dialog: RegularExpressionProcessDialog,
    ) -> None:
        if dialog in self._regular_expression_dialogs:
            self._regular_expression_dialogs.remove(dialog)

    def set_simulation_available(self, available: bool) -> None:
        self.simulation_panel.set_available(available)

    def show_simulation_snapshot(self, snapshot: object, *, playing: bool = False) -> None:
        from app_automatas.services.simulation import (
            DFASimulationSnapshot,
            NFASimulationSnapshot,
        )

        if not isinstance(snapshot, (DFASimulationSnapshot, NFASimulationSnapshot)):
            raise TypeError("Expected a DFA or NFA simulation snapshot")
        self.simulation_panel.show_snapshot(snapshot, playing=playing)
        if isinstance(snapshot, DFASimulationSnapshot):
            if snapshot.is_finished:
                final_transition = (
                    () if snapshot.last_transition is None else (snapshot.last_transition,)
                )
                self.scene.set_simulation_visuals(
                    active_state_ids=(snapshot.current_state_id,),
                    active_transition_keys=final_transition,
                    success_state_ids=snapshot.path_state_ids,
                    success_transition_keys=snapshot.path_transitions,
                    failed_state_ids=snapshot.failed_state_ids,
                    failed_transition_keys=snapshot.failed_transitions,
                )
            else:
                active_transitions = (
                    () if snapshot.last_transition is None else (snapshot.last_transition,)
                )
                self.scene.set_simulation_visuals(
                    active_state_ids=(snapshot.current_state_id,),
                    active_transition_keys=active_transitions,
                    success_state_ids=snapshot.path_state_ids,
                    success_transition_keys=snapshot.path_transitions,
                    failed_state_ids=snapshot.failed_state_ids,
                    failed_transition_keys=snapshot.failed_transitions,
                )
            return

        if snapshot.is_finished:
            self.scene.set_simulation_visuals(
                active_state_ids=snapshot.active_state_ids,
                active_transition_keys=snapshot.last_transitions,
                success_state_ids=snapshot.path_state_ids,
                success_transition_keys=snapshot.path_transitions,
                failed_state_ids=snapshot.failed_state_ids,
                failed_transition_keys=snapshot.failed_transitions,
            )
        else:
            self.scene.set_simulation_visuals(
                active_state_ids=snapshot.active_state_ids,
                active_transition_keys=snapshot.last_transitions,
                success_state_ids=snapshot.path_state_ids,
                success_transition_keys=snapshot.path_transitions,
                failed_state_ids=snapshot.failed_state_ids,
                failed_transition_keys=snapshot.failed_transitions,
            )

    def set_simulation_playing(self, playing: bool, snapshot: object) -> None:
        from app_automatas.services.simulation import (
            DFASimulationSnapshot,
            NFASimulationSnapshot,
        )

        if not isinstance(snapshot, (DFASimulationSnapshot, NFASimulationSnapshot)):
            raise TypeError("Expected a DFA or NFA simulation snapshot")
        self.simulation_panel.set_playing(playing, snapshot)

    def reset_simulation_display(self) -> None:
        self.simulation_panel.set_idle()
        self.scene.clear_simulation_highlight()

    def set_theme(self, theme_mode: str) -> None:
        """Apply a theme globally and synchronize canvas items and toolbar."""
        application = QApplication.instance()
        if application is None:
            raise RuntimeError("A QApplication must exist before applying a theme")
        self._theme_mode = theme_mode
        apply_theme(application, theme_mode)
        self.scene.set_theme(theme_mode)
        self.toolbar.set_theme(theme_mode)
        for dialog in tuple(self._conversion_dialogs):
            dialog.set_theme(theme_mode)

    def add_state(self, state: State) -> None:
        self.scene.add_state_item(state, select=True)

    def add_or_refresh_transition(self, transition: Transition) -> TransitionItem:
        return self.scene.add_or_refresh_transition(transition)

    def rebuild_automaton(
        self,
        states: tuple[State, ...],
        transitions: tuple[Transition, ...],
        *,
        selected_state_id: str | None = None,
        selected_transition: tuple[str, str] | None = None,
    ) -> None:
        """Recreate canvas items from the model after structural edits."""
        self.scene.rebuild_automaton(
            states,
            transitions,
            selected_state_id=selected_state_id,
            selected_transition=selected_transition,
        )

    def refresh_state(self, state: State) -> None:
        self.scene.refresh_state(state)
        self.show_selected_state(state)

    def refresh_states(self, states: tuple[State, ...]) -> None:
        self.scene.refresh_states(states)
        selected = next(
            (
                state
                for state in states
                if self.scene.state_item(state.identifier).isSelected()
            ),
            None,
        )
        if selected is not None:
            self.show_selected_state(selected)

    def show_selected_state(self, state: State | None) -> None:
        self.sidebar.show_state(state)
        if state is not None:
            self.sidebar.show_transition(None)

    def show_selected_transition(self, transition: Transition | None) -> None:
        self.sidebar.show_transition(transition)
        if transition is not None:
            self.sidebar.show_state(None)

    def request_transition_symbol(
        self,
        source_id: str,
        target_id: str,
        alphabet: frozenset[str],
    ) -> str | None:
        """Ask the user which existing alphabet symbol belongs to a new edge."""
        if not alphabet:
            return None
        symbols = sorted(alphabet)
        symbol, accepted = QInputDialog.getItem(
            self,
            "Crear transición",
            f"Símbolo para {source_id} → {target_id}:",
            symbols,
            0,
            False,
        )
        return symbol if accepted else None

    def confirm_alphabet_symbol_removal(self, symbols: frozenset[str]) -> bool:
        """Warn before removing symbols currently used by transitions."""
        rendered = ", ".join(sorted(symbols))
        answer = QMessageBox.question(
            self,
            "Modificar alfabeto",
            (
                f"Los símbolos {rendered} están siendo usados por transiciones.\n\n"
                "Si continúas, se eliminarán de las transiciones afectadas y cualquier "
                "transición que quede sin símbolos también será eliminada."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def confirm_state_deletion(self, identifier: str) -> bool:
        """Confirm deletion of a state and every connected transition."""
        answer = QMessageBox.question(
            self,
            "Eliminar estado",
            (
                f"¿Eliminar el estado {identifier}?\n\n"
                "También se eliminarán todas sus transiciones asociadas."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def confirm_transition_deletion(self, source_id: str, target_id: str) -> bool:
        """Confirm deletion of one complete graphical transition."""
        answer = QMessageBox.question(
            self,
            "Eliminar transición",
            f"¿Eliminar la transición {source_id} → {target_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def request_open_automaton_path(self) -> str | None:
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Abrir autómata",
            "",
            "Autómatas JSON (*.json);;Todos los archivos (*)",
        )
        return path or None

    def request_save_automaton_path(self) -> str | None:
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Guardar autómata",
            "automata.json",
            "Autómatas JSON (*.json)",
        )
        return path or None

    def confirm_replace_automaton(self) -> bool:
        answer = QMessageBox.question(
            self,
            "Abrir autómata",
            "El autómata actual será reemplazado. ¿Deseas continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def show_persistence_error(self, message: str) -> None:
        QMessageBox.warning(self, "Archivo de autómata", message)

    def confirm_clear_automaton(self) -> bool:
        """Confirm clearing the complete current automaton."""
        answer = QMessageBox.question(
            self,
            "Limpiar autómata",
            "¿Eliminar el alfabeto, todos los estados y todas las transiciones?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes


    def show_validation_result(
        self,
        automaton_type: str,
        is_valid: bool,
        messages: tuple[str, ...],
    ) -> None:
        """Present structural validation without exposing technical exceptions."""
        dialog = QMessageBox(self)
        dialog.setObjectName("validationDialog")
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)

        if is_valid:
            dialog.setWindowTitle("Autómata válido")
            dialog.setText(f"El {automaton_type} está listo para simular.")
            dialog.setInformativeText(
                "Las transiciones faltantes de un AFD se resolverán como rechazo "
                "cuando corresponda durante la simulación."
                if automaton_type == "AFD"
                else "La estructura actual cumple las reglas necesarias para simular."
            )
        else:
            dialog.setWindowTitle("Revisar autómata")
            dialog.setText("El autómata todavía no está listo para simular.")
            dialog.setInformativeText(
                "\n".join(f"• {message}" for message in messages)
            )

        dialog.exec()

    def show_simulation_error(self, message: str) -> None:
        QMessageBox.warning(self, "No se puede simular", message)

    def show_regular_expression_error(self, messages: tuple[str, ...]) -> None:
        """Explain why the current automaton cannot be converted yet."""
        detail = "\n".join(f"• {message}" for message in messages)
        QMessageBox.warning(
            self,
            "No se puede obtener la expresión regular",
            detail,
        )

    def request_regular_expression(self) -> tuple[str, bool]:
        """Ask for an expression using the notation supported by the parser."""
        return QInputDialog.getText(
            self,
            "Expresión regular a autómata",
            "Expresión (usa | o ∪, concatenación, *, +, paréntesis, λ y ∅):",
        )

    def show_regular_expression_to_nfa_error(self, message: str) -> None:
        QMessageBox.warning(
            self,
            "No se pudo construir el autómata",
            message,
        )

    def show_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
