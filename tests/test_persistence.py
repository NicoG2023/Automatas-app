import json

import pytest

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import EpsilonNFA, NFA
from app_automatas.services.persistence import (
    PersistenceError,
    automaton_from_dict,
    automaton_to_dict,
    load_automaton,
    save_automaton,
)


def test_dfa_round_trip_preserves_complete_document(tmp_path) -> None:
    automaton = DFA({"0", "1"})
    automaton.add_state("q0", is_initial=True, x=120.5, y=240.25)
    automaton.add_state("q1", is_accepting=True, x=480, y=240)
    automaton.add_transition("q0", "q1", "0")
    automaton.add_transition("q0", "q1", "1")
    automaton.add_transition("q1", "q1", "1")

    destination = save_automaton(tmp_path / "documento", automaton)
    loaded = load_automaton(destination)

    assert destination.name == "documento.json"
    assert isinstance(loaded, DFA)
    assert loaded.alphabet == frozenset({"0", "1"})
    assert [(s.identifier, s.is_initial, s.is_accepting, s.x, s.y) for s in loaded.states] == [
        ("q0", True, False, 120.5, 240.25),
        ("q1", False, True, 480.0, 240.0),
    ]
    assert loaded.get_transition("q0", "q1").symbols == {"0", "1"}
    assert loaded.get_transition("q1", "q1").symbols == {"1"}


def test_nfa_round_trip_preserves_branching_transitions(tmp_path) -> None:
    automaton = NFA({"a"})
    automaton.add_state("inicio", is_initial=True)
    automaton.add_state("izquierda", is_accepting=True)
    automaton.add_state("derecha")
    automaton.add_transition("inicio", "izquierda", "a")
    automaton.add_transition("inicio", "derecha", "a")

    loaded = load_automaton(save_automaton(tmp_path / "nfa.json", automaton))

    assert isinstance(loaded, NFA)
    assert loaded.destinations("inicio", "a") == frozenset({"izquierda", "derecha"})


def test_epsilon_nfa_round_trip_preserves_lambda_transitions(tmp_path) -> None:
    automaton = EpsilonNFA({"a"})
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1", is_accepting=True)
    automaton.add_transition("q0", "q1", "λ")

    loaded = load_automaton(save_automaton(tmp_path / "epsilon.json", automaton))

    assert isinstance(loaded, EpsilonNFA)
    assert loaded.get_transition("q0", "q1").symbols == {"λ"}


def test_serialized_document_is_human_readable_and_versioned() -> None:
    automaton = DFA({"a"})
    automaton.add_state("q0", is_initial=True)

    payload = automaton_to_dict(automaton)

    assert payload["format"] == "app-automatas"
    assert payload["version"] == 1
    assert payload["automaton_type"] == "AFD"
    assert payload["states"][0]["id"] == "q0"


def test_loaded_automatic_state_ids_continue_without_collision(tmp_path) -> None:
    automaton = DFA()
    automaton.add_state("q0")
    automaton.add_state("q1")
    loaded = load_automaton(save_automaton(tmp_path / "ids.json", automaton))

    assert loaded.add_state().identifier == "q2"


@pytest.mark.parametrize(
    "payload, message",
    [
        ([], "objeto JSON"),
        ({"format": "otro", "version": 1}, "no pertenece"),
        ({"format": "app-automatas", "version": 99}, "no compatible"),
        (
            {
                "format": "app-automatas",
                "version": 1,
                "automaton_type": "PDA",
                "alphabet": [],
                "states": [],
                "transitions": [],
            },
            "AFD, AFN o AFN-λ",
        ),
    ],
)
def test_invalid_document_metadata_is_rejected(payload, message) -> None:
    with pytest.raises(PersistenceError, match=message):
        automaton_from_dict(payload)


def test_invalid_transition_reference_is_rejected() -> None:
    payload = {
        "format": "app-automatas",
        "version": 1,
        "automaton_type": "AFD",
        "alphabet": ["a"],
        "states": [
            {"id": "q0", "is_initial": True, "is_accepting": False, "x": 0, "y": 0}
        ],
        "transitions": [{"source": "q0", "target": "q9", "symbols": ["a"]}],
    }

    with pytest.raises(PersistenceError, match="datos inválidos"):
        automaton_from_dict(payload)


def test_multiple_initial_states_are_rejected() -> None:
    payload = {
        "format": "app-automatas",
        "version": 1,
        "automaton_type": "AFN",
        "alphabet": [],
        "states": [
            {"id": "q0", "is_initial": True, "is_accepting": False, "x": 0, "y": 0},
            {"id": "q1", "is_initial": True, "is_accepting": False, "x": 1, "y": 1},
        ],
        "transitions": [],
    }

    with pytest.raises(PersistenceError, match="más de un estado inicial"):
        automaton_from_dict(payload)


def test_malformed_json_reports_friendly_error(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"format": ', encoding="utf-8")

    with pytest.raises(PersistenceError, match="JSON válido"):
        load_automaton(path)


def test_epsilon_in_saved_alphabet_is_rejected() -> None:
    payload = {
        "format": "app-automatas",
        "version": 1,
        "automaton_type": "AFN",
        "alphabet": ["ε"],
        "states": [],
        "transitions": [],
    }

    with pytest.raises(PersistenceError, match="datos inválidos"):
        automaton_from_dict(payload)


def test_json_written_to_disk_contains_expected_transition_shape(tmp_path) -> None:
    automaton = DFA({"a", "b"})
    automaton.add_state("q0", is_initial=True)
    automaton.add_state("q1")
    automaton.add_transition("q0", "q1", "a")
    automaton.add_transition("q0", "q1", "b")

    path = save_automaton(tmp_path / "shape.json", automaton)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["transitions"] == [
        {"source": "q0", "target": "q1", "symbols": ["a", "b"]}
    ]
