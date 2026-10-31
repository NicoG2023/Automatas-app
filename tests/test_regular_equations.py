from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.services.regular_equations import build_initial_equation_system
from app_automatas.services.regular_expression import Variable


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


def test_builds_same_initial_equations_as_cc3_example() -> None:
    system = build_initial_equation_system(_cc3_automaton())

    assert system.render() == (
        "A0 = bA1",
        "A1 = bA1 ∪ aA2",
        "A2 = bA3 ∪ λ",
        "A3 = aA4 ∪ λ",
        "A4 = bA3 ∪ bA1",
    )
    assert system.initial_variable == Variable("A0")


def test_nfa_keeps_same_symbol_to_multiple_destinations() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    automaton.add_state("q2")
    automaton.add_transition("q0", "q1", "a")
    automaton.add_transition("q0", "q2", "a")

    system = build_initial_equation_system(automaton)

    assert system.equation_for("q0").render() == "A0 = aA1 ∪ aA2"


def test_symbols_grouped_on_same_edge_are_rendered_as_one_union_label() -> None:
    automaton = DFA(["a", "b"])
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1", is_accepting=True)
    automaton.add_transition("q0", "q1", "b")
    automaton.add_transition("q0", "q1", "a")

    system = build_initial_equation_system(automaton)

    assert system.equation_for("q0").render() == "A0 = (a ∪ b)A1"
    assert system.equation_for("q1").render() == "A1 = λ"


def test_dead_non_accepting_state_has_empty_language_equation() -> None:
    automaton = DFA(["a"])
    automaton.add_state("q0", is_initial=True)

    system = build_initial_equation_system(automaton)

    assert system.render() == ("A0 = ∅",)


def test_custom_state_names_keep_an_explicit_variable_mapping() -> None:
    automaton = DFA(["a"])
    automaton.add_state("inicio", is_initial=True)
    automaton.add_state("fin", is_accepting=True)
    automaton.add_transition("inicio", "fin", "a")

    system = build_initial_equation_system(automaton)

    assert system.render() == (
        "A[inicio] = aA[fin]",
        "A[fin] = λ",
    )
    assert system.variable_for("inicio") == Variable("A[inicio]")


def test_system_can_be_built_before_an_initial_state_is_selected() -> None:
    automaton = NFA(["a"])
    automaton.add_state("q0", is_accepting=True)

    system = build_initial_equation_system(automaton)

    assert system.render() == ("A0 = λ",)
    assert system.initial_variable is None
