"""Deterministic finite automaton model."""

from __future__ import annotations

from app_automatas.model.automaton import Automaton
from app_automatas.model.exceptions import DuplicateTransitionError
from app_automatas.model.state import State


class DFA(Automaton):
    """Finite automaton with at most one destination per state and symbol."""

    @property
    def automaton_type(self) -> str:
        return "AFD"

    def _validate_transition_rule(
        self,
        source: State,
        target: State,
        symbol: str,
    ) -> None:
        for transition in self.transitions:
            if (
                transition.source is source
                and transition.accepts(symbol)
                and transition.target is not target
            ):
                raise DuplicateTransitionError(
                    f"State {source.identifier} already has a transition "
                    f"for symbol {symbol}"
                )
