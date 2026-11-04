"""Construct an epsilon-NFA from a regular expression."""

from __future__ import annotations

from dataclasses import dataclass

from app_automatas.model.nfa import EpsilonNFA
from app_automatas.services.regular_expression import (
    EMPTY_SET,
    LAMBDA,
    Concatenation,
    KleenePlus,
    KleeneStar,
    RegularExpression,
    Symbol,
    UnionExpression,
    concatenate,
    plus,
    star,
    union,
)


class RegularExpressionSyntaxError(ValueError):
    """Raised when an input string is not a supported regular expression."""


@dataclass(frozen=True, slots=True)
class _Fragment:
    start: int
    accepting: tuple[int, ...]


class _Parser:
    def __init__(self, source: str) -> None:
        self.source = source
        self.position = 0

    def parse(self) -> RegularExpression:
        expression = self._parse_union()
        self._skip_whitespace()
        if self.position != len(self.source):
            self._raise("Símbolo inesperado")
        return expression

    def _parse_union(self) -> RegularExpression:
        alternatives = [self._parse_concatenation()]
        while self._consume("|") or self._consume("∪"):
            alternatives.append(self._parse_concatenation())
        return union(*alternatives)

    def _parse_concatenation(self) -> RegularExpression:
        factors: list[RegularExpression] = []
        while True:
            self._skip_whitespace()
            if self.position >= len(self.source) or self.source[self.position] in ")|∪":
                break
            factors.append(self._parse_repetition())
        if not factors:
            self._raise("Se esperaba un símbolo o una expresión entre paréntesis")
        return concatenate(*factors)

    def _parse_repetition(self) -> RegularExpression:
        expression = self._parse_atom()
        while self._consume("*") or self._consume("+"):
            operator = self.source[self.position - 1]
            expression = star(expression) if operator == "*" else plus(expression)
        return expression

    def _parse_atom(self) -> RegularExpression:
        self._skip_whitespace()
        if self.position >= len(self.source):
            self._raise("Se esperaba un símbolo o una expresión entre paréntesis")

        character = self.source[self.position]
        self.position += 1
        if character == "(":
            expression = self._parse_union()
            if not self._consume(")"):
                self._raise("Falta cerrar el paréntesis")
            return expression
        if character == "\\":
            if self.position >= len(self.source):
                self._raise("La barra inversa debe preceder un símbolo")
            escaped = self.source[self.position]
            self.position += 1
            if escaped in {"λ", "ε", "ϵ"}:
                self._raise("La aplicación reserva λ y ε para la cadena vacía")
            return Symbol(escaped)
        if character in ")|∪*+":
            self._raise(f"El operador '{character}' no tiene operando")
        if character in {"λ", "ε", "ϵ"}:
            return LAMBDA
        if character == "∅":
            return EMPTY_SET
        return Symbol(character)

    def _consume(self, token: str) -> bool:
        self._skip_whitespace()
        if self.source.startswith(token, self.position):
            self.position += len(token)
            return True
        return False

    def _skip_whitespace(self) -> None:
        while (
            self.position < len(self.source)
            and self.source[self.position].isspace()
        ):
            self.position += 1

    def _raise(self, message: str) -> None:
        raise RegularExpressionSyntaxError(
            f"{message} en la posición {self.position + 1}."
        )


