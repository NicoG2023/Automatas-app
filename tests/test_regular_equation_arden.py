import pytest

from app_automatas.model.nfa import NFA
from app_automatas.services.regular_equations import (
    RegularEquation,
    apply_arden,
    build_initial_equation_system,
    substitute_equation,
)
from app_automatas.services.regular_expression import (
    LAMBDA,
    Symbol,
    Variable,
    concatenate,
    star,
    union,
)


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


def test_cc3_arden_after_substituting_a4_in_a3() -> None:
    system = build_initial_equation_system(_cc3_automaton())
    substitution = substitute_equation(
        system.equation_for("q3"),
        system.equation_for("q4"),
    )

    step = apply_arden(substitution.target_after)

    assert step.equation_before.render() == "A3 = abA3 ∪ abA1 ∪ λ"
    assert step.coefficient.render() == "ab"
    assert step.variable.render() == "A3"
    assert step.remainder.render() == "abA1 ∪ λ"
    assert step.render_identification() == "A = ab, X = A3, B = abA1 ∪ λ"
    assert step.render_arden_form() == "A3 = abA3 ∪ abA1 ∪ λ"
    assert step.render_result() == "A3 = (ab)*(abA1 ∪ λ)"


def test_arden_groups_multiple_recursive_alternatives() -> None:
    x = Variable("A0")
    equation = RegularEquation(
        "q0",
        x,
        union(
            concatenate(Symbol("a"), x),
            concatenate(Symbol("b"), x),
            Symbol("c"),
        ),
    )

    step = apply_arden(equation)

    assert step.coefficient.render() == "a ∪ b"
    assert step.remainder.render() == "c"
    assert step.render_arden_form() == "A0 = (a ∪ b)A0 ∪ c"
    assert step.render_result() == "A0 = (a ∪ b)*c"


def test_arden_with_no_remainder_solves_to_empty_set() -> None:
    x = Variable("A0")
    equation = RegularEquation("q0", x, concatenate(Symbol("a"), x))

    step = apply_arden(equation)

    assert step.remainder.render() == "∅"
    assert step.render_result() == "A0 = ∅"


def test_arden_rejects_equation_without_recursive_term() -> None:
    equation = RegularEquation("q0", Variable("A0"), Symbol("a"))

    with pytest.raises(ValueError, match="has no recursive AX term"):
        apply_arden(equation)


def test_arden_rejects_recursion_when_variable_is_not_final_factor() -> None:
    x = Variable("A0")
    equation = RegularEquation("q0", x, concatenate(x, Symbol("a")))

    with pytest.raises(ValueError, match="not in right-linear AX form"):
        apply_arden(equation)


def test_arden_rejects_recursive_coefficient_that_accepts_lambda() -> None:
    x = Variable("A0")
    equation = RegularEquation("q0", x, union(x, Symbol("b")))

    with pytest.raises(ValueError, match="does not accept λ"):
        apply_arden(equation)


def test_arden_rejects_recursive_coefficient_with_unknown_nullability() -> None:
    x = Variable("A0")
    other = Variable("A1")
    equation = RegularEquation(
        "q0",
        x,
        union(concatenate(other, x), Symbol("b")),
    )

    with pytest.raises(ValueError, match="unknown λ-nullability"):
        apply_arden(equation)


def test_arden_rejects_nullable_star_coefficient() -> None:
    x = Variable("A0")
    equation = RegularEquation(
        "q0",
        x,
        union(concatenate(star(Symbol("a")), x), Symbol("b")),
    )

    with pytest.raises(ValueError, match="does not accept λ"):
        apply_arden(equation)
