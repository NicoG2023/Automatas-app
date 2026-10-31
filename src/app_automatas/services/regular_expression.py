"""Small immutable algebra for regular expressions used by conversion services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class RegularExpression(ABC):
    """Base type for a regular-expression syntax tree."""

    @property
    @abstractmethod
    def precedence(self) -> int:
        """Return the rendering precedence of this node."""

    @abstractmethod
    def _render(self, parent_precedence: int) -> str:
        """Render this node, adding parentheses only when required."""

    def render(self) -> str:
        """Render the expression using the notation used in the course material."""
        return self._render(0)

    def __str__(self) -> str:
        return self.render()


@dataclass(frozen=True, slots=True)
class EmptySet(RegularExpression):
    """The empty language, written as ∅."""

    @property
    def precedence(self) -> int:
        return 4

    def _render(self, parent_precedence: int) -> str:
        return "∅"


@dataclass(frozen=True, slots=True)
class Lambda(RegularExpression):
    """The language containing only the empty word, written as λ."""

    @property
    def precedence(self) -> int:
        return 4

    def _render(self, parent_precedence: int) -> str:
        return "λ"


@dataclass(frozen=True, slots=True)
class Symbol(RegularExpression):
    """A literal alphabet symbol."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise ValueError("A regular-expression symbol must be a non-empty string")

    @property
    def precedence(self) -> int:
        return 4

    def _render(self, parent_precedence: int) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Variable(RegularExpression):
    """A symbolic equation variable used while solving automata equations."""

    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("A regular-expression variable must have a non-empty name")

    @property
    def precedence(self) -> int:
        return 4

    def _render(self, parent_precedence: int) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class UnionExpression(RegularExpression):
    """A union of two or more alternatives."""

    alternatives: tuple[RegularExpression, ...]

    @property
    def precedence(self) -> int:
        return 1

    def _render(self, parent_precedence: int) -> str:
        body = " ∪ ".join(
            alternative._render(self.precedence)
            for alternative in self.alternatives
        )
        return _parenthesize_if_needed(body, self.precedence, parent_precedence)


@dataclass(frozen=True, slots=True)
class Concatenation(RegularExpression):
    """A concatenation of two or more factors."""

    factors: tuple[RegularExpression, ...]

    @property
    def precedence(self) -> int:
        return 2

    def _render(self, parent_precedence: int) -> str:
        body = "".join(factor._render(self.precedence) for factor in self.factors)
        return _parenthesize_if_needed(body, self.precedence, parent_precedence)


@dataclass(frozen=True, slots=True)
class KleeneStar(RegularExpression):
    """Zero-or-more repetition of one regular expression."""

    operand: RegularExpression

    @property
    def precedence(self) -> int:
        return 3

    def _render(self, parent_precedence: int) -> str:
        body = f"{self.operand._render(self.precedence)}*"
        return _parenthesize_if_needed(body, self.precedence, parent_precedence)


@dataclass(frozen=True, slots=True)
class KleenePlus(RegularExpression):
    """One-or-more repetition, used to mirror the notation from CC3."""

    operand: RegularExpression

    @property
    def precedence(self) -> int:
        return 3

    def _render(self, parent_precedence: int) -> str:
        body = f"{self.operand._render(self.precedence)}+"
        return _parenthesize_if_needed(body, self.precedence, parent_precedence)


EMPTY_SET = EmptySet()
LAMBDA = Lambda()


def union(*expressions: RegularExpression) -> RegularExpression:
    """Build a simplified union while preserving first-seen alternative order."""
    flattened: list[RegularExpression] = []
    seen: set[RegularExpression] = set()

    for expression in expressions:
        candidates = (
            expression.alternatives
            if isinstance(expression, UnionExpression)
            else (expression,)
        )
        for candidate in candidates:
            if candidate == EMPTY_SET or candidate in seen:
                continue
            seen.add(candidate)
            flattened.append(candidate)

    if not flattened:
        return EMPTY_SET
    if len(flattened) == 1:
        return flattened[0]
    return UnionExpression(tuple(flattened))


def concatenate(*expressions: RegularExpression) -> RegularExpression:
    """Build a simplified concatenation."""
    flattened: list[RegularExpression] = []

    for expression in expressions:
        if expression == EMPTY_SET:
            return EMPTY_SET
        candidates = (
            expression.factors
            if isinstance(expression, Concatenation)
            else (expression,)
        )
        for candidate in candidates:
            if candidate == EMPTY_SET:
                return EMPTY_SET
            if candidate == LAMBDA:
                continue
            flattened.append(candidate)

    flattened = _compress_star_with_adjacent_operand(flattened)

    if not flattened:
        return LAMBDA
    if len(flattened) == 1:
        return flattened[0]
    return Concatenation(tuple(flattened))


def star(expression: RegularExpression) -> RegularExpression:
    """Build a simplified Kleene star."""
    if expression == EMPTY_SET or expression == LAMBDA:
        return LAMBDA
    if isinstance(expression, KleeneStar):
        return expression
    if isinstance(expression, KleenePlus):
        return KleeneStar(expression.operand)
    return KleeneStar(expression)


def plus(expression: RegularExpression) -> RegularExpression:
    """Build a simplified one-or-more repetition."""
    if expression == EMPTY_SET:
        return EMPTY_SET
    if expression == LAMBDA:
        return LAMBDA
    if isinstance(expression, KleenePlus):
        return expression
    if isinstance(expression, KleeneStar):
        return expression
    return KleenePlus(expression)


