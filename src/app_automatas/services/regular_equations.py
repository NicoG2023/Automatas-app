"""Build the initial regular-equation system associated with an automaton."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app_automatas.model.automaton import Automaton, EPSILON_SYMBOLS
from app_automatas.services.regular_expression import (
    EMPTY_SET,
    LAMBDA,
    Concatenation,
    RegularExpression,
    Symbol,
    UnionExpression,
    Variable,
    concatenate,
    contains_variable,
    distribute_concatenation,
    nullable_status,
    star,
    substitute_variable,
    union,
    variables_in_expression,
)


@dataclass(frozen=True, slots=True)
class RegularEquation:
    """One equation Ai = Ri from the automaton-to-regex procedure."""

    state_id: str
    variable: Variable
    expression: RegularExpression

    def render(self) -> str:
        return f"{self.variable.render()} = {self.expression.render()}"


@dataclass(frozen=True, slots=True)
class EquationSubstitutionStep:
    """Pedagogical record of replacing one equation variable in another."""

    target_before: RegularEquation
    source: RegularEquation
    substituted_expression: RegularExpression
    target_after: RegularEquation

    def render_substitution(self) -> str:
        return (
            f"{self.target_before.variable.render()} = "
            f"{self.substituted_expression.render()}"
        )

    def render_result(self) -> str:
        return self.target_after.render()


@dataclass(frozen=True, slots=True)
class ArdenApplicationStep:
    """Pedagogical record of one valid application of Arden's lemma."""

    equation_before: RegularEquation
    coefficient: RegularExpression
    remainder: RegularExpression
    equation_after: RegularEquation

    @property
    def variable(self) -> Variable:
        return self.equation_before.variable

    def render_identification(self) -> str:
        return (
            f"A = {self.coefficient.render()}, "
            f"X = {self.variable.render()}, "
            f"B = {self.remainder.render()}"
        )

    def render_arden_form(self) -> str:
        recursive_term = concatenate(self.coefficient, self.variable)
        expression = union(recursive_term, self.remainder)
        return f"{self.variable.render()} = {expression.render()}"

    def render_result(self) -> str:
        return self.equation_after.render()


EquationProcessStep = EquationSubstitutionStep | ArdenApplicationStep


@dataclass(frozen=True, slots=True)
class RegularEquationSolution:
    """Complete, replayable solution of an automaton equation system."""

    initial_system: "RegularEquationSystem"
    elimination_order: tuple[str, ...]
    steps: tuple[EquationProcessStep, ...]
    final_equation: RegularEquation

    @property
    def expression(self) -> RegularExpression:
        """Return the regular expression equivalent to the initial-state language."""
        return self.final_equation.expression

    def render_result(self) -> str:
        return self.final_equation.render()


@dataclass(frozen=True, slots=True)
class RegularEquationSystem:
    """Immutable initial system plus the state-to-variable correspondence."""

    equations: tuple[RegularEquation, ...]
    variables: tuple[tuple[str, Variable], ...]
    initial_variable: Variable | None

    def variable_for(self, state_id: str) -> Variable:
        try:
            return dict(self.variables)[state_id]
        except KeyError as exc:
            raise KeyError(f"Unknown state in equation system: {state_id}") from exc

    def equation_for(self, state_id: str) -> RegularEquation:
        for equation in self.equations:
            if equation.state_id == state_id:
                return equation
        raise KeyError(f"Unknown state in equation system: {state_id}")

    def equation_for_variable(self, variable: Variable) -> RegularEquation:
        for equation in self.equations:
            if equation.variable == variable:
                return equation
        raise KeyError(f"Unknown variable in equation system: {variable.render()}")

    def render(self) -> tuple[str, ...]:
        return tuple(equation.render() for equation in self.equations)


