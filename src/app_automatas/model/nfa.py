"""Nondeterministic finite automaton model without epsilon transitions."""

from __future__ import annotations

from app_automatas.model.automaton import Automaton, EPSILON_SYMBOLS
from app_automatas.model.exceptions import InvalidSymbolError
from app_automatas.model.state import State


class NFA(Automaton):
    """Finite automaton that can reach multiple states with the same symbol."""

    @property
    def automaton_type(self) -> str:
        return "AFN"

    def _validate_transition_rule(
        self,
        source: State,
        target: State,
        symbol: str,
    ) -> None:
        return None


class EpsilonNFA(NFA):
    """Nondeterministic finite automaton with explicit empty transitions."""

    @property
    def automaton_type(self) -> str:
        return "AFN-λ"

    def _validate_transition_symbol(self, symbol: str) -> str:
        if not isinstance(symbol, str):
            raise InvalidSymbolError("Transition symbols must be strings")
        if symbol in EPSILON_SYMBOLS:
            return symbol
        return super()._validate_transition_symbol(symbol)
