"""Finite automaton state model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class State:
    """Represent one state independently from its graphical item."""

    identifier: str
    is_initial: bool = False
    is_accepting: bool = False
    x: float = 0.0
    y: float = 0.0

    def set_position(self, x: float, y: float) -> None:
        """Store the editor position without depending on Qt classes."""
        self.x = float(x)
        self.y = float(y)
