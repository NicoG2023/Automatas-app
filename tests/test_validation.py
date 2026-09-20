from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.model.state import State
from app_automatas.services.validation import validate_automaton


def _issue_codes(automaton: DFA | NFA) -> set[str]:
    return {issue.code for issue in validate_automaton(automaton).issues}


def test_empty_automaton_reports_missing_state_and_initial_state() -> None:
    automaton = DFA()

    result = validate_automaton(automaton)

    assert not result.is_valid
    assert _issue_codes(automaton) == {"no_states", "no_initial_state"}


def test_state_without_initial_state_is_not_ready_to_simulate() -> None:
    automaton = DFA(["a"])
    automaton.add_state("q0")

    assert _issue_codes(automaton) == {"no_initial_state"}


def test_automaton_without_accepting_states_is_structurally_valid() -> None:
    automaton = DFA()
    automaton.add_state("q0", is_initial=True)

    result = validate_automaton(automaton)

    assert result.is_valid
    assert result.issues == ()


def test_incomplete_dfa_is_valid_before_simulation() -> None:
    automaton = DFA(["a", "b"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1", is_accepting=True)
    automaton.add_transition("q0", "q1", "a")

    result = validate_automaton(automaton)

    assert result.is_valid


def test_nfa_can_have_multiple_destinations_for_same_symbol() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1", is_accepting=True)
    automaton.add_state("q2")
    automaton.add_transition("q0", "q1", "a")
    automaton.add_transition("q0", "q2", "a")

    assert validate_automaton(automaton).is_valid


def test_validator_defensively_reports_symbol_outside_alphabet() -> None:
    automaton = DFA(["a"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    transition = automaton.add_transition("q0", "q1", "a")
    transition.symbols.add("b")

    assert "symbol_outside_alphabet" in _issue_codes(automaton)


def test_validator_defensively_reports_epsilon_transition() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    transition = automaton.add_transition("q0", "q1", "a")
    transition.symbols.add("ε")

    assert "epsilon_transition" in _issue_codes(automaton)


def test_validator_defensively_reports_empty_transition_symbols() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    transition = automaton.add_transition("q0", "q1", "a")
    transition.symbols.clear()

    assert "transition_without_symbols" in _issue_codes(automaton)


def test_validator_defensively_reports_nondeterministic_dfa() -> None:
    automaton = DFA(["a", "b"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    automaton.add_state("q2")
    automaton.add_transition("q0", "q1", "a")
    second = automaton.add_transition("q0", "q2", "b")
    second.symbols.add("a")

    assert "nondeterministic_dfa" in _issue_codes(automaton)


def test_validator_defensively_reports_transition_to_unknown_state() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    transition = automaton.add_transition("q0", "q1", "a")
    transition.target = State("ghost")

    assert "unknown_transition_state" in _issue_codes(automaton)
