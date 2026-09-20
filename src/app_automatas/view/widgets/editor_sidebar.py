"""Side panel with automaton configuration and state properties."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app_automatas.model.state import State


class EditorSidebar(QWidget):
    """Provide controls that configure the current automaton document."""

    automaton_type_changed = Signal(str)
    state_initial_changed = Signal(str, bool)
    state_accepting_changed = Signal(str, bool)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("editorSidebar")
        self.setMinimumWidth(220)
        self.setMaximumWidth(300)
        self._selected_state_id: str | None = None

        self.automaton_type_combo = QComboBox()
        self.automaton_type_combo.addItems(["AFD", "AFN"])
        self.automaton_type_combo.currentTextChanged.connect(
            self.automaton_type_changed.emit
        )

        automaton_group = QGroupBox("Autómata")
        automaton_form = QFormLayout(automaton_group)
        automaton_form.addRow("Tipo:", self.automaton_type_combo)

        state_group = QGroupBox("Estado seleccionado")
        state_layout = QVBoxLayout(state_group)
        self.selected_state_label = QLabel("Ninguno")
        self.selected_state_label.setObjectName("selectedStateName")
        self.initial_checkbox = QCheckBox("Estado inicial")
        self.accepting_checkbox = QCheckBox("Estado de aceptación")
        self.initial_checkbox.setEnabled(False)
        self.accepting_checkbox.setEnabled(False)
        self.initial_checkbox.toggled.connect(self._on_initial_toggled)
        self.accepting_checkbox.toggled.connect(self._on_accepting_toggled)
        state_layout.addWidget(self.selected_state_label)
        state_layout.addWidget(self.initial_checkbox)
        state_layout.addWidget(self.accepting_checkbox)

        help_label = QLabel(
            "Usa Estado para crear nodos en el lienzo y Seleccionar para moverlos o editar "
            "sus propiedades."
        )
        help_label.setObjectName("secondaryText")
        help_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        layout.addWidget(automaton_group)
        layout.addWidget(state_group)
        layout.addWidget(help_label)
        layout.addStretch(1)

    def set_automaton_type(self, automaton_type: str) -> None:
        """Select an automaton type without emitting a user-change signal."""
        previous_state = self.automaton_type_combo.blockSignals(True)
        self.automaton_type_combo.setCurrentText(automaton_type)
        self.automaton_type_combo.blockSignals(previous_state)

    def show_state(self, state: State | None) -> None:
        """Display editable properties for the selected state."""
        self._selected_state_id = state.identifier if state is not None else None
        self.selected_state_label.setText(
            state.identifier if state is not None else "Ninguno"
        )
        self._set_checkbox_value(self.initial_checkbox, state.is_initial if state else False)
        self._set_checkbox_value(
            self.accepting_checkbox,
            state.is_accepting if state else False,
        )
        enabled = state is not None
        self.initial_checkbox.setEnabled(enabled)
        self.accepting_checkbox.setEnabled(enabled)

    def _on_initial_toggled(self, checked: bool) -> None:
        if self._selected_state_id is not None:
            self.state_initial_changed.emit(self._selected_state_id, checked)

    def _on_accepting_toggled(self, checked: bool) -> None:
        if self._selected_state_id is not None:
            self.state_accepting_changed.emit(self._selected_state_id, checked)

    @staticmethod
    def _set_checkbox_value(checkbox: QCheckBox, checked: bool) -> None:
        previous_state = checkbox.blockSignals(True)
        checkbox.setChecked(checked)
        checkbox.blockSignals(previous_state)
