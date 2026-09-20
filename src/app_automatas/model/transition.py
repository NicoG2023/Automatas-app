"""Finite automaton transition model."""

from __future__ import annotations

from dataclasses import dataclass, field

from app_automatas.model.state import State


@dataclass(slots=True)
class Transition:
    """Represent one directed edge and the symbols grouped on that edge."""

    source: State
    target: State
    symbols: set[str] = field(default_factory=set)

    def add_symbol(self, symbol: str) -> None:
        self.symbols.add(symbol)

    def remove_symbol(self, symbol: str) -> None:
        self.symbols.discard(symbol)

    def accepts(self, symbol: str) -> bool:
        return symbol in self.symbols
