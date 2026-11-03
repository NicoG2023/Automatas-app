from itertools import product

import pytest

from app_automatas.model.automaton import EPSILON_SYMBOLS
from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import EpsilonNFA, NFA
from app_automatas.services.nfa_to_dfa import convert_nfa_to_dfa
from app_automatas.services.regular_expression_to_nfa import (
    RegularExpressionSyntaxError,
    parse_regular_expression,
    regular_expression_to_nfa,
)
from app_automatas.services.simulation import DFASimulator, NFASimulator


def _accepts(automaton: NFA, word: str) -> bool:
    simulator = NFASimulator(automaton)
    snapshot = simulator.start(word)
    while not snapshot.is_finished:
        snapshot = simulator.step()
    return snapshot.is_accepted


def _dfa_accepts(automaton: DFA, word: str) -> bool:
    simulator = DFASimulator(automaton)
    snapshot = simulator.start(word)
    while not snapshot.is_finished:
        snapshot = simulator.step()
    return snapshot.is_accepted


@pytest.mark.parametrize(
    ("expression", "accepted", "rejected", "has_lambda_edges"),
    [
        ("a(b|c)*", ("a", "ab", "ac", "abcb"), ("", "ba", "aa"), True),
        ("(a|b)*abb", ("abb", "aabb", "babb"), ("", "ab", "abba"), True),
        ("λ|a", ("", "a"), ("aa",), True),
        ("a+", ("a", "aa"), ("",), True),
        ("∅", (), ("",), False),
        ("∅*", ("",), (), False),
    ],
)
def test_kleene_construction_preserves_regular_expression_language(
    expression: str,
    accepted: tuple[str, ...],
    rejected: tuple[str, ...],
    has_lambda_edges: bool,
) -> None:
    automaton = regular_expression_to_nfa(expression)

    assert automaton.initial_state is not None
    transition_symbols = {
        symbol
        for transition in automaton.transitions
        for symbol in transition.symbols
    }
    assert automaton.alphabet == frozenset(transition_symbols - EPSILON_SYMBOLS)
    assert isinstance(automaton, EpsilonNFA)
    assert any(
        transition.symbols.intersection(EPSILON_SYMBOLS)
        for transition in automaton.transitions
    ) == has_lambda_edges
    assert all(_accepts(automaton, word) for word in accepted)
    assert all(not _accepts(automaton, word) for word in rejected)


def test_lambda_nfa_can_be_converted_to_equivalent_dfa() -> None:
    epsilon_nfa = regular_expression_to_nfa("(a|b)*abb")
    dfa = convert_nfa_to_dfa(epsilon_nfa)

    words = [""]
    for length in range(1, 5):
        words.extend(
            "".join(symbols)
            for symbols in product(sorted(epsilon_nfa.alphabet), repeat=length)
        )
    for word in words:
        assert _accepts(epsilon_nfa, word) == _dfa_accepts(dfa, word)


def test_kleene_part_one_builds_the_ab_union_ba_example() -> None:
    automaton = regular_expression_to_nfa("ab ∪ ba")

    assert len(automaton.states) == 9
    assert {state.identifier for state in automaton.accepting_states} == {"q4", "q8"}
    expected_edges = {
        ("q0", "q1"): {"λ"},
        ("q1", "q2"): {"a"},
        ("q2", "q3"): {"λ"},
        ("q3", "q4"): {"b"},
        ("q0", "q5"): {"λ"},
        ("q5", "q6"): {"b"},
        ("q6", "q7"): {"λ"},
        ("q7", "q8"): {"a"},
    }
    assert {
        (transition.source.identifier, transition.target.identifier):
        transition.symbols
        for transition in automaton.transitions
    } == expected_edges
    assert _accepts(automaton, "ab")
    assert _accepts(automaton, "ba")
    assert not _accepts(automaton, "")
    assert not _accepts(automaton, "aa")


def test_kleene_part_one_matches_the_a_star_ab_union_ba_star_diagram() -> None:
    automaton = regular_expression_to_nfa("a*(ab ∪ ba)*")

    expected_edges = {
        ("q0", "q0"): {"a"},
        ("q0", "q1"): {"λ"},
        ("q1", "q2"): {"λ"},
        ("q2", "q3"): {"a"},
        ("q3", "q4"): {"λ"},
        ("q4", "q5"): {"b"},
        ("q1", "q6"): {"λ"},
        ("q6", "q7"): {"b"},
        ("q7", "q8"): {"λ"},
        ("q8", "q9"): {"a"},
        ("q5", "q1"): {"λ"},
        ("q9", "q1"): {"λ"},
    }

    assert len(automaton.states) == 10
    assert automaton.initial_state is not None
    assert automaton.initial_state.identifier == "q0"
    assert {state.identifier for state in automaton.accepting_states} == {
        "q1",
        "q5",
        "q9",
    }
    assert {
        (transition.source.identifier, transition.target.identifier):
        transition.symbols
        for transition in automaton.transitions
    } == expected_edges
    assert _accepts(automaton, "")
    assert _accepts(automaton, "a")
    assert _accepts(automaton, "ab")
    assert _accepts(automaton, "ba")
    assert _accepts(automaton, "aab")
    assert _accepts(automaton, "abba")
    assert not _accepts(automaton, "abb")


@pytest.mark.parametrize(
    "expression",
    ["", "|a", "a|", "a||b", "()", "(a", "a)", "*a", "\\"],
)
def test_parser_rejects_malformed_expressions(expression: str) -> None:
    with pytest.raises(RegularExpressionSyntaxError):
        parse_regular_expression(expression)
