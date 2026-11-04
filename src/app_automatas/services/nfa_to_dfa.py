"""Subset-construction conversion from NFA to DFA."""

from __future__ import annotations

import math
from collections import deque

from app_automatas.model.automaton import EPSILON_SYMBOLS
from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.services.validation import validate_automaton


class NFAConversionError(ValueError):
    """Raised when an NFA cannot be converted because it is structurally invalid."""

    def __init__(self, messages: tuple[str, ...]) -> None:
        self.messages = messages
        super().__init__("NFA is not ready for conversion")


def convert_nfa_to_dfa(nfa: NFA) -> DFA:
    """Convert an NFA, including lambda transitions, by subset construction.

    Only reachable non-empty subsets are materialized. Missing transitions remain
    absent because this application's DFA semantics reject when no transition exists.
    """
    if not isinstance(nfa, NFA):
        raise TypeError("convert_nfa_to_dfa requires an NFA")

    validation = validate_automaton(nfa)
    if not validation.is_valid:
        raise NFAConversionError(validation.messages)

    initial_state = nfa.initial_state
    if initial_state is None:  # defensive; validation already catches this
        raise NFAConversionError(("Selecciona un estado inicial.",))

    state_order = {
        state.identifier: index
        for index, state in enumerate(nfa.states)
    }
    accepting_ids = {state.identifier for state in nfa.accepting_states}

    def subset_name(subset: frozenset[str]) -> str:
        ordered = sorted(subset, key=lambda identifier: state_order[identifier])
        return "{" + ",".join(ordered) + "}"

    dfa = DFA(nfa.alphabet)
    initial_subset = _epsilon_closure(nfa, {initial_state.identifier})
    pending: deque[frozenset[str]] = deque([initial_subset])
    discovered: set[frozenset[str]] = {initial_subset}
    created_names: set[str] = set()

    while pending:
        subset = pending.popleft()
        identifier = subset_name(subset)
        if identifier not in created_names:
            dfa.add_state(
                identifier,
                is_initial=subset == initial_subset,
                is_accepting=bool(subset & accepting_ids),
            )
            created_names.add(identifier)

        for symbol in sorted(nfa.alphabet):
            destination_ids: set[str] = set()
            for source_id in subset:
                destination_ids.update(nfa.destinations(source_id, symbol))

            if not destination_ids:
                continue

            target_subset = _epsilon_closure(nfa, destination_ids)
            if target_subset not in discovered:
                discovered.add(target_subset)
                pending.append(target_subset)

            target_identifier = subset_name(target_subset)
            if target_identifier not in created_names:
                dfa.add_state(
                    target_identifier,
                    is_accepting=bool(target_subset & accepting_ids),
                )
                created_names.add(target_identifier)
            dfa.add_transition(identifier, target_identifier, symbol)

    _apply_grid_layout(dfa)
    return dfa


def _epsilon_closure(
    nfa: NFA,
    state_ids: set[str] | frozenset[str],
) -> frozenset[str]:
    closure = set(state_ids)
    pending = list(state_ids)
    while pending:
        source_id = pending.pop()
        for epsilon_symbol in EPSILON_SYMBOLS:
            for target_id in nfa.destinations(source_id, epsilon_symbol):
                if target_id in closure:
                    continue
                closure.add(target_id)
                pending.append(target_id)
    return frozenset(closure)


def _apply_grid_layout(dfa: DFA) -> None:
    """Assign a readable deterministic layout to generated DFA states."""
    states = dfa.states
    if not states:
        return

    columns = min(4, max(1, math.ceil(math.sqrt(len(states)))))
    origin_x = 180.0
    origin_y = 170.0
    spacing_x = 270.0
    spacing_y = 210.0

    for index, state in enumerate(states):
        row, column = divmod(index, columns)
        state.set_position(
            origin_x + column * spacing_x,
            origin_y + row * spacing_y,
        )