def _compress_star_with_adjacent_operand(
    factors: list[RegularExpression],
) -> list[RegularExpression]:
    """Rewrite RR* and R*R as R+ without changing the represented language."""
    result = list(factors)
    changed = True

    while changed:
        changed = False
        for index, factor in enumerate(result):
            if not isinstance(factor, KleeneStar):
                continue

            operand_factors = (
                factor.operand.factors
                if isinstance(factor.operand, Concatenation)
                else (factor.operand,)
            )
            width = len(operand_factors)

            if index >= width and tuple(result[index - width:index]) == operand_factors:
                result[index - width:index + 1] = [plus(factor.operand)]
                changed = True
                break

            if tuple(result[index + 1:index + 1 + width]) == operand_factors:
                result[index:index + 1 + width] = [plus(factor.operand)]
                changed = True
                break

    return result


def contains_variable(expression: RegularExpression, variable: Variable) -> bool:
    """Return whether a variable occurs anywhere inside an expression tree."""
    if expression == variable:
        return True
    if isinstance(expression, UnionExpression):
        return any(
            contains_variable(alternative, variable)
            for alternative in expression.alternatives
        )
    if isinstance(expression, Concatenation):
        return any(
            contains_variable(factor, variable) for factor in expression.factors
        )
    if isinstance(expression, (KleeneStar, KleenePlus)):
        return contains_variable(expression.operand, variable)
    return False


def variables_in_expression(expression: RegularExpression) -> frozenset[Variable]:
    """Return every equation variable occurring in an expression tree."""
    if isinstance(expression, Variable):
        return frozenset((expression,))
    if isinstance(expression, UnionExpression):
        return frozenset().union(
            *(variables_in_expression(item) for item in expression.alternatives)
        )
    if isinstance(expression, Concatenation):
        return frozenset().union(
            *(variables_in_expression(item) for item in expression.factors)
        )
    if isinstance(expression, (KleeneStar, KleenePlus)):
        return variables_in_expression(expression.operand)
    return frozenset()


def substitute_variable(
    expression: RegularExpression,
    variable: Variable,
    replacement: RegularExpression,
) -> RegularExpression:
    """Replace one equation variable without recursively rewriting its replacement."""
    if expression == variable:
        return replacement
    if isinstance(expression, UnionExpression):
        return union(
            *(
                substitute_variable(alternative, variable, replacement)
                for alternative in expression.alternatives
            )
        )
    if isinstance(expression, Concatenation):
        return concatenate(
            *(
                substitute_variable(factor, variable, replacement)
                for factor in expression.factors
            )
        )
    if isinstance(expression, KleeneStar):
        return star(substitute_variable(expression.operand, variable, replacement))
    if isinstance(expression, KleenePlus):
        return plus(substitute_variable(expression.operand, variable, replacement))
    return expression


def nullable_status(expression: RegularExpression) -> bool | None:
    """Return whether an expression accepts λ, or ``None`` when unknown.

    Equation variables stand for languages that have not necessarily been solved
    yet, so their nullability is unknown.  Composite expressions can still have a
    definite answer when one of their operators determines it.
    """
    if expression == EMPTY_SET:
        return False
    if expression == LAMBDA:
        return True
    if isinstance(expression, Symbol):
        return False
    if isinstance(expression, Variable):
        return None
    if isinstance(expression, KleeneStar):
        return True
    if isinstance(expression, KleenePlus):
        return nullable_status(expression.operand)
    if isinstance(expression, UnionExpression):
        statuses = tuple(nullable_status(item) for item in expression.alternatives)
        if any(status is True for status in statuses):
            return True
        if all(status is False for status in statuses):
            return False
        return None
    if isinstance(expression, Concatenation):
        statuses = tuple(nullable_status(item) for item in expression.factors)
        if any(status is False for status in statuses):
            return False
        if all(status is True for status in statuses):
            return True
        return None
    raise TypeError(f"Unsupported regular-expression node: {type(expression).__name__}")


def distribute_concatenation(
    expression: RegularExpression,
) -> RegularExpression:
    """Expand concatenation over unions while preserving alternative order.

    For example, ``a(b ∪ c)`` becomes ``ab ∪ ac``.  This mirrors the
    algebraic expansion shown after substitutions in the course procedure.
    """
    if isinstance(expression, UnionExpression):
        return union(
            *(
                distribute_concatenation(alternative)
                for alternative in expression.alternatives
            )
        )

    if isinstance(expression, KleeneStar):
        return star(distribute_concatenation(expression.operand))

    if isinstance(expression, KleenePlus):
        return plus(distribute_concatenation(expression.operand))

    if not isinstance(expression, Concatenation):
        return expression

    expanded_factors = tuple(
        distribute_concatenation(factor) for factor in expression.factors
    )
    products: list[tuple[RegularExpression, ...]] = [()]

    for factor in expanded_factors:
        choices = (
            factor.alternatives
            if isinstance(factor, UnionExpression)
            else (factor,)
        )
        products = [
            (*product, choice)
            for product in products
            for choice in choices
        ]

    return union(*(concatenate(*product) for product in products))


def _parenthesize_if_needed(
    body: str,
    precedence: int,
    parent_precedence: int,
) -> str:
    if precedence < parent_precedence:
        return f"({body})"
    return body
