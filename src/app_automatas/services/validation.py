"""Validation rules used before running an automaton simulation."""

from __future__ import annotations

from dataclasses import dataclass

from app_automatas.model.automaton import Automaton, EPSILON_SYMBOLS


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Describe one user-facing structural problem in an automaton."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class AutomatonValidationResult:
    """Collect every blocking issue found during structural validation."""

    issues: tuple[ValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues

    @property
    def messages(self) -> tuple[str, ...]:
        return tuple(issue.message for issue in self.issues)


def validate_automaton(automaton: Automaton) -> AutomatonValidationResult:
    """Validate the structure required before a simulation can start.

    An incomplete DFA is intentionally valid here. Missing transitions are a
    runtime condition: if a symbol has no outgoing transition while simulating,
    the string is rejected rather than the automaton being considered malformed.
    """

    issues: list[ValidationIssue] = []

    if not automaton.states:
        issues.append(
            ValidationIssue(
                code="no_states",
                message="Crea al menos un estado antes de iniciar una simulación.",
            )
        )

    if automaton.initial_state is None:
        issues.append(
            ValidationIssue(
                code="no_initial_state",
                message="Selecciona un estado inicial.",
            )
        )

    known_states = {id(state) for state in automaton.states}
    deterministic_destinations: dict[tuple[int, str], int] = {}

    for transition in automaton.transitions:
        if id(transition.source) not in known_states or id(transition.target) not in known_states:
            issues.append(
                ValidationIssue(
                    code="unknown_transition_state",
                    message=(
                        "Existe una transición conectada a un estado que ya no pertenece "
                        "al autómata."
                    ),
                )
            )
            continue

        if not transition.symbols:
            issues.append(
                ValidationIssue(
                    code="transition_without_symbols",
                    message=(
                        f"La transición {transition.source.identifier} → "
                        f"{transition.target.identifier} no tiene símbolos asociados."
                    ),
                )
            )
            continue

        for symbol in sorted(transition.symbols):
            if symbol in EPSILON_SYMBOLS:
                issues.append(
                    ValidationIssue(
                        code="epsilon_transition",
                        message=(
                            f"La transición {transition.source.identifier} → "
                            f"{transition.target.identifier} usa ε, y esta app no admite "
                            "transiciones epsilon."
                        ),
                    )
                )
                continue

            if symbol not in automaton.alphabet:
                issues.append(
                    ValidationIssue(
                        code="symbol_outside_alphabet",
                        message=(
                            f"El símbolo '{symbol}' de la transición "
                            f"{transition.source.identifier} → {transition.target.identifier} "
                            "no pertenece al alfabeto."
                        ),
                    )
                )

            if automaton.automaton_type == "AFD":
                key = (id(transition.source), symbol)
                previous_target = deterministic_destinations.get(key)
                target_identity = id(transition.target)
                if previous_target is not None and previous_target != target_identity:
                    issues.append(
                        ValidationIssue(
                            code="nondeterministic_dfa",
                            message=(
                                f"El estado {transition.source.identifier} tiene más de una "
                                f"transición para el símbolo '{symbol}'."
                            ),
                        )
                    )
                else:
                    deterministic_destinations[key] = target_identity

    return AutomatonValidationResult(tuple(_deduplicate_issues(issues)))


def _deduplicate_issues(issues: list[ValidationIssue]) -> list[ValidationIssue]:
    """Keep validation output concise when defensive checks find duplicates."""

    unique: list[ValidationIssue] = []
    seen: set[tuple[str, str]] = set()
    for issue in issues:
        key = (issue.code, issue.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return unique
