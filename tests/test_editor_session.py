import pytest

from app_automatas.model.editor_session import EditorSession


def test_editor_session_defaults_to_dfa_and_light_theme() -> None:
    session = EditorSession()

    assert session.automaton_type == "AFD"
    assert session.theme_mode == "light"


def test_editor_session_accepts_nfa() -> None:
    session = EditorSession()

    session.set_automaton_type("AFN")

    assert session.automaton_type == "AFN"


def test_editor_session_rejects_unknown_type() -> None:
    session = EditorSession()

    with pytest.raises(ValueError, match="Unsupported automaton type"):
        session.set_automaton_type("PDA")


def test_editor_session_accepts_dark_theme() -> None:
    session = EditorSession()

    session.set_theme_mode("dark")

    assert session.theme_mode == "dark"


def test_editor_session_rejects_unknown_theme() -> None:
    session = EditorSession()

    with pytest.raises(ValueError, match="Unsupported theme"):
        session.set_theme_mode("system")
