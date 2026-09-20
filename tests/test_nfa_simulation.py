import pytest

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.services.simulation import (
    InvalidSimulationInputError,
    NFASimulator,
    SimulationError,
)


def _branching_nfa() -> NFA:
    automaton = NFA(["a", "b"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    automaton.add_state("q2")
    automaton.add_state("q3", is_accepting=True)
    automaton.add_transition("q0", "q1", "a")
    automaton.add_transition("q0", "q2", "a")
    automaton.add_transition("q1", "q3", "b")
    return automaton


def test_nfa_simulator_requires_an_nfa() -> None:
    automaton = DFA(["a"])
    automaton.add_state("q0", is_initial=True)

    with pytest.raises(TypeError, match="requires an NFA"):
        NFASimulator(automaton)  # type: ignore[arg-type]


def test_nfa_snapshot_is_unavailable_before_start() -> None:
    simulator = NFASimulator(_branching_nfa())

    with pytest.raises(SimulationError, match="not been started"):
        _ = simulator.snapshot


def test_nfa_start_rejects_symbols_outside_alphabet() -> None:
    simulator = NFASimulator(_branching_nfa())

    with pytest.raises(InvalidSimulationInputError) as exc_info:
        simulator.start("ac")

    assert exc_info.value.symbols == frozenset({"c"})


def test_nfa_fans_out_to_every_reachable_state_for_symbol() -> None:
    simulator = NFASimulator(_branching_nfa())

    initial = simulator.start("ab")
    first = simulator.step()

    assert initial.active_state_ids == frozenset({"q0"})
    assert first.status == "running"
    assert first.active_state_ids == frozenset({"q1", "q2"})
    assert first.last_symbol == "a"
    assert set(first.last_transitions) == {("q0", "q1"), ("q0", "q2")}
    assert first.processed_input == "a"
    assert first.remaining_input == "b"


def test_nfa_discards_only_dead_branches_while_others_continue() -> None:
    simulator = NFASimulator(_branching_nfa())
    simulator.start("ab")
    simulator.step()

    result = simulator.step()

    assert result.status == "accepted"
    assert result.active_state_ids == frozenset({"q3"})
    assert result.last_transitions == (("q1", "q3"),)
    assert result.processed_input == "ab"
    assert result.remaining_input == ""


def test_nfa_rejects_when_no_active_branch_can_continue() -> None:
    simulator = NFASimulator(_branching_nfa())
    simulator.start("aa")
    simulator.step()

    result = simulator.step()

    assert result.status == "rejected"
    assert result.active_state_ids == frozenset()
    assert result.last_symbol == "a"
    assert result.last_transitions == ()
    assert result.processed_input == "a"
    assert result.remaining_input == "a"
    assert "Ningún recorrido" in (result.rejection_reason or "")


def test_nfa_accepts_if_at_least_one_final_branch_is_accepting() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1", is_accepting=True)
    automaton.add_state("q2")
    automaton.add_transition("q0", "q1", "a")
    automaton.add_transition("q0", "q2", "a")

    result = NFASimulator(automaton).start("a")
    simulator = NFASimulator(automaton)
    simulator.start("a")
    result = simulator.step()

    assert result.status == "accepted"
    assert result.active_state_ids == frozenset({"q1", "q2"})


def test_nfa_rejects_when_input_finishes_without_accepting_state() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    automaton.add_transition("q0", "q1", "a")
    simulator = NFASimulator(automaton)

    simulator.start("a")
    result = simulator.step()

    assert result.status == "rejected"
    assert result.active_state_ids == frozenset({"q1"})
    assert "sin ningún recorrido" in (result.rejection_reason or "")


def test_nfa_empty_string_uses_initial_acceptance() -> None:
    accepting = NFA(["a"])
    accepting.add_state("q0", is_initial=True, is_accepting=True)
    rejecting = NFA(["a"])
    rejecting.add_state("q0", is_initial=True)

    accepted = NFASimulator(accepting).start("")
    rejected = NFASimulator(rejecting).start("")

    assert accepted.status == "accepted"
    assert accepted.active_state_ids == frozenset({"q0"})
    assert rejected.status == "rejected"
    assert rejected.active_state_ids == frozenset({"q0"})


def test_nfa_reset_restarts_same_input_from_initial_state() -> None:
    simulator = NFASimulator(_branching_nfa())
    simulator.start("ab")
    simulator.step()

    reset = simulator.reset()

    assert reset.status == "ready"
    assert reset.position == 0
    assert reset.active_state_ids == frozenset({"q0"})
    assert reset.remaining_input == "ab"
    assert reset.last_transitions == ()
