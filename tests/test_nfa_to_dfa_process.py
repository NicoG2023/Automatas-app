from app_automatas.model.nfa import NFA
from app_automatas.services.nfa_to_dfa_process import (
    build_conversion_process,
    render_subset,
)


def _classroom_nfa() -> NFA:
    automaton = NFA(["a", "b"])
    automaton.add_state("q0", is_initial=True, is_accepting=True)
    automaton.add_state("q1")
    automaton.add_state("q2")
    automaton.add_state("q3")
    automaton.add_transition("q0", "q1", "a")
    automaton.add_transition("q0", "q2", "a")
    automaton.add_transition("q1", "q0", "b")
    automaton.add_transition("q2", "q3", "b")
    automaton.add_transition("q3", "q0", "a")
    return automaton


def test_process_starts_with_original_singleton_rows() -> None:
    process = build_conversion_process(_classroom_nfa())

    assert [render_subset(row[0]) for row in process.original_rows] == [
        "q0",
        "q1",
        "q2",
        "q3",
    ]
    first_cells = dict(process.original_rows[0][1])
    assert first_cells["a"] == frozenset({"q1", "q2"})
    assert first_cells["b"] == frozenset()


def test_process_expands_new_subsets_until_closure() -> None:
    process = build_conversion_process(_classroom_nfa())

    assert [render_subset(row[0]) for row in process.expanded_rows] == [
        "q0",
        "q1",
        "q2",
        "q3",
        "{q1,q2}",
        "{q0,q3}",
        "{q0,q1,q2}",
    ]


def test_process_renames_rows_to_k_states_in_order() -> None:
    process = build_conversion_process(_classroom_nfa())

    assert [(render_subset(subset), name) for subset, name in process.names] == [
        ("q0", "k0"),
        ("q1", "k1"),
        ("q2", "k2"),
        ("q3", "k3"),
        ("{q1,q2}", "k4"),
        ("{q0,q3}", "k5"),
        ("{q0,q1,q2}", "k6"),
    ]


def test_process_complete_dfa_contains_all_table_rows() -> None:
    process = build_conversion_process(_classroom_nfa())
    dfa = process.complete_dfa

    assert {state.identifier for state in dfa.states} == {
        "k0",
        "k1",
        "k2",
        "k3",
        "k4",
        "k5",
        "k6",
    }
    assert dfa.destinations("k0", "a") == frozenset({"k4"})
    assert dfa.destinations("k4", "b") == frozenset({"k5"})
    assert dfa.destinations("k5", "a") == frozenset({"k6"})
    assert dfa.destinations("k6", "a") == frozenset({"k4"})
    assert dfa.destinations("k6", "b") == frozenset({"k5"})


def test_process_removes_unreachable_states_only_at_final_step() -> None:
    process = build_conversion_process(_classroom_nfa())

    assert process.unreachable_names == ("k1", "k2", "k3")
    assert {state.identifier for state in process.reachable_dfa.states} == {
        "k0",
        "k4",
        "k5",
        "k6",
    }
    assert process.reachable_dfa.initial_state is not None
    assert process.reachable_dfa.initial_state.identifier == "k0"


def test_accepting_k_states_include_any_subset_containing_original_final() -> None:
    process = build_conversion_process(_classroom_nfa())

    assert {state.identifier for state in process.complete_dfa.accepting_states} == {
        "k0",
        "k5",
        "k6",
    }
