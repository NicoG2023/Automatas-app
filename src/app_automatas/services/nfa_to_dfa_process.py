"""Pedagogical trace for the NFA-to-DFA subset-construction process."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.services.nfa_to_dfa import NFAConversionError
from app_automatas.services.validation import validate_automaton

Subset = frozenset[str]
TransitionRow = tuple[Subset, tuple[tuple[str, Subset], ...]]


@dataclass(frozen=True, slots=True)
class ConversionProcess:
    """Immutable data needed to render every pedagogical conversion step."""

    symbols: tuple[str, ...]
    original_rows: tuple[TransitionRow, ...]
    expanded_rows: tuple[TransitionRow, ...]
    names: tuple[tuple[Subset, str], ...]
    complete_dfa: DFA
    reachable_dfa: DFA
    reachable_names: tuple[str, ...]
    unreachable_names: tuple[str, ...]

    @property
    def name_map(self) -> dict[Subset, str]:
        return dict(self.names)


def build_conversion_process(nfa: NFA) -> ConversionProcess:
    """Build the five-step classroom-style subset-construction trace.

    Unlike ``convert_nfa_to_dfa``, this trace intentionally starts with every
    original singleton state, expands every non-empty subset that appears in the
    table, renames all rows to k0, k1, ... and only then removes unreachable
    states. This mirrors the pedagogical workflow commonly done by hand.
    """
    if not isinstance(nfa, NFA):
        raise TypeError("build_conversion_process requires an NFA")

    validation = validate_automaton(nfa)
    if not validation.is_valid:
        raise NFAConversionError(validation.messages)

    initial = nfa.initial_state
    if initial is None:
        raise NFAConversionError(("Selecciona un estado inicial.",))

    symbols = tuple(sorted(nfa.alphabet))
    state_order = {state.identifier: index for index, state in enumerate(nfa.states)}
    singleton_order = [initial.identifier]
    singleton_order.extend(
        state.identifier
        for state in nfa.states
        if state.identifier != initial.identifier
    )

    original_subsets = tuple(frozenset({identifier}) for identifier in singleton_order)
    original_rows = tuple(
        _row_for_subset(nfa, subset, symbols) for subset in original_subsets
    )

    ordered_subsets: list[Subset] = list(original_subsets)
    discovered: set[Subset] = set(original_subsets)
    pending: deque[Subset] = deque(original_subsets)

    while pending:
        subset = pending.popleft()
        row = _row_for_subset(nfa, subset, symbols)
        for _symbol, destination in row[1]:
            if not destination or destination in discovered:
                continue
            discovered.add(destination)
            ordered_subsets.append(destination)
            pending.append(destination)

    expanded_rows = tuple(
        _row_for_subset(nfa, subset, symbols) for subset in ordered_subsets
    )
    names = tuple((subset, f"k{index}") for index, subset in enumerate(ordered_subsets))
    name_map = dict(names)

    complete_dfa = _build_named_dfa(
        nfa,
        expanded_rows,
        name_map,
        initial_subset=frozenset({initial.identifier}),
    )
    reachable_name_set = _reachable_state_names(complete_dfa)
    reachable_names = tuple(
        state.identifier
        for state in complete_dfa.states
        if state.identifier in reachable_name_set
    )
    reachable_dfa = _copy_reachable_dfa(complete_dfa, reachable_name_set)
    unreachable_names = tuple(
        state.identifier
        for state in complete_dfa.states
        if state.identifier not in reachable_name_set
    )

    return ConversionProcess(
        symbols=symbols,
        original_rows=original_rows,
        expanded_rows=expanded_rows,
        names=names,
        complete_dfa=complete_dfa,
        reachable_dfa=reachable_dfa,
        reachable_names=reachable_names,
        unreachable_names=unreachable_names,
    )


def render_subset(subset: Subset, *, singleton_braces: bool = False) -> str:
    """Render table subsets using the notation from the classroom procedure."""
    if not subset:
        return "∅"
    ordered = sorted(subset)
    if len(ordered) == 1 and not singleton_braces:
        return ordered[0]
    return "{" + ",".join(ordered) + "}"


def _row_for_subset(
    nfa: NFA,
    subset: Subset,
    symbols: tuple[str, ...],
) -> TransitionRow:
    cells: list[tuple[str, Subset]] = []
    for symbol in symbols:
        destinations: set[str] = set()
        for source_id in subset:
            destinations.update(nfa.destinations(source_id, symbol))
        cells.append((symbol, frozenset(destinations)))
    return subset, tuple(cells)


def _build_named_dfa(
    nfa: NFA,
    rows: tuple[TransitionRow, ...],
    name_map: dict[Subset, str],
    *,
    initial_subset: Subset,
) -> DFA:
    accepting_ids = {state.identifier for state in nfa.accepting_states}
    dfa = DFA(nfa.alphabet)

    for subset, _cells in rows:
        dfa.add_state(
            name_map[subset],
            is_initial=subset == initial_subset,
            is_accepting=bool(subset & accepting_ids),
        )

    for subset, cells in rows:
        source_name = name_map[subset]
        for symbol, destination in cells:
            if not destination:
                continue
            target_name = name_map[destination]
            dfa.add_transition(source_name, target_name, symbol)

    _apply_process_layout(dfa)
    return dfa


def _reachable_state_names(dfa: DFA) -> frozenset[str]:
    initial = dfa.initial_state
    if initial is None:
        return frozenset()

    visited: set[str] = {initial.identifier}
    pending: deque[str] = deque([initial.identifier])
    symbols = tuple(sorted(dfa.alphabet))
    while pending:
        source_id = pending.popleft()
        for symbol in symbols:
            for target_id in dfa.destinations(source_id, symbol):
                if target_id in visited:
                    continue
                visited.add(target_id)
                pending.append(target_id)
    return frozenset(visited)


def _copy_reachable_dfa(source: DFA, reachable_names: frozenset[str]) -> DFA:
    result = DFA(source.alphabet)
    for state in source.states:
        if state.identifier not in reachable_names:
            continue
        result.add_state(
            state.identifier,
            is_initial=state.is_initial,
            is_accepting=state.is_accepting,
        )

    for transition in source.transitions:
        source_id = transition.source.identifier
        target_id = transition.target.identifier
        if source_id not in reachable_names or target_id not in reachable_names:
            continue
        for symbol in sorted(transition.symbols):
            result.add_transition(source_id, target_id, symbol)

    _apply_process_layout(result)
    return result


def _apply_process_layout(dfa: DFA) -> None:
    states = dfa.states
    if not states:
        return

    columns = 3 if len(states) > 4 else 2
    spacing_x = 245.0
    spacing_y = 190.0
    origin_x = 180.0
    origin_y = 170.0
    for index, state in enumerate(states):
        row, column = divmod(index, columns)
        state.set_position(
            origin_x + column * spacing_x,
            origin_y + row * spacing_y,
        )
