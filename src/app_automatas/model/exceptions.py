"""Domain-specific errors raised by finite automata models."""

from __future__ import annotations


class AutomatonError(ValueError):
    """Base error for invalid automaton operations."""


class DuplicateStateError(AutomatonError):
    """Raised when a state identifier is already in use."""


class UnknownStateError(AutomatonError):
    """Raised when an operation references a state that does not exist."""


class InvalidSymbolError(AutomatonError):
    """Raised when a symbol is invalid or does not belong to the alphabet."""


class UnknownTransitionError(AutomatonError):
    """Raised when an operation references a transition that does not exist."""


class DuplicateTransitionError(AutomatonError):
    """Raised when a transition violates deterministic automaton rules."""


class AlphabetSymbolInUseError(AutomatonError):
    """Raised when removing alphabet symbols still used by transitions."""

    def __init__(self, symbols: set[str]) -> None:
        self.symbols = frozenset(symbols)
        joined = ", ".join(sorted(symbols))
        super().__init__(f"Alphabet symbols still in use: {joined}")
