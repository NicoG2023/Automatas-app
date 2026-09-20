"""Minimal editor session used by the application bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

AutomatonType = Literal["AFD", "AFN"]
ThemeMode = Literal["light", "dark"]
SUPPORTED_AUTOMATON_TYPES: tuple[AutomatonType, ...] = ("AFD", "AFN")
SUPPORTED_THEMES: tuple[ThemeMode, ...] = ("light", "dark")


@dataclass(slots=True)
class EditorSession:
    """State shared by the editor while the automaton model is introduced."""

    automaton_type: AutomatonType = "AFD"
    theme_mode: ThemeMode = "light"

    def set_automaton_type(self, automaton_type: str) -> None:
        """Update the selected automaton type after validating it."""
        if automaton_type not in SUPPORTED_AUTOMATON_TYPES:
            raise ValueError(f"Unsupported automaton type: {automaton_type}")
        self.automaton_type = cast(AutomatonType, automaton_type)

    def set_theme_mode(self, theme_mode: str) -> None:
        """Update the selected visual theme after validating it."""
        if theme_mode not in SUPPORTED_THEMES:
            raise ValueError(f"Unsupported theme: {theme_mode}")
        self.theme_mode = cast(ThemeMode, theme_mode)
