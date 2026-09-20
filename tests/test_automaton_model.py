import pytest

from app_automatas.model.dfa import DFA
from app_automatas.model.exceptions import (
    AlphabetSymbolInUseError,
    DuplicateStateError,
    DuplicateTransitionError,
    InvalidSymbolError,
    UnknownStateError,
    UnknownTransitionError,
)
from app_automatas.model.nfa import NFA


def test_states_receive_unique_consecutive_identifiers() -> None:
    automaton = DFA()

    first = automaton.add_state()
    second = automaton.add_state()
    third = automaton.add_state()

    assert [first.identifier, second.identifier, third.identifier] == ["q0", "q1", "q2"]


def test_state_can_be_renamed_but_identifiers_remain_unique() -> None:
    automaton = DFA()
    automaton.add_state("inicio")
    automaton.add_state("fin")

    renamed = automaton.rename_state("inicio", "qInicial")

    assert renamed.identifier == "qInicial"
    assert automaton.get_state("qInicial") is renamed
    with pytest.raises(UnknownStateError):
        automaton.get_state("inicio")
    with pytest.raises(DuplicateStateError):
        automaton.rename_state("qInicial", "fin")


def test_selecting_new_initial_state_unsets_previous_one() -> None:
    automaton = DFA()
    first = automaton.add_state(is_initial=True, is_accepting=True)
    second = automaton.add_state()

    automaton.set_initial_state(second.identifier)

    assert not first.is_initial
    assert first.is_accepting
    assert second.is_initial
    assert automaton.initial_state is second


def test_removing_state_also_removes_connected_transitions() -> None:
    automaton = DFA({"a"})
    first = automaton.add_state()
    second = automaton.add_state()
    automaton.add_transition(first.identifier, second.identifier, "a")

    automaton.remove_state(second.identifier)

    assert automaton.transitions == ()


def test_transition_symbol_must_belong_to_alphabet() -> None:
    automaton = DFA({"a"})
    first = automaton.add_state()
    second = automaton.add_state()

    with pytest.raises(InvalidSymbolError, match="does not belong"):
        automaton.add_transition(first.identifier, second.identifier, "b")


@pytest.mark.parametrize("symbol", ["", "ε", "ϵ"])
def test_epsilon_and_empty_symbols_are_not_supported(symbol: str) -> None:
    with pytest.raises(InvalidSymbolError):
        DFA({symbol})


def test_existing_edge_groups_multiple_symbols() -> None:
    automaton = DFA({"a", "b"})
    first = automaton.add_state()
    second = automaton.add_state()

    first_edge = automaton.add_transition(first.identifier, second.identifier, "a")
    second_edge = automaton.add_transition(first.identifier, second.identifier, "b")

    assert first_edge is second_edge
    assert automaton.transitions == (first_edge,)
    assert first_edge.symbols == {"a", "b"}


def test_dfa_rejects_two_destinations_for_same_source_and_symbol() -> None:
    automaton = DFA({"a"})
    source = automaton.add_state()
    first_target = automaton.add_state()
    second_target = automaton.add_state()
    automaton.add_transition(source.identifier, first_target.identifier, "a")

    with pytest.raises(DuplicateTransitionError):
        automaton.add_transition(source.identifier, second_target.identifier, "a")


def test_nfa_allows_multiple_destinations_for_same_source_and_symbol() -> None:
    automaton = NFA({"a"})
    source = automaton.add_state()
    first_target = automaton.add_state()
    second_target = automaton.add_state()

    automaton.add_transition(source.identifier, first_target.identifier, "a")
    automaton.add_transition(source.identifier, second_target.identifier, "a")

    assert automaton.destinations(source.identifier, "a") == frozenset(
        {first_target.identifier, second_target.identifier}
    )


def test_removing_used_alphabet_symbol_requires_explicit_confirmation_path() -> None:
    automaton = DFA({"a", "b"})
    first = automaton.add_state()
    second = automaton.add_state()
    automaton.add_transition(first.identifier, second.identifier, "a")

    with pytest.raises(AlphabetSymbolInUseError) as error:
        automaton.remove_symbol("a")

    assert error.value.symbols == frozenset({"a"})
    assert automaton.alphabet == frozenset({"a", "b"})
    assert len(automaton.transitions) == 1


def test_confirmed_alphabet_change_removes_affected_transition_symbols() -> None:
    automaton = DFA({"a", "b"})
    first = automaton.add_state()
    second = automaton.add_state()
    transition = automaton.add_transition(first.identifier, second.identifier, "a")
    automaton.add_transition(first.identifier, second.identifier, "b")

    automaton.remove_symbol("a", remove_invalid_transitions=True)

    assert automaton.alphabet == frozenset({"b"})
    assert automaton.transitions == (transition,)
    assert transition.symbols == {"b"}


def test_transition_symbols_can_be_replaced_transactionally() -> None:
    automaton = DFA({"a", "b", "c"})
    source = automaton.add_state()
    target = automaton.add_state()
    transition = automaton.add_transition(source.identifier, target.identifier, "a")
    automaton.add_transition(source.identifier, target.identifier, "b")

    updated = automaton.set_transition_symbols(
        source.identifier,
        target.identifier,
        {"b", "c"},
    )

    assert updated is transition
    assert transition.symbols == {"b", "c"}


def test_transition_symbols_replacement_rejects_empty_set() -> None:
    automaton = DFA({"a"})
    source = automaton.add_state()
    target = automaton.add_state()
    transition = automaton.add_transition(source.identifier, target.identifier, "a")

    with pytest.raises(InvalidSymbolError, match="at least one"):
        automaton.set_transition_symbols(source.identifier, target.identifier, [])

    assert transition.symbols == {"a"}


def test_transition_symbols_replacement_preserves_dfa_rule() -> None:
    automaton = DFA({"a", "b"})
    source = automaton.add_state()
    first_target = automaton.add_state()
    second_target = automaton.add_state()
    first = automaton.add_transition(source.identifier, first_target.identifier, "a")
    second = automaton.add_transition(source.identifier, second_target.identifier, "b")

    with pytest.raises(DuplicateTransitionError):
        automaton.set_transition_symbols(
            source.identifier,
            second_target.identifier,
            {"a", "b"},
        )

    assert first.symbols == {"a"}
    assert second.symbols == {"b"}


def test_get_transition_reports_unknown_edge() -> None:
    automaton = DFA({"a"})
    source = automaton.add_state()
    target = automaton.add_state()

    with pytest.raises(UnknownTransitionError):
        automaton.get_transition(source.identifier, target.identifier)


def test_renaming_state_updates_transition_endpoint_references() -> None:
    automaton = DFA({"a"})
    source = automaton.add_state()
    target = automaton.add_state()
    transition = automaton.add_transition(source.identifier, target.identifier, "a")

    automaton.rename_state(source.identifier, "inicio")

    assert transition.source.identifier == "inicio"
    assert automaton.get_transition("inicio", target.identifier) is transition


def test_clear_resets_complete_document_and_automatic_ids() -> None:
    automaton = DFA({"a"})
    source = automaton.add_state()
    target = automaton.add_state()
    automaton.add_transition(source.identifier, target.identifier, "a")

    automaton.clear()
    new_state = automaton.add_state()

    assert automaton.alphabet == frozenset()
    assert automaton.transitions == ()
    assert [state.identifier for state in automaton.states] == ["q0"]
    assert new_state.identifier == "q0"
