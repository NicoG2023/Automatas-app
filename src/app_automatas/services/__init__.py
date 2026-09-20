"""Application services that are independent from the graphical interface."""

from app_automatas.services.nfa_to_dfa import NFAConversionError, convert_nfa_to_dfa
from app_automatas.services.persistence import (
    PersistenceError,
    automaton_from_dict,
    automaton_to_dict,
    load_automaton,
    save_automaton,
)
from app_automatas.services.nfa_to_dfa_process import (
    ConversionProcess,
    build_conversion_process,
    render_subset,
)
from app_automatas.services.simulation import (
    DFASimulationSnapshot,
    DFASimulator,
    NFASimulationSnapshot,
    NFASimulator,
    InvalidSimulationAutomatonError,
    InvalidSimulationInputError,
    SimulationError,
)
from app_automatas.services.validation import (
    AutomatonValidationResult,
    ValidationIssue,
    validate_automaton,
)

__all__ = [
    "AutomatonValidationResult",
    "ConversionProcess",
    "DFASimulationSnapshot",
    "DFASimulator",
    "NFASimulationSnapshot",
    "NFASimulator",
    "InvalidSimulationAutomatonError",
    "InvalidSimulationInputError",
    "NFAConversionError",
    "PersistenceError",
    "SimulationError",
    "ValidationIssue",
    "automaton_from_dict",
    "automaton_to_dict",
    "build_conversion_process",
    "convert_nfa_to_dfa",
    "load_automaton",
    "render_subset",
    "save_automaton",
    "validate_automaton",
]
