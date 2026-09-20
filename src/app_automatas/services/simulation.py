"""Pure finite automaton simulation engines for DFA and NFA."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.services.validation import validate_automaton

SimulationStatus = Literal["ready", "running", "accepted", "rejected"]
TransitionKey = tuple[str, str]


class SimulationError(ValueError):
    """Base error for user-correctable simulation problems."""


class InvalidSimulationInputError(SimulationError):
    """Raised when the input string contains symbols outside the alphabet."""

    def __init__(self, symbols: frozenset[str]) -> None:
        self.symbols = symbols
        rendered = ", ".join(sorted(symbols))
        super().__init__(f"Input contains symbols outside the alphabet: {rendered}")


class InvalidSimulationAutomatonError(SimulationError):
    """Raised when a simulator receives an automaton that is not ready."""

    def __init__(self, messages: tuple[str, ...]) -> None:
        self.messages = messages
        super().__init__("Automaton is not ready for simulation")


@dataclass(frozen=True, slots=True)
class DFASimulationSnapshot:
    """Immutable view of one point in a DFA simulation."""

    input_string: str
    position: int
    current_state_id: str
    status: SimulationStatus
    last_symbol: str | None = None
    last_transition: TransitionKey | None = None
    rejection_reason: str | None = None
    path_state_ids: tuple[str, ...] = ()
    path_transitions: tuple[TransitionKey, ...] = ()
    failed_state_ids: tuple[str, ...] = ()
    failed_transitions: tuple[TransitionKey, ...] = ()

    @property
    def processed_input(self) -> str:
        return self.input_string[: self.position]

    @property
    def remaining_input(self) -> str:
        return self.input_string[self.position :]

    @property
    def next_symbol(self) -> str | None:
        if self.position >= len(self.input_string):
            return None
        return self.input_string[self.position]

    @property
    def is_finished(self) -> bool:
        return self.status in {"accepted", "rejected"}

    @property
    def is_accepted(self) -> bool:
        return self.status == "accepted"


@dataclass(frozen=True, slots=True)
class NFASimulationSnapshot:
    """Immutable view of one point in an NFA simulation."""

    input_string: str
    position: int
    active_state_ids: frozenset[str]
    status: SimulationStatus
    last_symbol: str | None = None
    last_transitions: tuple[TransitionKey, ...] = ()
    rejection_reason: str | None = None
    path_state_ids: tuple[str, ...] = ()
    path_transitions: tuple[TransitionKey, ...] = ()
    failed_state_ids: tuple[str, ...] = ()
    failed_transitions: tuple[TransitionKey, ...] = ()

    @property
    def processed_input(self) -> str:
        return self.input_string[: self.position]

    @property
    def remaining_input(self) -> str:
        return self.input_string[self.position :]

    @property
    def next_symbol(self) -> str | None:
        if self.position >= len(self.input_string):
            return None
        return self.input_string[self.position]

    @property
    def is_finished(self) -> bool:
        return self.status in {"accepted", "rejected"}

    @property
    def is_accepted(self) -> bool:
        return self.status == "accepted"


class DFASimulator:
    """Advance a DFA one input symbol at a time without depending on Qt."""

    def __init__(self, automaton: DFA) -> None:
        if not isinstance(automaton, DFA):
            raise TypeError("DFASimulator requires a DFA")

        validation = validate_automaton(automaton)
        if not validation.is_valid:
            raise InvalidSimulationAutomatonError(validation.messages)

        self._automaton = automaton
        self._input_string = ""
        self._snapshot: DFASimulationSnapshot | None = None
        self._history_states: list[str] = []
        self._history_transitions: list[TransitionKey] = []

    @property
    def snapshot(self) -> DFASimulationSnapshot:
        if self._snapshot is None:
            raise SimulationError("Simulation has not been started")
        return self._snapshot

    def start(self, input_string: str) -> DFASimulationSnapshot:
        """Initialize a new run at the DFA initial state."""
        if not isinstance(input_string, str):
            raise TypeError("Simulation input must be a string")

        _validate_input_symbols(input_string, self._automaton.alphabet)
        initial_state = self._automaton.initial_state
        if initial_state is None:
            raise InvalidSimulationAutomatonError(("Selecciona un estado inicial.",))

        self._input_string = input_string
        self._history_states = [initial_state.identifier]
        self._history_transitions = []
        if input_string == "":
            status: SimulationStatus = (
                "accepted" if initial_state.is_accepting else "rejected"
            )
            reason = (
                None
                if initial_state.is_accepting
                else "La cadena vacía termina en un estado que no es de aceptación."
            )
        else:
            status = "ready"
            reason = None

        self._snapshot = DFASimulationSnapshot(
            input_string=input_string,
            position=0,
            current_state_id=initial_state.identifier,
            status=status,
            rejection_reason=reason,
            path_state_ids=tuple(self._history_states),
            path_transitions=tuple(self._history_transitions),
        )
        return self._snapshot

    def step(self) -> DFASimulationSnapshot:
        """Consume at most one symbol and return the resulting snapshot."""
        current = self.snapshot
        if current.is_finished:
            return current

        symbol = current.next_symbol
        if symbol is None:
            state = self._automaton.get_state(current.current_state_id)
            status: SimulationStatus = "accepted" if state.is_accepting else "rejected"
            self._snapshot = DFASimulationSnapshot(
                input_string=current.input_string,
                position=current.position,
                current_state_id=current.current_state_id,
                status=status,
                rejection_reason=(
                    None
                    if state.is_accepting
                    else "La cadena terminó en un estado que no es de aceptación."
                ),
                path_state_ids=tuple(self._history_states),
                path_transitions=tuple(self._history_transitions),
            )
            return self._snapshot

        destinations = self._automaton.destinations(current.current_state_id, symbol)
        if not destinations:
            self._snapshot = DFASimulationSnapshot(
                input_string=current.input_string,
                position=current.position,
                current_state_id=current.current_state_id,
                status="rejected",
                last_symbol=symbol,
                rejection_reason=(
                    f"No existe una transición desde {current.current_state_id} "
                    f"para el símbolo '{symbol}'."
                ),
                path_state_ids=tuple(self._history_states),
                path_transitions=tuple(self._history_transitions),
            )
            return self._snapshot

        target_id = next(iter(destinations))
        new_position = current.position + 1
        target_state = self._automaton.get_state(target_id)
        traversed = (current.current_state_id, target_id)
        self._history_transitions.append(traversed)
        self._history_states.append(target_id)

        if new_position == len(current.input_string):
            status = "accepted" if target_state.is_accepting else "rejected"
            reason = (
                None
                if target_state.is_accepting
                else "La cadena terminó en un estado que no es de aceptación."
            )
        else:
            status = "running"
            reason = None

        self._snapshot = DFASimulationSnapshot(
            input_string=current.input_string,
            position=new_position,
            current_state_id=target_id,
            status=status,
            last_symbol=symbol,
            last_transition=traversed,
            rejection_reason=reason,
            path_state_ids=tuple(self._history_states),
            path_transitions=tuple(self._history_transitions),
        )
        return self._snapshot

    def reset(self) -> DFASimulationSnapshot:
        """Restart the current input string from the DFA initial state."""
        if self._snapshot is None:
            raise SimulationError("Simulation has not been started")
        return self.start(self._input_string)


class NFASimulator:
    """Advance all live NFA branches one input symbol at a time."""

    def __init__(self, automaton: NFA) -> None:
        if not isinstance(automaton, NFA):
            raise TypeError("NFASimulator requires an NFA")

        validation = validate_automaton(automaton)
        if not validation.is_valid:
            raise InvalidSimulationAutomatonError(validation.messages)

        self._automaton = automaton
        self._input_string = ""
        self._snapshot: NFASimulationSnapshot | None = None
        self._live_paths: set[tuple[str, ...]] = set()
        self._dead_paths: set[tuple[str, ...]] = set()

    @property
    def snapshot(self) -> NFASimulationSnapshot:
        if self._snapshot is None:
            raise SimulationError("Simulation has not been started")
        return self._snapshot

    def start(self, input_string: str) -> NFASimulationSnapshot:
        """Initialize an NFA run with only its initial state active."""
        if not isinstance(input_string, str):
            raise TypeError("Simulation input must be a string")

        _validate_input_symbols(input_string, self._automaton.alphabet)
        initial_state = self._automaton.initial_state
        if initial_state is None:
            raise InvalidSimulationAutomatonError(("Selecciona un estado inicial.",))

        self._input_string = input_string
        initial_path = (initial_state.identifier,)
        self._live_paths = {initial_path}
        self._dead_paths = set()
        active_states = frozenset({initial_state.identifier})
        if input_string == "":
            status: SimulationStatus = (
                "accepted" if initial_state.is_accepting else "rejected"
            )
            reason = (
                None
                if initial_state.is_accepting
                else "La cadena vacía termina sin ningún recorrido en un estado de aceptación."
            )
        else:
            status = "ready"
            reason = None

        path_states, path_transitions = _collect_paths(self._live_paths)
        self._snapshot = NFASimulationSnapshot(
            input_string=input_string,
            position=0,
            active_state_ids=active_states,
            status=status,
            rejection_reason=reason,
            path_state_ids=path_states,
            path_transitions=path_transitions,
        )
        return self._snapshot

    def step(self) -> NFASimulationSnapshot:
        """Consume one symbol across every currently active NFA branch."""
        current = self.snapshot
        if current.is_finished:
            return current

        symbol = current.next_symbol
        if symbol is None:
            accepted_paths = {
                path
                for path in self._live_paths
                if self._automaton.get_state(path[-1]).is_accepting
            }
            rejected_paths = self._live_paths - accepted_paths
            success_paths = accepted_paths or self._live_paths
            failed_paths = self._dead_paths | rejected_paths
            success_states, success_transitions = _collect_paths(success_paths)
            failed_states, failed_transitions = _collect_paths(failed_paths)
            accepted = bool(accepted_paths)
            self._snapshot = NFASimulationSnapshot(
                input_string=current.input_string,
                position=current.position,
                active_state_ids=current.active_state_ids,
                status="accepted" if accepted else "rejected",
                rejection_reason=(
                    None
                    if accepted
                    else "La cadena terminó sin ningún recorrido en un estado de aceptación."
                ),
                path_state_ids=success_states,
                path_transitions=success_transitions,
                failed_state_ids=failed_states,
                failed_transitions=failed_transitions,
            )
            return self._snapshot

        next_paths: set[tuple[str, ...]] = set()
        traversed: set[TransitionKey] = set()
        stalled_paths: set[tuple[str, ...]] = set()
        for path in self._live_paths:
            source_id = path[-1]
            destinations = self._automaton.destinations(source_id, symbol)
            if not destinations:
                stalled_paths.add(path)
                continue
            for target_id in destinations:
                next_paths.add(path + (target_id,))
                traversed.add((source_id, target_id))

        self._dead_paths |= stalled_paths

        if not next_paths:
            failed_states, failed_transitions = _collect_paths(self._dead_paths | stalled_paths)
            self._live_paths = set()
            self._snapshot = NFASimulationSnapshot(
                input_string=current.input_string,
                position=current.position,
                active_state_ids=frozenset(),
                status="rejected",
                last_symbol=symbol,
                rejection_reason=(
                    f"Ningún recorrido puede continuar con el símbolo '{symbol}'."
                ),
                failed_state_ids=failed_states,
                failed_transitions=failed_transitions,
            )
            return self._snapshot

        self._live_paths = next_paths
        new_position = current.position + 1
        active_state_ids = frozenset(path[-1] for path in next_paths)
        path_states, path_transitions = _collect_paths(next_paths)
        failed_states, failed_transitions = _collect_paths(self._dead_paths)

        if new_position == len(current.input_string):
            accepted_paths = {
                path
                for path in next_paths
                if self._automaton.get_state(path[-1]).is_accepting
            }
            rejected_paths = next_paths - accepted_paths
            success_paths = accepted_paths or next_paths
            failed_states, failed_transitions = _collect_paths(
                self._dead_paths | rejected_paths
            )
            path_states, path_transitions = _collect_paths(success_paths)
            accepted = bool(accepted_paths)
            status = "accepted" if accepted else "rejected"
            reason = (
                None
                if accepted
                else "La cadena terminó sin ningún recorrido en un estado de aceptación."
            )
        else:
            status = "running"
            reason = None

        self._snapshot = NFASimulationSnapshot(
            input_string=current.input_string,
            position=new_position,
            active_state_ids=active_state_ids,
            status=status,
            last_symbol=symbol,
            last_transitions=tuple(sorted(traversed)),
            rejection_reason=reason,
            path_state_ids=path_states,
            path_transitions=path_transitions,
            failed_state_ids=failed_states,
            failed_transitions=failed_transitions,
        )
        return self._snapshot

    def reset(self) -> NFASimulationSnapshot:
        """Restart the current input string from the NFA initial state."""
        if self._snapshot is None:
            raise SimulationError("Simulation has not been started")
        return self.start(self._input_string)


def _validate_input_symbols(input_string: str, alphabet: frozenset[str]) -> None:
    invalid_symbols = frozenset(symbol for symbol in input_string if symbol not in alphabet)
    if invalid_symbols:
        raise InvalidSimulationInputError(invalid_symbols)


def _collect_paths(paths: set[tuple[str, ...]] | frozenset[tuple[str, ...]]) -> tuple[tuple[str, ...], tuple[TransitionKey, ...]]:
    states: set[str] = set()
    transitions: set[TransitionKey] = set()
    for path in paths:
        states.update(path)
        transitions.update(zip(path, path[1:], strict=False))
    return tuple(sorted(states)), tuple(sorted(transitions))
