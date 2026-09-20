"""Editor session containing UI preferences and the current automaton."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, cast

from app_automatas.model.automaton import Automaton
from app_automatas.model.factory import create_automaton

AutomatonType = Literal["AFD", "AFN"]
ThemeMode = Literal["light", "dark"]
EditorTool = Literal["select", "state"]
SUPPORTED_AUTOMATON_TYPES: tuple[AutomatonType, ...] = ("AFD", "AFN")
SUPPORTED_THEMES: tuple[ThemeMode, ...] = ("light", "dark")
SUPPORTED_EDITOR_TOOLS: tuple[EditorTool, ...] = ("select", "state")


@dataclass(slots=True)
class EditorSession:
    """State shared by the editor independently from the Qt widgets."""

    automaton_type: AutomatonType = "AFD"
    theme_mode: ThemeMode = "light"
    editor_tool: EditorTool = "select"
    automaton: Automaton = field(init=False)

    def __post_init__(self) -> None:
        self.automaton = create_automaton(self.automaton_type)

    def set_automaton_type(self, automaton_type: str) -> None:
        """Switch the concrete automaton while the current document is empty."""
        if automaton_type not in SUPPORTED_AUTOMATON_TYPES:
            raise ValueError(f"Unsupported automaton type: {automaton_type}")

        validated_type = cast(AutomatonType, automaton_type)
        if validated_type == self.automaton_type:
            return
        if not self.automaton.is_empty:
            raise ValueError("Cannot change automaton type while the document is not empty")

        self.automaton_type = validated_type
        self.automaton = create_automaton(validated_type)

    def set_theme_mode(self, theme_mode: str) -> None:
        """Update the selected visual theme after validating it."""
        if theme_mode not in SUPPORTED_THEMES:
            raise ValueError(f"Unsupported theme: {theme_mode}")
        self.theme_mode = cast(ThemeMode, theme_mode)

    def set_editor_tool(self, editor_tool: str) -> None:
        """Select the active canvas interaction tool."""
        if editor_tool not in SUPPORTED_EDITOR_TOOLS:
            raise ValueError(f"Unsupported editor tool: {editor_tool}")
        self.editor_tool = cast(EditorTool, editor_tool)