class _KleenePartOneBuilder:
    """Build epsilon-NFA fragments inductively from regular-expression syntax."""

    def __init__(self) -> None:
        self.transitions: list[tuple[int, str | None, int]] = []
        self.state_count = 0

    def build(self, expression: RegularExpression) -> _Fragment:
        if expression == EMPTY_SET:
            return _Fragment(self._new_state(), ())
        if expression == LAMBDA:
            state = self._new_state()
            return _Fragment(state, (state,))
        if isinstance(expression, Symbol):
            start, accept = self._new_state(), self._new_state()
            self.transitions.append((start, expression.value, accept))
            return _Fragment(start, (accept,))
        if isinstance(expression, UnionExpression):
            start = self._new_state()
            accepting: list[int] = []
            for alternative in expression.alternatives:
                fragment = self.build(alternative)
                self._add_epsilon(start, fragment.start)
                accepting.extend(fragment.accepting)
            return _Fragment(start, tuple(accepting))
        if isinstance(expression, Concatenation):
            fragments = [self.build(factor) for factor in expression.factors]
            for left, right in zip(fragments, fragments[1:]):
                for accepting_state in left.accepting:
                    self._add_epsilon(accepting_state, right.start)
            return _Fragment(fragments[0].start, fragments[-1].accepting)
        if isinstance(expression, KleeneStar):
            if isinstance(expression.operand, Symbol):
                state = self._new_state()
                self.transitions.append(
                    (state, expression.operand.value, state)
                )
                return _Fragment(state, (state,))

            fragment = self.build(expression.operand)
            for accepting_state in fragment.accepting:
                self._add_epsilon(accepting_state, fragment.start)
            return _Fragment(
                fragment.start,
                (fragment.start, *fragment.accepting),
            )
        if isinstance(expression, KleenePlus):
            fragment = self.build(expression.operand)
            for accepting_state in fragment.accepting:
                self._add_epsilon(accepting_state, fragment.start)
            return fragment
        raise TypeError(
            f"Unsupported regular-expression node: {type(expression).__name__}"
        )

    def _new_state(self) -> int:
        state = self.state_count
        self.state_count += 1
        return state

    def _add_epsilon(self, source: int, target: int) -> None:
        self.transitions.append((source, None, target))


def parse_regular_expression(source: str) -> RegularExpression:
    """Parse a regular expression using single-character alphabet symbols."""
    if not isinstance(source, str):
        raise TypeError("parse_regular_expression requires a string")
    if not source.strip():
        raise RegularExpressionSyntaxError("Ingresa una expresión regular.")
    return _Parser(source).parse()


def regular_expression_to_nfa(source: str) -> EpsilonNFA:
    """Build an AFN-λ by the inductive first part of Kleene's theorem.

    Union adds a new initial state with lambda branches. Concatenation joins
    accepting states to the following fragment, and repetition adds lambda
    cycles. Final states are retained per branch rather than merged.
    """
    expression = parse_regular_expression(source)
    builder = _KleenePartOneBuilder()
    fragment = builder.build(expression)
    alphabet = sorted(
        {
            symbol
            for _, symbol, _ in builder.transitions
            if symbol is not None
        }
    )
    nfa = EpsilonNFA(alphabet)

    positions = _layout_states(builder, fragment.start)
    accepting_states = set(fragment.accepting)
    for state in range(builder.state_count):
        nfa.add_state(
            f"q{state}",
            is_initial=state == fragment.start,
            is_accepting=state in accepting_states,
            x=positions[state][0],
            y=positions[state][1],
        )

    for source, symbol, target in builder.transitions:
        nfa.add_transition(
            f"q{source}",
            f"q{target}",
            "λ" if symbol is None else symbol,
        )

    return nfa


def _layout_states(
    builder: _KleenePartOneBuilder,
    initial_state: int,
) -> tuple[tuple[float, float], ...]:
    adjacency: list[list[int]] = [[] for _ in range(builder.state_count)]
    for transition in builder.transitions:
        adjacency[transition[0]].append(transition[2])

    depths: dict[int, int] = {initial_state: 0}
    pending = [initial_state]
    while pending:
        source = pending.pop(0)
        for target in adjacency[source]:
            if target in depths:
                continue
            depths[target] = depths[source] + 1
            pending.append(target)

    levels: dict[int, list[int]] = {}
    for state in range(builder.state_count):
        levels.setdefault(depths.get(state, 0), []).append(state)

    positions: list[tuple[float, float]] = [(0.0, 0.0)] * builder.state_count
    for depth, states in levels.items():
        center_y = 320.0
        spacing_y = 160.0
        first_y = center_y - (len(states) - 1) * spacing_y / 2.0
        for index, state in enumerate(states):
            positions[state] = (
                180.0 + depth * 190.0,
                first_y + index * spacing_y,
            )
    return tuple(positions)
