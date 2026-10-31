"""Top-level controller for the automaton editor."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QTimer

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.model.editor_session import EditorSession
from app_automatas.model.exceptions import (
    AlphabetSymbolInUseError,
    DuplicateStateError,
    DuplicateTransitionError,
    InvalidSymbolError,
    UnknownTransitionError,
)
from app_automatas.services.nfa_to_dfa import NFAConversionError, convert_nfa_to_dfa
from app_automatas.services.persistence import PersistenceError, load_automaton, save_automaton
from app_automatas.services.regular_equations import automaton_to_regular_expression
from app_automatas.services.simulation import (
    DFASimulator,
    NFASimulator,
    InvalidSimulationAutomatonError,
    InvalidSimulationInputError,
    NFASimulationSnapshot,
)
from app_automatas.services.validation import validate_automaton
from app_automatas.view.main_window import MainWindow


class AppController(QObject):
    """Coordinate the editor model and main window."""

    def __init__(self, model: EditorSession, view: MainWindow) -> None:
        super().__init__()
        self._model = model
        self._view = view
        self._simulator: DFASimulator | NFASimulator | None = None
        self._simulation_timer = QTimer(self)
        self._simulation_timer.setInterval(900)
        self._simulation_timer.timeout.connect(self._advance_simulation)

        self._view.automaton_type_changed.connect(self._on_automaton_type_changed)
        self._view.alphabet_changed.connect(self._on_alphabet_changed)
        self._view.editor_tool_changed.connect(self._on_editor_tool_changed)
        self._view.theme_changed.connect(self._on_theme_changed)
        self._view.clear_requested.connect(self._on_clear_requested)
        self._view.validation_requested.connect(self._on_validation_requested)
        self._view.conversion_requested.connect(self._on_conversion_requested)
        self._view.regular_expression_requested.connect(
            self._on_regular_expression_requested
        )
        self._view.open_requested.connect(self._on_open_requested)
        self._view.save_requested.connect(self._on_save_requested)
        self._view.simulation_start_requested.connect(self._on_simulation_start_requested)
        self._view.simulation_next_requested.connect(self._on_simulation_next_requested)
        self._view.simulation_play_requested.connect(self._on_simulation_play_requested)
        self._view.simulation_pause_requested.connect(self._on_simulation_pause_requested)
        self._view.simulation_reset_requested.connect(self._on_simulation_reset_requested)
        self._view.canvas_clicked.connect(self._on_canvas_clicked)
        self._view.state_selected.connect(self._on_state_selected)
        self._view.state_moved.connect(self._on_state_moved)
        self._view.state_initial_changed.connect(self._on_state_initial_changed)
        self._view.state_accepting_changed.connect(self._on_state_accepting_changed)
        self._view.state_rename_requested.connect(self._on_state_rename_requested)
        self._view.state_delete_requested.connect(self._on_state_delete_requested)
        self._view.transition_source_changed.connect(self._on_transition_source_changed)
        self._view.transition_requested.connect(self._on_transition_requested)
        self._view.transition_selected.connect(self._on_transition_selected)
        self._view.transition_symbols_changed.connect(
            self._on_transition_symbols_changed
        )
        self._view.transition_delete_requested.connect(
            self._on_transition_delete_requested
        )
        self._sync_view()

    def show(self) -> None:
        """Display the main window."""
        self._view.show()

    def _sync_view(self) -> None:
        self._view.set_automaton_type(self._model.automaton_type)
        self._view.set_alphabet(self._model.automaton.alphabet)
        self._view.set_theme(self._model.theme_mode)
        self._view.set_editor_tool(self._model.editor_tool)
        self._view.set_simulation_automaton_type(self._model.automaton_type)
        self._view.set_conversion_available(isinstance(self._model.automaton, NFA))
        self._view.show_status(f"Modo de edición: {self._model.automaton_type}")

    def _on_automaton_type_changed(self, automaton_type: str) -> None:
        try:
            self._model.set_automaton_type(automaton_type)
        except ValueError:
            self._view.set_automaton_type(self._model.automaton_type)
            self._view.show_status(
                "No se puede cambiar el tipo mientras el autómata tenga estados"
            )
            return
        self._invalidate_simulation()
        self._view.set_alphabet(self._model.automaton.alphabet)
        self._view.set_simulation_automaton_type(self._model.automaton_type)
        self._view.set_conversion_available(isinstance(self._model.automaton, NFA))
        self._view.show_status(f"Modo de edición: {self._model.automaton_type}")

    def _on_alphabet_changed(self, symbols: object) -> None:
        if not isinstance(symbols, list) or not all(
            isinstance(symbol, str) for symbol in symbols
        ):
            return
        try:
            self._model.automaton.set_alphabet(symbols)
        except AlphabetSymbolInUseError as exc:
            if not self._view.confirm_alphabet_symbol_removal(exc.symbols):
                self._view.set_alphabet(self._model.automaton.alphabet)
                self._view.show_status("Modificación del alfabeto cancelada")
                return
            self._model.automaton.set_alphabet(
                symbols,
                remove_invalid_transitions=True,
            )
            self._view.rebuild_automaton(
                self._model.automaton.states,
                self._model.automaton.transitions,
            )
        except InvalidSymbolError:
            self._view.set_alphabet(self._model.automaton.alphabet)
            self._view.show_status("El alfabeto no admite símbolos vacíos ni ε")
            return

        self._invalidate_simulation()
        self._view.set_alphabet(self._model.automaton.alphabet)
        if self._model.automaton.alphabet:
            rendered = ", ".join(sorted(self._model.automaton.alphabet))
            self._view.show_status(f"Alfabeto actualizado: {{{rendered}}}")
        else:
            self._view.show_status("Alfabeto vacío")

    def _on_editor_tool_changed(self, editor_tool: str) -> None:
        self._model.set_editor_tool(editor_tool)
        self._view.set_editor_tool(self._model.editor_tool)
        labels = {
            "select": "Seleccionar",
            "state": "Estado",
            "transition": "Transición",
        }
        self._view.show_status(f"Herramienta activa: {labels[editor_tool]}")

    def _on_theme_changed(self, theme_mode: str) -> None:
        self._model.set_theme_mode(theme_mode)
        self._view.set_theme(self._model.theme_mode)
        theme_label = "oscuro" if self._model.theme_mode == "dark" else "claro"
        self._view.show_status(f"Tema {theme_label} activado")

    def _on_validation_requested(self) -> None:
        result = validate_automaton(self._model.automaton)
        self._view.show_validation_result(
            self._model.automaton_type,
            result.is_valid,
            result.messages,
        )
        if result.is_valid:
            self._view.show_status("Autómata válido: listo para simular")
        else:
            count = len(result.issues)
            suffix = "problema" if count == 1 else "problemas"
            self._view.show_status(
                f"Validación pendiente: {count} {suffix} por corregir"
            )

    def _on_save_requested(self) -> None:
        path = self._view.request_save_automaton_path()
        if path is None:
            self._view.show_status("Guardado cancelado")
            return
        try:
            saved_path = save_automaton(path, self._model.automaton)
        except PersistenceError as exc:
            self._view.show_persistence_error(str(exc))
            self._view.show_status("No se pudo guardar el autómata")
            return
        self._view.show_status(f"Autómata guardado en {saved_path.name}")

    def _on_open_requested(self) -> None:
        path = self._view.request_open_automaton_path()
        if path is None:
            self._view.show_status("Apertura cancelada")
            return
        try:
            loaded = load_automaton(path)
        except PersistenceError as exc:
            self._view.show_persistence_error(str(exc))
            self._view.show_status("No se pudo abrir el autómata")
            return

        current = self._model.automaton
        if (not current.is_empty or current.alphabet) and not self._view.confirm_replace_automaton():
            self._view.show_status("Apertura cancelada")
            return

        self._stop_simulation_timer()
        self._simulator = None
        self._model.replace_automaton(loaded)
        self._view.set_automaton_type(self._model.automaton_type)
        self._view.set_alphabet(loaded.alphabet)
        self._view.set_editor_tool(self._model.editor_tool)
        self._view.set_simulation_automaton_type(self._model.automaton_type)
        self._view.set_conversion_available(isinstance(loaded, NFA))
        self._view.rebuild_automaton(loaded.states, loaded.transitions)
        self._view.show_selected_state(None)
        self._view.show_selected_transition(None)
        self._view.reset_simulation_display()
        self._view.show_status(f"Autómata abierto: {Path(path).name}")

    def _on_conversion_requested(self) -> None:
        automaton = self._model.automaton
        if not isinstance(automaton, NFA):
            self._view.show_status("La conversión por subconjuntos está disponible para AFN")
            return

        try:
            generated = convert_nfa_to_dfa(automaton)
        except NFAConversionError as exc:
            self._view.show_validation_result(
                self._model.automaton_type,
                False,
                exc.messages,
            )
            self._view.show_status("Corrige el AFN antes de convertirlo a AFD")
            return

        self._view.show_converted_automaton(generated, source_nfa=automaton)
        self._view.show_status(
            f"AFD generado: {len(generated.states)} estados por subconjuntos"
        )

    def _on_regular_expression_requested(self) -> None:
        automaton = self._model.automaton
        validation = validate_automaton(automaton)
        if not validation.is_valid:
            messages = tuple(
                message.replace(
                    "antes de iniciar una simulación",
                    "antes de obtener la expresión regular",
                )
                for message in validation.messages
            )
            self._view.show_regular_expression_error(messages)
            self._view.show_status(
                "Corrige el autómata antes de obtener la expresión regular"
            )
            return

        try:
            solution = automaton_to_regular_expression(automaton)
        except (ValueError, RuntimeError):
            self._view.show_regular_expression_error(
                (
                    "No fue posible completar el método de ecuaciones para el "
                    "autómata actual.",
                )
            )
            self._view.show_status("No se pudo obtener la expresión regular")
            return

        self._view.show_regular_expression_process(solution)
        self._view.show_status(
            f"Expresión regular obtenida para {automaton.automaton_type}"
        )

    def _on_simulation_start_requested(self, input_string: str) -> None:
        automaton = self._model.automaton
        validation = validate_automaton(automaton)
        if not validation.is_valid:
            self._view.show_validation_result(
                self._model.automaton_type,
                False,
                validation.messages,
            )
            self._view.show_status("Corrige el autómata antes de iniciar la simulación")
            return

        self._stop_simulation_timer()
        self._simulator = None
        self._view.reset_simulation_display()
        try:
            if isinstance(automaton, DFA):
                self._simulator = DFASimulator(automaton)
            elif isinstance(automaton, NFA):
                self._simulator = NFASimulator(automaton)
            else:
                raise TypeError("Unsupported automaton type")
            snapshot = self._simulator.start(input_string)
        except InvalidSimulationInputError as exc:
            self._simulator = None
            rendered = ", ".join(sorted(exc.symbols))
            self._view.show_simulation_error(
                f"La cadena contiene símbolos que no pertenecen al alfabeto: {rendered}."
            )
            self._view.show_status("Cadena inválida para el alfabeto actual")
            return
        except InvalidSimulationAutomatonError as exc:
            self._simulator = None
            self._view.show_simulation_error("\n".join(exc.messages))
            return

        self._view.show_simulation_snapshot(snapshot)
        if snapshot.is_finished:
            self._show_simulation_outcome(snapshot.status)
        elif isinstance(snapshot, NFASimulationSnapshot):
            rendered = ", ".join(sorted(snapshot.active_state_ids))
            self._view.show_status(
                f"Simulación preparada; estados activos: {rendered}; "
                f"siguiente símbolo: {snapshot.next_symbol}"
            )
        else:
            self._view.show_status(
                f"Simulación preparada en {snapshot.current_state_id}; "
                f"siguiente símbolo: {snapshot.next_symbol}"
            )

    def _on_simulation_next_requested(self) -> None:
        if self._simulator is None:
            return
        self._stop_simulation_timer()
        self._advance_simulation()

    def _on_simulation_play_requested(self) -> None:
        if self._simulator is None:
            return
        snapshot = self._simulator.snapshot
        if snapshot.is_finished:
            return
        self._simulation_timer.start()
        self._view.set_simulation_playing(True, snapshot)
        self._view.show_status("Simulación automática en curso")

    def _on_simulation_pause_requested(self) -> None:
        if self._simulator is None:
            return
        self._stop_simulation_timer()
        self._view.set_simulation_playing(False, self._simulator.snapshot)
        self._view.show_status("Simulación pausada")

    def _on_simulation_reset_requested(self) -> None:
        if self._simulator is None:
            return
        self._stop_simulation_timer()
        snapshot = self._simulator.reset()
        self._view.show_simulation_snapshot(snapshot)
        if snapshot.is_finished:
            self._show_simulation_outcome(snapshot.status)
        else:
            self._view.show_status("Simulación reiniciada")

    def _advance_simulation(self) -> None:
        if self._simulator is None:
            self._stop_simulation_timer()
            return
        snapshot = self._simulator.step()
        playing = self._simulation_timer.isActive() and not snapshot.is_finished
        self._view.show_simulation_snapshot(snapshot, playing=playing)

        if snapshot.is_finished:
            self._stop_simulation_timer()
            self._show_simulation_outcome(snapshot.status)
            return

        if isinstance(snapshot, NFASimulationSnapshot):
            if snapshot.last_transitions:
                rendered = "; ".join(
                    f"{source} → {target}"
                    for source, target in snapshot.last_transitions
                )
                self._view.show_status(
                    f"{rendered} con '{snapshot.last_symbol}'"
                )
        elif snapshot.last_transition is not None:
            source_id, target_id = snapshot.last_transition
            self._view.show_status(
                f"{source_id} → {target_id} con '{snapshot.last_symbol}'"
            )

    def _show_simulation_outcome(self, status: str) -> None:
        if status == "accepted":
            self._view.show_status("Cadena aceptada")
        else:
            self._view.show_status("Cadena rechazada")

    def _stop_simulation_timer(self) -> None:
        if self._simulation_timer.isActive():
            self._simulation_timer.stop()

    def _invalidate_simulation(self) -> None:
        self._stop_simulation_timer()
        if self._simulator is None:
            return
        self._simulator = None
        self._view.reset_simulation_display()

    def _on_clear_requested(self) -> None:
        automaton = self._model.automaton
        if automaton.is_empty and not automaton.alphabet:
            self._view.show_status("El autómata ya está vacío")
            return
        if not self._view.confirm_clear_automaton():
            self._view.show_status("Limpieza cancelada")
            return

        self._invalidate_simulation()
        automaton.clear()
        self._view.rebuild_automaton(automaton.states, automaton.transitions)
        self._view.set_alphabet(automaton.alphabet)
        self._view.show_selected_state(None)
        self._view.show_selected_transition(None)
        self._view.show_status("Autómata limpiado")

    def _on_canvas_clicked(self, x: float, y: float) -> None:
        if self._model.editor_tool != "state":
            return
        state = self._model.automaton.add_state(x=x, y=y)
        self._invalidate_simulation()
        self._view.add_state(state)
        self._view.show_status(f"Estado {state.identifier} creado")

    def _on_state_selected(self, identifier: object) -> None:
        if identifier is None:
            self._view.show_selected_state(None)
            return
        if not isinstance(identifier, str):
            return
        state = self._model.automaton.get_state(identifier)
        self._view.show_selected_state(state)
        self._view.show_status(f"Estado seleccionado: {state.identifier}")

    def _on_state_moved(self, identifier: str, x: float, y: float) -> None:
        state = self._model.automaton.get_state(identifier)
        state.set_position(x, y)

    def _on_state_initial_changed(self, identifier: str, checked: bool) -> None:
        state = self._model.automaton.get_state(identifier)
        if checked:
            self._model.automaton.set_initial_state(identifier)
        elif state.is_initial:
            self._model.automaton.set_initial_state(None)

        self._invalidate_simulation()
        self._view.refresh_states(self._model.automaton.states)
        self._view.show_selected_state(state)
        self._view.show_status(
            f"{state.identifier} "
            + ("es el estado inicial" if state.is_initial else "ya no es el estado inicial")
        )

    def _on_state_accepting_changed(self, identifier: str, checked: bool) -> None:
        self._model.automaton.set_accepting(identifier, checked)
        self._invalidate_simulation()
        state = self._model.automaton.get_state(identifier)
        self._view.refresh_state(state)
        self._view.show_status(
            f"{state.identifier} "
            + ("marcado como estado de aceptación" if checked else "ya no es de aceptación")
        )

    def _on_state_rename_requested(
        self,
        current_identifier: str,
        new_identifier: str,
    ) -> None:
        try:
            state = self._model.automaton.rename_state(
                current_identifier,
                new_identifier,
            )
        except DuplicateStateError:
            state = self._model.automaton.get_state(current_identifier)
            self._view.show_selected_state(state)
            self._view.show_status(f"Ya existe un estado llamado {new_identifier}")
            return
        except ValueError:
            state = self._model.automaton.get_state(current_identifier)
            self._view.show_selected_state(state)
            self._view.show_status("El nombre del estado no puede estar vacío")
            return

        self._invalidate_simulation()
        self._view.rebuild_automaton(
            self._model.automaton.states,
            self._model.automaton.transitions,
            selected_state_id=state.identifier,
        )
        self._view.show_selected_state(state)
        self._view.show_status(
            f"Estado {current_identifier} renombrado como {state.identifier}"
        )

    def _on_state_delete_requested(self, identifier: str) -> None:
        if not self._view.confirm_state_deletion(identifier):
            self._view.show_status("Eliminación del estado cancelada")
            return

        self._model.automaton.remove_state(identifier)
        self._invalidate_simulation()
        self._view.rebuild_automaton(
            self._model.automaton.states,
            self._model.automaton.transitions,
        )
        self._view.show_selected_state(None)
        self._view.show_selected_transition(None)
        self._view.show_status(
            f"Estado {identifier} y sus transiciones asociadas eliminados"
        )

    def _on_transition_source_changed(self, identifier: object) -> None:
        if isinstance(identifier, str):
            self._view.show_status(
                f"Origen: {identifier}. Selecciona el estado de destino"
            )

    def _on_transition_requested(self, source_id: str, target_id: str) -> None:
        alphabet = self._model.automaton.alphabet
        if not alphabet:
            self._view.show_status(
                "Define primero el alfabeto antes de crear una transición"
            )
            return

        symbol = self._view.request_transition_symbol(source_id, target_id, alphabet)
        if symbol is None:
            self._view.show_status("Creación de transición cancelada")
            return

        try:
            transition = self._model.automaton.add_transition(
                source_id,
                target_id,
                symbol,
            )
        except DuplicateTransitionError:
            self._view.show_status(
                f"En un AFD, {source_id} ya tiene una transición para '{symbol}'"
            )
            return
        except InvalidSymbolError:
            self._view.show_status(
                f"El símbolo '{symbol}' no pertenece al alfabeto"
            )
            return

        self._invalidate_simulation()
        self._view.add_or_refresh_transition(transition)
        symbols = ", ".join(sorted(transition.symbols))
        self._view.show_status(
            f"Transición {source_id} → {target_id} creada/actualizada: {symbols}"
        )

    def _on_transition_selected(self, transition_key: object) -> None:
        if transition_key is None:
            self._view.show_selected_transition(None)
            return
        if (
            not isinstance(transition_key, tuple)
            or len(transition_key) != 2
            or not all(isinstance(value, str) for value in transition_key)
        ):
            return
        source_id, target_id = transition_key
        try:
            transition = self._model.automaton.get_transition(source_id, target_id)
        except UnknownTransitionError:
            self._view.show_selected_transition(None)
            return
        self._view.show_selected_transition(transition)
        self._view.show_status(f"Transición seleccionada: {source_id} → {target_id}")

    def _on_transition_symbols_changed(
        self,
        source_id: str,
        target_id: str,
        symbols: object,
    ) -> None:
        if not isinstance(symbols, list) or not all(
            isinstance(symbol, str) for symbol in symbols
        ):
            return
        try:
            transition = self._model.automaton.set_transition_symbols(
                source_id,
                target_id,
                symbols,
            )
        except DuplicateTransitionError:
            transition = self._model.automaton.get_transition(source_id, target_id)
            self._view.show_selected_transition(transition)
            self._view.show_status(
                "La edición violaría la regla determinista del AFD"
            )
            return
        except InvalidSymbolError:
            transition = self._model.automaton.get_transition(source_id, target_id)
            self._view.show_selected_transition(transition)
            self._view.show_status(
                "La transición necesita al menos un símbolo válido del alfabeto"
            )
            return
        except UnknownTransitionError:
            self._view.show_selected_transition(None)
            self._view.show_status("La transición seleccionada ya no existe")
            return

        self._invalidate_simulation()
        self._view.rebuild_automaton(
            self._model.automaton.states,
            self._model.automaton.transitions,
            selected_transition=(source_id, target_id),
        )
        self._view.show_selected_transition(transition)
        rendered = ", ".join(sorted(transition.symbols))
        self._view.show_status(
            f"Transición {source_id} → {target_id} actualizada: {rendered}"
        )

    def _on_transition_delete_requested(self, source_id: str, target_id: str) -> None:
        if not self._view.confirm_transition_deletion(source_id, target_id):
            self._view.show_status("Eliminación de la transición cancelada")
            return

        self._model.automaton.remove_transition(source_id, target_id)
        self._invalidate_simulation()
        self._view.rebuild_automaton(
            self._model.automaton.states,
            self._model.automaton.transitions,
        )
        self._view.show_selected_transition(None)
        self._view.show_status(f"Transición {source_id} → {target_id} eliminada")
