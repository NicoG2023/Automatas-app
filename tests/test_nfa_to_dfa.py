import pytest

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.services.nfa_to_dfa import NFAConversionError, convert_nfa_to_dfa
from app_automatas.services.simulation import DFASimulator, NFASimulator


def _branching_nfa() -> NFA:
    automaton = NFA(["a", "b"])
    automaton.add_state("q0", is_initial=True, x=25, y=40)
    automaton.add_state("q1", is_accepting=True, x=80, y=120)
    automaton.add_transition("q0", "q0", "a")
    automaton.add_transition("q0", "q1", "a")
    automaton.add_transition("q1", "q1", "b")
    return automaton


def _run(simulator: DFASimulator | NFASimulator, word: str) -> bool:
    snapshot = simulator.start(word)
    while not snapshot.is_finished:
        snapshot = simulator.step()
    return snapshot.is_accepted


def test_conversion_requires_an_nfa() -> None:
    with pytest.raises(TypeError, match="requires an NFA"):
        convert_nfa_to_dfa(DFA(["a"]))  # type: ignore[arg-type]


def test_invalid_nfa_cannot_be_converted() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0")

    with pytest.raises(NFAConversionError) as exc_info:
        convert_nfa_to_dfa(automaton)

    assert "Selecciona un estado inicial." in exc_info.value.messages


def test_subset_construction_creates_expected_reachable_states() -> None:
    result = convert_nfa_to_dfa(_branching_nfa())

    assert isinstance(result, DFA)
    assert result.alphabet == frozenset({"a", "b"})
    assert {state.identifier for state in result.states} == {
        "{q0}",
        "{q0,q1}",
        "{q1}",
    }
    assert result.initial_state is not None
    assert result.initial_state.identifier == "{q0}"
    assert {state.identifier for state in result.accepting_states} == {
        "{q0,q1}",
        "{q1}",
    }


def test_conversion_groups_deterministic_transitions() -> None:
    result = convert_nfa_to_dfa(_branching_nfa())

    assert result.destinations("{q0}", "a") == frozenset({"{q0,q1}"})
    assert result.destinations("{q0}", "b") == frozenset()
    assert result.destinations("{q0,q1}", "a") == frozenset({"{q0,q1}"})
    assert result.destinations("{q0,q1}", "b") == frozenset({"{q1}"})
    assert result.destinations("{q1}", "b") == frozenset({"{q1}"})


def test_generated_dfa_preserves_language_for_representative_words() -> None:
    nfa = _branching_nfa()
    dfa = convert_nfa_to_dfa(nfa)

    for word in ("", "a", "aa", "ab", "aab", "abb", "b", "ba", "abab"):
        assert _run(NFASimulator(nfa), word) == _run(DFASimulator(dfa), word)


def test_conversion_does_not_modify_source_nfa() -> None:
    nfa = _branching_nfa()
    state_snapshot = tuple(
        (state.identifier, state.is_initial, state.is_accepting, state.x, state.y)
        for state in nfa.states
    )
    transition_snapshot = tuple(
        (
            transition.source.identifier,
            transition.target.identifier,
            frozenset(transition.symbols),
        )
        for transition in nfa.transitions
    )

    _ = convert_nfa_to_dfa(nfa)

    assert tuple(
        (state.identifier, state.is_initial, state.is_accepting, state.x, state.y)
        for state in nfa.states
    ) == state_snapshot
    assert tuple(
        (
            transition.source.identifier,
            transition.target.identifier,
            frozenset(transition.symbols),
        )
        for transition in nfa.transitions
    ) == transition_snapshot


def test_generated_states_receive_automatic_layout() -> None:
    result = convert_nfa_to_dfa(_branching_nfa())
    positions = {(state.x, state.y) for state in result.states}

    assert len(positions) == len(result.states)
    assert all(x > 0 and y > 0 for x, y in positions)
