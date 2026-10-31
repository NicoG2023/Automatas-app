import pytest

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.services.regular_equations import (
    ArdenApplicationStep,
    EquationSubstitutionStep,
    automaton_to_regular_expression,
    build_initial_equation_system,
    solve_equation_system,
)
from app_automatas.services.regular_expression import variables_in_expression


def _cc3_automaton() -> NFA:
    automaton = NFA(["a", "b"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    automaton.add_state("q2", is_accepting=True)
    automaton.add_state("q3", is_accepting=True)
    automaton.add_state("q4")

    automaton.add_transition("q0", "q1", "b")
    automaton.add_transition("q1", "q1", "b")
    automaton.add_transition("q1", "q2", "a")
    automaton.add_transition("q2", "q3", "b")
    automaton.add_transition("q3", "q4", "a")
    automaton.add_transition("q4", "q3", "b")
    automaton.add_transition("q4", "q1", "b")
    return automaton


def test_cc3_solver_replays_replacements_and_arden_in_course_order() -> None:
    solution = automaton_to_regular_expression(_cc3_automaton())

    assert solution.initial_system.render() == (
        "A0 = bA1",
        "A1 = bA1 ∪ aA2",
        "A2 = bA3 ∪ λ",
        "A3 = aA4 ∪ λ",
        "A4 = bA3 ∪ bA1",
    )
    assert solution.elimination_order == ("q4", "q3", "q2", "q1", "q0")
    assert [type(step) for step in solution.steps] == [
        EquationSubstitutionStep,
        ArdenApplicationStep,
        EquationSubstitutionStep,
        EquationSubstitutionStep,
        ArdenApplicationStep,
        EquationSubstitutionStep,
    ]

    first = solution.steps[0]
    assert isinstance(first, EquationSubstitutionStep)
    assert first.source.render() == "A4 = bA3 ∪ bA1"
    assert first.render_substitution() == "A3 = a(bA3 ∪ bA1) ∪ λ"
    assert first.render_result() == "A3 = abA3 ∪ abA1 ∪ λ"

    first_arden = solution.steps[1]
    assert isinstance(first_arden, ArdenApplicationStep)
    assert first_arden.render_identification() == "A = ab, X = A3, B = abA1 ∪ λ"
    assert first_arden.render_result() == "A3 = (ab)*(abA1 ∪ λ)"

    assert solution.steps[2].render_result() == (
        "A2 = b(ab)+A1 ∪ b(ab)* ∪ λ"
    )
    assert solution.steps[3].render_result() == (
        "A1 = bA1 ∪ ab(ab)+A1 ∪ (ab)+ ∪ a"
    )

    second_arden = solution.steps[4]
    assert isinstance(second_arden, ArdenApplicationStep)
    assert second_arden.render_identification() == (
        "A = b ∪ ab(ab)+, X = A1, B = (ab)+ ∪ a"
    )
    assert second_arden.render_result() == (
        "A1 = (b ∪ ab(ab)+)*((ab)+ ∪ a)"
    )

    assert solution.steps[5].render_substitution() == (
        "A0 = b(b ∪ ab(ab)+)*((ab)+ ∪ a)"
    )
    assert solution.render_result() == (
        "A0 = b(b ∪ ab(ab)+)*((ab)+ ∪ a)"
    )
    assert not variables_in_expression(solution.expression)


def test_solver_handles_initial_state_with_direct_self_loop() -> None:
    automaton = DFA(["a"])
    automaton.add_state("q0", is_initial=True, is_accepting=True)
    automaton.add_transition("q0", "q0", "a")

    solution = automaton_to_regular_expression(automaton)

    assert solution.elimination_order == ("q0",)
    assert len(solution.steps) == 1
    assert isinstance(solution.steps[0], ArdenApplicationStep)
    assert solution.render_result() == "A0 = a*"


def test_solver_substitutes_dead_state_to_empty_set() -> None:
    automaton = DFA(["a"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    automaton.add_transition("q0", "q1", "a")

    solution = automaton_to_regular_expression(automaton)

    assert solution.render_result() == "A0 = ∅"
    assert len(solution.steps) == 1
    assert isinstance(solution.steps[0], EquationSubstitutionStep)


def test_solver_keeps_initial_state_for_last_even_if_added_in_middle() -> None:
    automaton = NFA(["a", "b"])
    automaton.add_state("left")
    automaton.add_state("start", is_initial=True)
    automaton.add_state("final", is_accepting=True)
    automaton.add_transition("start", "left", "a")
    automaton.add_transition("left", "final", "b")

    solution = automaton_to_regular_expression(automaton)

    assert solution.elimination_order == ("final", "left", "start")
    assert solution.render_result() == "A[start] = ab"



def test_solver_resolves_cycle_that_reaches_the_initial_state() -> None:
    automaton = NFA(["a", "b"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1", is_accepting=True)
    automaton.add_transition("q0", "q1", "a")
    automaton.add_transition("q1", "q0", "b")

    solution = automaton_to_regular_expression(automaton)

    assert solution.elimination_order == ("q1", "q0")
    assert [type(step) for step in solution.steps] == [
        EquationSubstitutionStep,
        ArdenApplicationStep,
    ]
    assert solution.steps[0].render_result() == "A0 = abA0 ∪ a"
    assert solution.render_result() == "A0 = (ab)*a"
    assert not variables_in_expression(solution.expression)

def test_solver_returns_lambda_for_accepting_initial_state_without_transitions() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_initial=True, is_accepting=True)

    solution = automaton_to_regular_expression(automaton)

    assert solution.steps == ()
    assert solution.render_result() == "A0 = λ"


def test_solver_requires_an_initial_state() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_accepting=True)
    system = build_initial_equation_system(automaton)

    with pytest.raises(ValueError, match="without an initial state"):
        solve_equation_system(system)


def test_solver_rejects_non_system_input() -> None:
    with pytest.raises(TypeError, match="RegularEquationSystem"):
        solve_equation_system(object())  # type: ignore[arg-type]
