import pytest

from app_automatas.services.regular_expression import (
    EMPTY_SET,
    LAMBDA,
    Concatenation,
    KleenePlus,
    KleeneStar,
    Symbol,
    UnionExpression,
    concatenate,
    plus,
    star,
    union,
)


def test_symbol_must_be_non_empty() -> None:
    with pytest.raises(ValueError, match="non-empty string"):
        Symbol("")


def test_union_flattens_deduplicates_and_discards_empty_set() -> None:
    a = Symbol("a")
    b = Symbol("b")

    expression = union(a, EMPTY_SET, union(b, a))

    assert expression == UnionExpression((a, b))
    assert expression.render() == "a ∪ b"


def test_empty_union_is_empty_set() -> None:
    assert union() == EMPTY_SET
    assert union(EMPTY_SET, EMPTY_SET) == EMPTY_SET


def test_concatenation_flattens_and_uses_lambda_as_identity() -> None:
    a = Symbol("a")
    b = Symbol("b")

    expression = concatenate(LAMBDA, a, concatenate(b, LAMBDA))

    assert expression == Concatenation((a, b))
    assert expression.render() == "ab"


def test_empty_set_annihilates_concatenation() -> None:
    assert concatenate(Symbol("a"), EMPTY_SET, Symbol("b")) == EMPTY_SET


def test_empty_concatenation_is_lambda() -> None:
    assert concatenate() == LAMBDA
    assert concatenate(LAMBDA, LAMBDA) == LAMBDA


def test_star_simplifies_empty_set_lambda_and_nested_star() -> None:
    a = Symbol("a")
    a_star = star(a)

    assert star(EMPTY_SET) == LAMBDA
    assert star(LAMBDA) == LAMBDA
    assert star(a_star) is a_star
    assert a_star == KleeneStar(a)


def test_renderer_uses_course_notation_and_minimal_parentheses() -> None:
    a = Symbol("a")
    b = Symbol("b")
    c = Symbol("c")

    expression = concatenate(a, star(union(b, c)))

    assert expression.render() == "a(b ∪ c)*"
    assert star(concatenate(a, b)).render() == "(ab)*"
    assert union(concatenate(a, b), c).render() == "ab ∪ c"


def test_concatenation_uses_plus_for_operand_adjacent_to_its_star() -> None:
    a = Symbol("a")
    b = Symbol("b")
    ab = concatenate(a, b)

    assert concatenate(ab, star(ab)) == KleenePlus(ab)
    assert concatenate(star(ab), ab) == KleenePlus(ab)
    assert concatenate(a, b, star(ab)).render() == "(ab)+"
    assert concatenate(star(ab), a, b).render() == "(ab)+"


def test_plus_simplifies_basic_cases() -> None:
    a = Symbol("a")

    assert plus(EMPTY_SET) == EMPTY_SET
    assert plus(LAMBDA) == LAMBDA
    assert plus(a) == KleenePlus(a)
    assert plus(star(a)) == star(a)
