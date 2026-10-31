import pytest

from app_automatas.services.regular_equations import (
    RegularEquation,
    build_initial_equation_system,
    substitute_equation,
)
from app_automatas.services.regular_expression import (
    LAMBDA,
    Symbol,
    Variable,
    concatenate,
    distribute_concatenation,
    star,
    union,
)
from app_automatas.model.nfa import NFA


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


def test_cc3_substitution_replaces_a4_in_a3_and_distributes() -> None:
    system = build_initial_equation_system(_cc3_automaton())

    step = substitute_equation(
        system.equation_for("q3"),
        system.equation_for("q4"),
    )

    assert step.target_before.render() == "A3 = aA4 ∪ λ"
    assert step.source.render() == "A4 = bA3 ∪ bA1"
    assert step.render_substitution() == "A3 = a(bA3 ∪ bA1) ∪ λ"
    assert step.render_result() == "A3 = abA3 ∪ abA1 ∪ λ"


def test_substitution_replaces_every_occurrence_of_source_variable() -> None:
    a0 = Variable("A0")
    a1 = Variable("A1")
    target = RegularEquation(
        state_id="q0",
        variable=a0,
        expression=union(concatenate(Symbol("a"), a1), concatenate(Symbol("b"), a1)),
    )
    source = RegularEquation(
        state_id="q1",
        variable=a1,
        expression=union(Symbol("c"), LAMBDA),
    )

    step = substitute_equation(target, source)

    assert step.render_substitution() == "A0 = a(c ∪ λ) ∪ b(c ∪ λ)"
    assert step.render_result() == "A0 = ac ∪ a ∪ bc ∪ b"


def test_substitution_does_not_recursively_replace_inside_replacement() -> None:
    a0 = Variable("A0")
    a1 = Variable("A1")
    target = RegularEquation("q0", a0, concatenate(Symbol("a"), a1))
    source = RegularEquation(
        "q1",
        a1,
        union(concatenate(Symbol("b"), a1), Symbol("c")),
    )

    step = substitute_equation(target, source)

    assert step.render_result() == "A0 = abA1 ∪ ac"


def test_distribution_expands_multiple_union_factors_in_stable_order() -> None:
    expression = concatenate(
        union(Symbol("a"), Symbol("b")),
        union(Symbol("c"), Symbol("d")),
    )

    assert distribute_concatenation(expression).render() == "ac ∪ ad ∪ bc ∪ bd"


def test_distribution_preserves_union_inside_kleene_star() -> None:
    expression = concatenate(
        Symbol("a"),
        star(union(Symbol("b"), Symbol("c"))),
    )

    assert distribute_concatenation(expression).render() == "a(b ∪ c)*"


def test_substitution_requires_source_variable_to_occur_in_target() -> None:
    target = RegularEquation("q0", Variable("A0"), Symbol("a"))
    source = RegularEquation("q1", Variable("A1"), Symbol("b"))

    with pytest.raises(ValueError, match="A1 does not occur in A0"):
        substitute_equation(target, source)


def test_equation_cannot_be_substituted_into_itself() -> None:
    equation = RegularEquation("q0", Variable("A0"), Symbol("a"))

    with pytest.raises(ValueError, match="cannot be substituted into itself"):
        substitute_equation(equation, equation)
