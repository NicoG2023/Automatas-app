"""Nondeterministic finite automaton model without epsilon transitions."""

from __future__ import annotations

from app_automatas.model.automaton import Automaton
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
