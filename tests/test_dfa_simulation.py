import pytest

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.services.simulation import (
    DFASimulator,
    InvalidSimulationAutomatonError,
    InvalidSimulationInputError,
    SimulationError,
)


def _binary_dfa() -> DFA:
    automaton = DFA(["0", "1"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1", is_accepting=True)
    automaton.add_transition("q0", "q1", "1")
    automaton.add_transition("q0", "q0", "0")
    automaton.add_transition("q1", "q1", "1")
    automaton.add_transition("q1", "q0", "0")
    return automaton


def test_simulator_requires_a_dfa() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_initial=True)

    with pytest.raises(TypeError, match="requires a DFA"):
        DFASimulator(automaton)  # type: ignore[arg-type]


def test_simulator_rejects_structurally_invalid_dfa() -> None:
    automaton = DFA(["a"])
    automaton.add_state("q0")

    with pytest.raises(InvalidSimulationAutomatonError) as exc_info:
        DFASimulator(automaton)

    assert "Selecciona un estado inicial." in exc_info.value.messages


def test_snapshot_is_unavailable_before_start() -> None:
    simulator = DFASimulator(_binary_dfa())

    with pytest.raises(SimulationError, match="not been started"):
        _ = simulator.snapshot


def test_start_rejects_input_symbols_outside_alphabet() -> None:
    simulator = DFASimulator(_binary_dfa())

    with pytest.raises(InvalidSimulationInputError) as exc_info:
        simulator.start("102x")

    assert exc_info.value.symbols == frozenset({"2", "x"})


def test_manual_steps_report_processed_remaining_state_and_transition() -> None:
    simulator = DFASimulator(_binary_dfa())

    initial = simulator.start("01")
    first = simulator.step()
    second = simulator.step()

    assert initial.status == "ready"
    assert initial.current_state_id == "q0"
    assert initial.processed_input == ""
    assert initial.remaining_input == "01"
    assert initial.next_symbol == "0"

    assert first.status == "running"
    assert first.current_state_id == "q0"
    assert first.last_symbol == "0"
    assert first.last_transition == ("q0", "q0")
    assert first.processed_input == "0"
    assert first.remaining_input == "1"
    assert first.next_symbol == "1"

    assert second.status == "accepted"
    assert second.current_state_id == "q1"
    assert second.last_symbol == "1"
    assert second.last_transition == ("q0", "q1")
    assert second.processed_input == "01"
    assert second.remaining_input == ""


def test_complete_input_rejects_when_final_state_is_not_accepting() -> None:
    simulator = DFASimulator(_binary_dfa())

    simulator.start("10")
    simulator.step()
    result = simulator.step()

    assert result.status == "rejected"
    assert result.current_state_id == "q0"
    assert result.processed_input == "10"
    assert "no es de aceptación" in (result.rejection_reason or "")


def test_missing_transition_rejects_on_current_symbol_without_consuming_it() -> None:
    automaton = DFA(["a", "b"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1", is_accepting=True)
    automaton.add_transition("q0", "q1", "a")
    simulator = DFASimulator(automaton)

    simulator.start("b")
    result = simulator.step()

    assert result.status == "rejected"
    assert result.current_state_id == "q0"
    assert result.last_symbol == "b"
    assert result.last_transition is None
    assert result.processed_input == ""
    assert result.remaining_input == "b"
    assert "No existe una transición" in (result.rejection_reason or "")


def test_empty_string_is_accepted_when_initial_state_is_accepting() -> None:
    automaton = DFA(["a"])
    automaton.add_state("q0", is_initial=True, is_accepting=True)

    result = DFASimulator(automaton).start("")

    assert result.status == "accepted"
    assert result.is_accepted
    assert result.processed_input == ""
    assert result.remaining_input == ""


def test_empty_string_is_rejected_when_initial_state_is_not_accepting() -> None:
    automaton = DFA(["a"])
    automaton.add_state("q0", is_initial=True)

    result = DFASimulator(automaton).start("")

    assert result.status == "rejected"
    assert not result.is_accepted
    assert "cadena vacía" in (result.rejection_reason or "")


def test_reset_restarts_same_input() -> None:
    simulator = DFASimulator(_binary_dfa())
    simulator.start("01")
    simulator.step()

    reset = simulator.reset()

    assert reset.status == "ready"
    assert reset.current_state_id == "q0"
    assert reset.position == 0
    assert reset.remaining_input == "01"
    assert reset.last_transition is None