def substitute_equation(
    target: RegularEquation,
    source: RegularEquation,
    *,
    distribute: bool = True,
) -> EquationSubstitutionStep:
    """Substitute ``source`` into ``target`` and optionally distribute unions.

    Intermediate substitutions are distributed when that is useful to expose a
    recursive AX term for Arden.  Once a solved source contains no variables, the
    solver can preserve the factored form used in the final line of CC3.
    """
    if target.variable == source.variable:
        raise ValueError("An equation cannot be substituted into itself")
    if not contains_variable(target.expression, source.variable):
        raise ValueError(
            f"{source.variable.render()} does not occur in {target.variable.render()}"
        )

    substituted = substitute_variable(
        target.expression,
        source.variable,
        source.expression,
    )
    result = distribute_concatenation(substituted) if distribute else substituted
    after = RegularEquation(
        state_id=target.state_id,
        variable=target.variable,
        expression=result,
    )

    return EquationSubstitutionStep(
        target_before=target,
        source=source,
        substituted_expression=substituted,
        target_after=after,
    )


def apply_arden(equation: RegularEquation) -> ArdenApplicationStep:
    """Solve one right-linear recursive equation with Arden's lemma.

    The supported shape is ``X = AX ∪ B``.  Multiple recursive alternatives
    such as ``aX ∪ bX`` are grouped into ``A = a ∪ b``.  The recursive variable
    must be the final factor of each recursive term, matching the right-linear
    equations generated from automata.
    """
    recursive_coefficients: list[RegularExpression] = []
    remainder_terms: list[RegularExpression] = []

    terms = (
        equation.expression.alternatives
        if isinstance(equation.expression, UnionExpression)
        else (equation.expression,)
    )

    for term in terms:
        coefficient = _recursive_coefficient(term, equation.variable)
        if coefficient is None:
            remainder_terms.append(term)
        else:
            recursive_coefficients.append(coefficient)

    if not recursive_coefficients:
        raise ValueError(
            f"{equation.variable.render()} has no recursive AX term for Arden's lemma"
        )

    coefficient = union(*recursive_coefficients)
    nullable = nullable_status(coefficient)
    if nullable is not False:
        detail = "accepts λ" if nullable is True else "has unknown λ-nullability"
        raise ValueError(
            "Arden's lemma requires a recursive coefficient A that does not "
            f"accept λ; {coefficient.render()} {detail}"
        )

    remainder = union(*remainder_terms) if remainder_terms else EMPTY_SET
    solved_expression = concatenate(star(coefficient), remainder)
    solved = RegularEquation(
        state_id=equation.state_id,
        variable=equation.variable,
        expression=solved_expression,
    )

    return ArdenApplicationStep(
        equation_before=equation,
        coefficient=coefficient,
        remainder=remainder,
        equation_after=solved,
    )


def _recursive_coefficient(
    term: RegularExpression,
    variable: Variable,
) -> RegularExpression | None:
    """Extract A from an ``AX`` term, rejecting non-right-linear recursion."""
    if term == variable:
        return LAMBDA

    if isinstance(term, Concatenation) and term.factors[-1] == variable:
        prefix = concatenate(*term.factors[:-1])
        if contains_variable(prefix, variable):
            raise ValueError(
                f"Recursive term {term.render()} contains "
                f"{variable.render()} more than once"
            )
        return prefix

    if contains_variable(term, variable):
        raise ValueError(
            f"Recursive term {term.render()} is not in right-linear AX form"
        )

    return None


