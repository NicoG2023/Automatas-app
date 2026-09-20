import pytest

from app_automatas.model.dfa import DFA
from app_automatas.model.editor_session import EditorSession
from app_automatas.model.nfa import NFA


def test_editor_session_defaults_to_dfa_light_theme_and_select_tool() -> None:
    session = EditorSession()

    assert session.automaton_type == "AFD"
    assert session.theme_mode == "light"
    assert session.editor_tool == "select"
    assert isinstance(session.automaton, DFA)


def test_editor_session_accepts_nfa() -> None:
    session = EditorSession()

    session.set_automaton_type("AFN")

    assert session.automaton_type == "AFN"
    assert isinstance(session.automaton, NFA)


def test_editor_session_rejects_unknown_type() -> None:
    session = EditorSession()

    with pytest.raises(ValueError, match="Unsupported automaton type"):
        session.set_automaton_type("PDA")


def test_editor_session_does_not_discard_non_empty_automaton_when_switching_type() -> None:
    session = EditorSession()
    session.automaton.add_state()

    with pytest.raises(ValueError, match="document is not empty"):
        session.set_automaton_type("AFN")

    assert session.automaton_type == "AFD"
    assert isinstance(session.automaton, DFA)
    assert len(session.automaton.states) == 1


def test_editor_session_accepts_dark_theme() -> None:
    session = EditorSession()

    session.set_theme_mode("dark")

    assert session.theme_mode == "dark"


def test_editor_session_rejects_unknown_theme() -> None:
    session = EditorSession()

    with pytest.raises(ValueError, match="Unsupported theme"):
        session.set_theme_mode("system")


def test_editor_session_accepts_state_tool() -> None:
    session = EditorSession()

    session.set_editor_tool("state")

    assert session.editor_tool == "state"


def test_editor_session_rejects_unknown_tool() -> None:
    session = EditorSession()

    with pytest.raises(ValueError, match="Unsupported editor tool"):
        session.set_editor_tool("transition")
