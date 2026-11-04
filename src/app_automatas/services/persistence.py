"""JSON persistence for finite automata documents."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from app_automatas.model.automaton import Automaton
from app_automatas.model.exceptions import AutomatonError
from app_automatas.model.factory import create_automaton

FORMAT_NAME = "app-automatas"
FORMAT_VERSION = 1


class PersistenceError(ValueError):
    """Raised when an automaton document cannot be read or written safely."""


def automaton_to_dict(automaton: Automaton) -> dict[str, Any]:
    """Serialize one automaton to a stable, human-readable JSON structure."""
    return {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "automaton_type": automaton.automaton_type,
        "alphabet": sorted(automaton.alphabet),
        "states": [
            {
                "id": state.identifier,
                "is_initial": state.is_initial,
                "is_accepting": state.is_accepting,
                "x": state.x,
                "y": state.y,
            }
            for state in automaton.states
        ],
        "transitions": [
            {
                "source": transition.source.identifier,
                "target": transition.target.identifier,
                "symbols": sorted(transition.symbols),
            }
            for transition in automaton.transitions
        ],
    }


def automaton_from_dict(payload: object) -> Automaton:
    """Build a validated domain automaton from one decoded JSON document."""
    if not isinstance(payload, dict):
        raise PersistenceError("El archivo debe contener un objeto JSON.")

    if payload.get("format") != FORMAT_NAME:
        raise PersistenceError("El archivo no pertenece a App de Autómatas.")
    if payload.get("version") != FORMAT_VERSION:
        raise PersistenceError(
            f"Versión de archivo no compatible: {payload.get('version')!r}."
        )

    automaton_type = payload.get("automaton_type")
    if automaton_type not in {"AFD", "AFN", "AFN-λ"}:
        raise PersistenceError("El tipo de autómata debe ser AFD, AFN o AFN-λ.")

    alphabet = _string_list(payload.get("alphabet"), "alphabet")
    states = payload.get("states")
    transitions = payload.get("transitions")
    if not isinstance(states, list):
        raise PersistenceError("El campo states debe ser una lista.")
    if not isinstance(transitions, list):
        raise PersistenceError("El campo transitions debe ser una lista.")

    automaton = create_automaton(automaton_type)
    try:
        automaton.set_alphabet(alphabet)
        initial_count = 0
        for index, raw_state in enumerate(states):
            if not isinstance(raw_state, dict):
                raise PersistenceError(f"El estado #{index + 1} no es válido.")
            identifier = _required_string(raw_state, "id", f"estado #{index + 1}")
            is_initial = _required_bool(raw_state, "is_initial", identifier)
            is_accepting = _required_bool(raw_state, "is_accepting", identifier)
            x = _required_number(raw_state, "x", identifier)
            y = _required_number(raw_state, "y", identifier)
            initial_count += int(is_initial)
            if initial_count > 1:
                raise PersistenceError("El archivo contiene más de un estado inicial.")
            automaton.add_state(
                identifier,
                is_initial=is_initial,
                is_accepting=is_accepting,
                x=x,
                y=y,
            )

        for index, raw_transition in enumerate(transitions):
            if not isinstance(raw_transition, dict):
                raise PersistenceError(f"La transición #{index + 1} no es válida.")
            source = _required_string(raw_transition, "source", f"transición #{index + 1}")
            target = _required_string(raw_transition, "target", f"transición #{index + 1}")
            symbols = _string_list(raw_transition.get("symbols"), "symbols")
            if not symbols:
                raise PersistenceError("Una transición debe contener al menos un símbolo.")
            for symbol in symbols:
                automaton.add_transition(source, target, symbol)
    except PersistenceError:
        raise
    except (AutomatonError, TypeError, ValueError) as exc:
        raise PersistenceError(f"El archivo contiene datos inválidos: {exc}") from exc

    return automaton


def save_automaton(path: str | Path, automaton: Automaton) -> Path:
    """Write an automaton document atomically enough for a desktop project."""
    destination = Path(path)
    if destination.suffix.lower() != ".json":
        destination = destination.with_suffix(".json")
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(
            json.dumps(automaton_to_dict(automaton), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise PersistenceError(f"No se pudo guardar el archivo: {exc}") from exc
    return destination


def load_automaton(path: str | Path) -> Automaton:
    """Read and validate one saved automaton document."""
    source = Path(path)
    try:
        raw = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise PersistenceError(f"No se pudo abrir el archivo: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PersistenceError(
            f"El archivo no contiene JSON válido (línea {exc.lineno}, columna {exc.colno})."
        ) from exc
    return automaton_from_dict(payload)


def _required_string(payload: dict[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PersistenceError(f"{context}: {key} debe ser texto no vacío.")
    return value.strip()


def _required_bool(payload: dict[str, Any], key: str, context: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise PersistenceError(f"{context}: {key} debe ser booleano.")
    return value


def _required_number(payload: dict[str, Any], key: str, context: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PersistenceError(f"{context}: {key} debe ser numérico.")
    number = float(value)
    if not math.isfinite(number):
        raise PersistenceError(f"{context}: {key} debe ser un número finito.")
    return number


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PersistenceError(f"El campo {field} debe ser una lista de textos.")
    return value