def solve_equation_system(system: RegularEquationSystem) -> RegularEquationSolution:
    """Eliminate state variables until only the initial-state regex remains.

    Equations are processed in reverse construction order, while the initial
    state's equation is always left for last.  A recursive source equation is
    first solved with Arden's lemma and then substituted into every equation
    that is still active.  This mirrors the replacement sequence used in CC3.
    """
    if not isinstance(system, RegularEquationSystem):
        raise TypeError("solve_equation_system requires a RegularEquationSystem")
    if system.initial_variable is None:
        raise ValueError("Cannot solve an equation system without an initial state")

    initial_equation = system.equation_for_variable(system.initial_variable)
    working = {equation.state_id: equation for equation in system.equations}
    active_state_ids = [equation.state_id for equation in system.equations]
    non_initial_order = [
        equation.state_id
        for equation in reversed(system.equations)
        if equation.variable != system.initial_variable
    ]
    elimination_order = (*non_initial_order, initial_equation.state_id)
    steps: list[EquationProcessStep] = []

    for source_state_id in non_initial_order:
        source = working[source_state_id]

        if contains_variable(source.expression, source.variable):
            arden_step = apply_arden(source)
            steps.append(arden_step)
            source = arden_step.equation_after
            working[source_state_id] = source

        for target_state_id in tuple(active_state_ids):
            if target_state_id == source_state_id:
                continue
            target = working[target_state_id]
            if not contains_variable(target.expression, source.variable):
                continue

            substitution_step = substitute_equation(
                target,
                source,
                distribute=bool(variables_in_expression(source.expression)),
            )
            steps.append(substitution_step)
            working[target_state_id] = substitution_step.target_after

        active_state_ids.remove(source_state_id)

    final_equation = working[initial_equation.state_id]
    if contains_variable(final_equation.expression, final_equation.variable):
        arden_step = apply_arden(final_equation)
        steps.append(arden_step)
        final_equation = arden_step.equation_after
        working[initial_equation.state_id] = final_equation

    unresolved = variables_in_expression(final_equation.expression)
    if unresolved:
        names = ", ".join(sorted(variable.render() for variable in unresolved))
        raise RuntimeError(f"Equation solver left unresolved variables: {names}")

    return RegularEquationSolution(
        initial_system=system,
        elimination_order=elimination_order,
        steps=tuple(steps),
        final_equation=final_equation,
    )


def automaton_to_regular_expression(automaton: Automaton) -> RegularEquationSolution:
    """Build and completely solve the regular equations for an automaton."""
    return solve_equation_system(build_initial_equation_system(automaton))


def build_initial_equation_system(automaton: Automaton) -> RegularEquationSystem:
    """Create one right-language equation per state.

    For every transition qi --a--> qj, equation Ai receives the term aAj.
    Accepting states additionally receive λ.  This is the initial system used
    before substitutions and Arden's lemma are applied.
    """
    if not isinstance(automaton, Automaton):
        raise TypeError("build_initial_equation_system requires an Automaton")

    variables = tuple(
        (state.identifier, Variable(_variable_name(state.identifier)))
        for state in automaton.states
    )
    variable_map = dict(variables)

    equations: list[RegularEquation] = []
    for state in automaton.states:
        terms: list[RegularExpression] = []
        epsilon_closure = _epsilon_closure(automaton, state.identifier)

        for transition in automaton.transitions:
            if transition.source.identifier not in epsilon_closure:
                continue

            symbols = tuple(
                symbol
                for symbol in sorted(transition.symbols)
                if symbol not in EPSILON_SYMBOLS
            )
            if not symbols:
                continue

            label = union(*(Symbol(symbol) for symbol in symbols))
            terms.append(
                concatenate(label, variable_map[transition.target.identifier])
            )

        if any(
            automaton.get_state(state_id).is_accepting
            for state_id in epsilon_closure
        ):
            terms.append(LAMBDA)

        equations.append(
            RegularEquation(
                state_id=state.identifier,
                variable=variable_map[state.identifier],
                expression=union(*terms) if terms else EMPTY_SET,
            )
        )

    initial = automaton.initial_state
    initial_variable = (
        variable_map[initial.identifier]
        if initial is not None
        else None
    )

    return RegularEquationSystem(
        equations=tuple(equations),
        variables=variables,
        initial_variable=initial_variable,
    )


def _epsilon_closure(automaton: Automaton, state_id: str) -> frozenset[str]:
    closure = {state_id}
    pending = [state_id]
    while pending:
        source_id = pending.pop()
        for symbol in EPSILON_SYMBOLS:
            for target_id in automaton.destinations(source_id, symbol):
                if target_id in closure:
                    continue
                closure.add(target_id)
                pending.append(target_id)
    return frozenset(closure)


def _variable_name(state_id: str) -> str:
    """Use course-style A0 for q0, while keeping custom state names unambiguous."""
    match = re.fullmatch(r"q(\d+)", state_id)
    if match is not None:
        return f"A{match.group(1)}"
    return f"A[{state_id}]"
