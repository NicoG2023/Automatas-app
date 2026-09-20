"""Factory helpers for finite automata."""

from __future__ import annotations

from app_automatas.model.automaton import Automaton
from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA


def create_automaton(automaton_type: str) -> Automaton:
    """Create the concrete automaton requested by the editor."""
    if automaton_type == "AFD":
        return DFA()
    if automaton_type == "AFN":
        return NFA()
    raise ValueError(f"Unsupported automaton type: {automaton_type}")
