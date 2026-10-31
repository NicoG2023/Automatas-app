"""Rich-text presentation helpers for regular-expression equations."""

from __future__ import annotations

import html
import re

from app_automatas.services.regular_expression import (
    Concatenation,
    EmptySet,
    KleenePlus,
    KleeneStar,
    Lambda,
    RegularExpression,
    Symbol,
    UnionExpression,
    Variable,
)


def expression_to_html(expression: RegularExpression) -> str:
    """Render an expression as Qt-compatible rich text with math typography."""
    return _expression_html(expression, 0)


def variable_to_html(variable: Variable | str) -> str:
    """Render A0/A[name] variables with a mathematical subscript."""
    name = variable.name if isinstance(variable, Variable) else variable
    numeric = re.fullmatch(r"A(\d+)", name)
    if numeric is not None:
        return f"<i>A</i><sub>{html.escape(numeric.group(1))}</sub>"

    custom = re.fullmatch(r"A\[(.+)]", name)
    if custom is not None:
        return f"<i>A</i><sub>{html.escape(custom.group(1))}</sub>"

    return f"<i>{html.escape(name)}</i>"


def equation_to_html(variable: Variable, expression: RegularExpression) -> str:
    return f"{variable_to_html(variable)} = {expression_to_html(expression)}"


def arden_identification_to_html(
    coefficient: RegularExpression,
    variable: Variable,
    remainder: RegularExpression,
) -> str:
    return (
        f"<i>A</i> = {expression_to_html(coefficient)}, &nbsp; "
        f"<i>X</i> = {variable_to_html(variable)}, &nbsp; "
        f"<i>B</i> = {expression_to_html(remainder)}"
    )


def _expression_html(expression: RegularExpression, parent_precedence: int) -> str:
    precedence = expression.precedence

    if isinstance(expression, EmptySet):
        body = "∅"
    elif isinstance(expression, Lambda):
        body = "λ"
    elif isinstance(expression, Symbol):
        body = f"<i>{html.escape(expression.value)}</i>"
    elif isinstance(expression, Variable):
        body = variable_to_html(expression)
    elif isinstance(expression, UnionExpression):
        body = " &cup; ".join(
            _expression_html(item, precedence) for item in expression.alternatives
        )
    elif isinstance(expression, Concatenation):
        body = "".join(_expression_html(item, precedence) for item in expression.factors)
    elif isinstance(expression, KleeneStar):
        body = f"{_expression_html(expression.operand, precedence)}<sup>*</sup>"
    elif isinstance(expression, KleenePlus):
        body = f"{_expression_html(expression.operand, precedence)}<sup>+</sup>"
    else:  # pragma: no cover - every AST node is handled above
        raise TypeError(
            f"Unsupported regular-expression node: {type(expression).__name__}"
        )

    if precedence < parent_precedence:
        return f"({body})"
    return body
