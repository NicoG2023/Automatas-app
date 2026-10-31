from app_automatas.services.regular_expression import (
    LAMBDA,
    Symbol,
    Variable,
    concatenate,
    plus,
    star,
    union,
)
from app_automatas.services.regular_expression_presentation import (
    equation_to_html,
    expression_to_html,
    variable_to_html,
)


def test_math_html_uses_subscripts_and_superscripts() -> None:
    ab = concatenate(Symbol("a"), Symbol("b"))
    expression = concatenate(
        Symbol("b"),
        star(union(Symbol("b"), concatenate(ab, plus(ab)))),
        union(plus(ab), Symbol("a")),
    )

    rendered = expression_to_html(expression)

    assert "<sup>*</sup>" in rendered
    assert "<sup>+</sup>" in rendered
    assert "&cup;" in rendered


def test_variable_html_renders_course_subscript() -> None:
    assert variable_to_html(Variable("A3")) == "<i>A</i><sub>3</sub>"
    assert variable_to_html(Variable("A[start]")) == "<i>A</i><sub>start</sub>"


def test_equation_html_preserves_lambda() -> None:
    assert equation_to_html(Variable("A2"), LAMBDA) == (
        "<i>A</i><sub>2</sub> = λ"
    )
