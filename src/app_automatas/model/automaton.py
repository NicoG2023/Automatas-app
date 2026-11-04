"""Base model shared by deterministic and nondeterministic automata."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from app_automatas.model.exceptions import (
    AlphabetSymbolInUseError,
    DuplicateStateError,
    InvalidSymbolError,
    UnknownStateError,
    UnknownTransitionError,
)
from app_automatas.model.state import State
from app_automatas.model.transition import Transition

EPSILON_SYMBOLS = frozenset({"ε", "ϵ", "λ"})


class Automaton(ABC):
    """Own the alphabet, states and transitions of a finite automaton."""

    def __init__(self, alphabet: Iterable[str] | None = None) -> None:
        self._alphabet: set[str] = set()
        self._states: dict[str, State] = {}
        self._transitions: list[Transition] = []
        self._next_state_index = 0

        if alphabet is not None:
            self.set_alphabet(alphabet)

    @property
    @abstractmethod
    def automaton_type(self) -> str:
        """Return the human-facing automaton type label."""

    @property
    def alphabet(self) -> frozenset[str]:
        return frozenset(self._alphabet)

    @property
    def states(self) -> tuple[State, ...]:
        return tuple(self._states.values())

    @property
    def transitions(self) -> tuple[Transition, ...]:
        return tuple(self._transitions)

    @property
    def initial_state(self) -> State | None:
        return next((state for state in self._states.values() if state.is_initial), None)

    @property
    def accepting_states(self) -> tuple[State, ...]:
        return tuple(state for state in self._states.values() if state.is_accepting)

    @property
    def is_empty(self) -> bool:
        return not self._states and not self._transitions

    def set_alphabet(
        self,
        symbols: Iterable[str],
        *,
        remove_invalid_transitions: bool = False,
    ) -> None:
        """Replace the alphabet, optionally removing affected transition symbols."""
        new_alphabet = {self._validate_symbol(symbol) for symbol in symbols}
        removed_symbols = self._alphabet - new_alphabet
        symbols_in_use = {
            symbol
            for transition in self._transitions
            for symbol in transition.symbols
            if symbol in removed_symbols
        }

        if symbols_in_use and not remove_invalid_transitions:
            raise AlphabetSymbolInUseError(symbols_in_use)

        if symbols_in_use:
            for transition in tuple(self._transitions):
                transition.symbols.difference_update(symbols_in_use)
                if not transition.symbols:
                    self._transitions.remove(transition)

        self._alphabet = new_alphabet

    def add_symbol(self, symbol: str) -> None:
        self._alphabet.add(self._validate_symbol(symbol))

    def remove_symbol(
        self,
        symbol: str,
        *,
        remove_invalid_transitions: bool = False,
    ) -> None:
        if symbol not in self._alphabet:
            return
        self.set_alphabet(
            self._alphabet - {symbol},
            remove_invalid_transitions=remove_invalid_transitions,
        )

    def add_state(
        self,
        identifier: str | None = None,
        *,
        is_initial: bool = False,
        is_accepting: bool = False,
        x: float = 0.0,
        y: float = 0.0,
    ) -> State:
        """Create a state with an automatic qN identifier when omitted."""
        state_identifier = (
            self._next_automatic_identifier()
            if identifier is None
            else self._validate_identifier(identifier)
        )
        if state_identifier in self._states:
            raise DuplicateStateError(f"State already exists: {state_identifier}")

        state = State(
            identifier=state_identifier,
            is_accepting=is_accepting,
            x=float(x),
            y=float(y),
        )
        self._states[state_identifier] = state

        if is_initial:
            self.set_initial_state(state_identifier)

        return state

    def get_state(self, identifier: str) -> State:
        try:
            return self._states[identifier]
        except KeyError as exc:
            raise UnknownStateError(f"Unknown state: {identifier}") from exc

    def rename_state(self, current_identifier: str, new_identifier: str) -> State:
        state = self.get_state(current_identifier)
        validated_identifier = self._validate_identifier(new_identifier)

        if validated_identifier != current_identifier and validated_identifier in self._states:
            raise DuplicateStateError(f"State already exists: {validated_identifier}")

        if validated_identifier == current_identifier:
            return state

        del self._states[current_identifier]
        state.identifier = validated_identifier
        self._states[validated_identifier] = state
        return state

    def remove_state(self, identifier: str) -> State:
        state = self.get_state(identifier)
        self._transitions = [
            transition
            for transition in self._transitions
            if transition.source is not state and transition.target is not state
        ]
        del self._states[identifier]
        return state

    def set_initial_state(self, identifier: str | None) -> None:
        """Set the only initial state, or clear it when identifier is None."""
        new_initial = self.get_state(identifier) if identifier is not None else None
        for state in self._states.values():
            state.is_initial = state is new_initial

    def set_accepting(self, identifier: str, is_accepting: bool = True) -> None:
        self.get_state(identifier).is_accepting = is_accepting

    def add_transition(self, source_id: str, target_id: str, symbol: str) -> Transition:
        """Add one symbol, reusing an existing edge for the same state pair."""
        validated_symbol = self._validate_transition_symbol(symbol)
        source = self.get_state(source_id)
        target = self.get_state(target_id)

        self._validate_transition_rule(source, target, validated_symbol)

        transition = self._find_transition(source, target)
        if transition is None:
            transition = Transition(source=source, target=target)
            self._transitions.append(transition)
        transition.add_symbol(validated_symbol)
        return transition

    def get_transition(self, source_id: str, target_id: str) -> Transition:
        """Return the logical edge connecting one ordered pair of states."""
        source = self.get_state(source_id)
        target = self.get_state(target_id)
        transition = self._find_transition(source, target)
        if transition is None:
            raise UnknownTransitionError(
                f"Unknown transition: {source_id} -> {target_id}"
            )
        return transition

    def set_transition_symbols(
        self,
        source_id: str,
        target_id: str,
        symbols: Iterable[str],
    ) -> Transition:
        """Replace all symbols on an existing edge after full validation."""
        transition = self.get_transition(source_id, target_id)
        validated_symbols = {
            self._validate_transition_symbol(symbol) for symbol in symbols
        }
        if not validated_symbols:
            raise InvalidSymbolError("A transition must contain at least one symbol")

        for symbol in validated_symbols:
            self._validate_transition_rule(
                transition.source,
                transition.target,
                symbol,
            )

        transition.symbols = validated_symbols
        return transition

    def remove_transition(
        self,
        source_id: str,
        target_id: str,
        symbol: str | None = None,
    ) -> None:
        source = self.get_state(source_id)
        target = self.get_state(target_id)
        transition = self._find_transition(source, target)
        if transition is None:
            return

        if symbol is None:
            self._transitions.remove(transition)
            return

        transition.remove_symbol(symbol)
        if not transition.symbols:
            self._transitions.remove(transition)

    def clear(self) -> None:
        """Reset the whole document while keeping the concrete automaton type."""
        self._alphabet.clear()
        self._states.clear()
        self._transitions.clear()
        self._next_state_index = 0

    def destinations(self, source_id: str, symbol: str) -> frozenset[str]:
        """Return every state identifier reachable with one symbol."""
        source = self.get_state(source_id)
        return frozenset(
            transition.target.identifier
            for transition in self._transitions
            if transition.source is source and transition.accepts(symbol)
        )

    def _find_transition(self, source: State, target: State) -> Transition | None:
        return next(
            (
                transition
                for transition in self._transitions
                if transition.source is source and transition.target is target
            ),
            None,
        )

    def _next_automatic_identifier(self) -> str:
        while True:
            candidate = f"q{self._next_state_index}"
            self._next_state_index += 1
            if candidate not in self._states:
                return candidate

    @staticmethod
    def _validate_identifier(identifier: str) -> str:
        validated_identifier = identifier.strip()
        if not validated_identifier:
            raise ValueError("State identifier cannot be empty")
        return validated_identifier

    @staticmethod
    def _validate_symbol(symbol: str) -> str:
        if not isinstance(symbol, str):
            raise InvalidSymbolError("Alphabet symbols must be strings")
        if symbol == "" or symbol in EPSILON_SYMBOLS:
            raise InvalidSymbolError("Empty and epsilon symbols are not supported")
        return symbol

    def _validate_transition_symbol(self, symbol: str) -> str:
        validated_symbol = self._validate_symbol(symbol)
        if validated_symbol not in self._alphabet:
            raise InvalidSymbolError(
                f"Symbol does not belong to the alphabet: {validated_symbol}"
            )
        return validated_symbol

    @abstractmethod
    def _validate_transition_rule(
        self,
        source: State,
        target: State,
        symbol: str,
    ) -> None:
        """Validate automaton-specific transition constraints."""
