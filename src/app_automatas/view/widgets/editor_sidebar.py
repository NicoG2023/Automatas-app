"""Side panel with automaton configuration and selection editors."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app_automatas.model.state import State
from app_automatas.model.transition import Transition


class EditorSidebar(QWidget):
    """Provide controls that configure the current automaton document."""

    automaton_type_changed = Signal(str)
    alphabet_changed = Signal(object)
    state_initial_changed = Signal(str, bool)
    state_accepting_changed = Signal(str, bool)
    state_rename_requested = Signal(str, str)
    state_delete_requested = Signal(str)
    transition_symbols_changed = Signal(str, str, object)
    transition_delete_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("editorSidebar")
        self.setMinimumWidth(280)
        self.setMaximumWidth(360)
        self._selected_state_id: str | None = None
        self._selected_transition: tuple[str, str] | None = None

        self.automaton_type_combo = QComboBox()
        self.automaton_type_combo.addItems(["AFD", "AFN", "AFN-λ"])
        self.automaton_type_combo.currentTextChanged.connect(
            self.automaton_type_changed.emit
        )

        automaton_group = QGroupBox("Autómata")
        automaton_form = QFormLayout(automaton_group)
        automaton_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        automaton_form.setLabelAlignment(
            automaton_form.labelAlignment()
        )
        automaton_form.setContentsMargins(16, 22, 16, 16)
        automaton_form.setHorizontalSpacing(12)
        automaton_form.setVerticalSpacing(12)
        automaton_form.addRow("Tipo:", self.automaton_type_combo)

        alphabet_group = QGroupBox("Alfabeto")
        alphabet_layout = QVBoxLayout(alphabet_group)
        alphabet_layout.setContentsMargins(16, 22, 16, 16)
        alphabet_layout.setSpacing(10)
        self.alphabet_input = QLineEdit()
        self.alphabet_input.setPlaceholderText("Ej.: a, b, 0, 1")
        self.alphabet_input.setToolTip("Separa los símbolos con comas")
        self.apply_alphabet_button = QPushButton("Aplicar alfabeto")
        self.apply_alphabet_button.clicked.connect(self._emit_alphabet)
        self.alphabet_input.returnPressed.connect(self._emit_alphabet)
        alphabet_layout.addWidget(self.alphabet_input)
        alphabet_layout.addWidget(self.apply_alphabet_button)

        state_group = QGroupBox("Estado seleccionado")
        state_layout = QVBoxLayout(state_group)
        state_layout.setContentsMargins(16, 22, 16, 16)
        state_layout.setSpacing(10)
        self.selected_state_label = QLabel("Ninguno")
        self.selected_state_label.setObjectName("selectedStateName")

        self.state_name_input = QLineEdit()
        self.state_name_input.setPlaceholderText("Nombre del estado")
        self.rename_state_button = QPushButton("Renombrar")
        self.rename_state_button.clicked.connect(self._emit_state_rename)
        self.state_name_input.returnPressed.connect(self._emit_state_rename)

        self.initial_checkbox = QCheckBox("Estado inicial")
        self.accepting_checkbox = QCheckBox("Estado de aceptación")
        self.initial_checkbox.toggled.connect(self._on_initial_toggled)
        self.accepting_checkbox.toggled.connect(self._on_accepting_toggled)
        self.delete_state_button = QPushButton("Eliminar estado")
        self.delete_state_button.clicked.connect(self._emit_state_delete)

        state_layout.addWidget(self.selected_state_label)
        state_layout.addWidget(self.state_name_input)
        state_layout.addWidget(self.rename_state_button)
        state_layout.addWidget(self.initial_checkbox)
        state_layout.addWidget(self.accepting_checkbox)
        state_layout.addWidget(self.delete_state_button)

        transition_group = QGroupBox("Transición seleccionada")
        transition_layout = QVBoxLayout(transition_group)
        transition_layout.setContentsMargins(16, 22, 16, 16)
        transition_layout.setSpacing(10)
        self.selected_transition_label = QLabel("Ninguna")
        self.selected_transition_label.setObjectName("selectedTransitionName")
        self.transition_symbols_input = QLineEdit()
        self.transition_symbols_input.setPlaceholderText("Símbolos: a, b")
        self.transition_symbols_input.setToolTip("Separa los símbolos con comas")
        self.apply_transition_button = QPushButton("Aplicar símbolos")
        self.delete_transition_button = QPushButton("Eliminar transición")
        self.apply_transition_button.clicked.connect(self._emit_transition_symbols)
        self.transition_symbols_input.returnPressed.connect(
            self._emit_transition_symbols
        )
        self.delete_transition_button.clicked.connect(self._emit_transition_delete)
        transition_layout.addWidget(self.selected_transition_label)
        transition_layout.addWidget(self.transition_symbols_input)
        transition_layout.addWidget(self.apply_transition_button)
        transition_layout.addWidget(self.delete_transition_button)

        help_label = QLabel(
            "Selecciona un estado o una transición para editarla. Las transiciones "
            "también pueden crearse con la herramienta Transición."
        )
        help_label.setObjectName("secondaryText")
        help_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)
        layout.addWidget(automaton_group)
        layout.addWidget(alphabet_group)
        layout.addWidget(state_group)
        layout.addWidget(transition_group)
        layout.addWidget(help_label)
        layout.addStretch(1)

        self.show_state(None)
        self.show_transition(None)

    def set_automaton_type(self, automaton_type: str) -> None:
        """Select an automaton type without emitting a user-change signal."""
        previous_state = self.automaton_type_combo.blockSignals(True)
        self.automaton_type_combo.setCurrentText(automaton_type)
        self.automaton_type_combo.blockSignals(previous_state)

    def set_alphabet(self, symbols: frozenset[str] | set[str]) -> None:
        """Render the model alphabet without triggering another update."""
        self.alphabet_input.setText(", ".join(sorted(symbols)))

    def show_state(self, state: State | None) -> None:
        """Display editable properties for the selected state."""
        self._selected_state_id = state.identifier if state is not None else None
        self.selected_state_label.setText(
            state.identifier if state is not None else "Ninguno"
        )
        self.state_name_input.setText(state.identifier if state is not None else "")
        self._set_checkbox_value(
            self.initial_checkbox,
            state.is_initial if state else False,
        )
        self._set_checkbox_value(
            self.accepting_checkbox,
            state.is_accepting if state else False,
        )
        enabled = state is not None
        self.state_name_input.setEnabled(enabled)
        self.rename_state_button.setEnabled(enabled)
        self.initial_checkbox.setEnabled(enabled)
        self.accepting_checkbox.setEnabled(enabled)
        self.delete_state_button.setEnabled(enabled)

    def show_transition(self, transition: Transition | None) -> None:
        """Display editable symbols for the selected transition."""
        if transition is None:
            self._selected_transition = None
            self.selected_transition_label.setText("Ninguna")
            self.transition_symbols_input.clear()
        else:
            source_id = transition.source.identifier
            target_id = transition.target.identifier
            self._selected_transition = (source_id, target_id)
            self.selected_transition_label.setText(f"{source_id} → {target_id}")
            self.transition_symbols_input.setText(", ".join(sorted(transition.symbols)))

        enabled = transition is not None
        self.transition_symbols_input.setEnabled(enabled)
        self.apply_transition_button.setEnabled(enabled)
        self.delete_transition_button.setEnabled(enabled)

    def _emit_alphabet(self) -> None:
        self.alphabet_changed.emit(self._parse_symbols(self.alphabet_input.text()))

    def _emit_state_rename(self) -> None:
        if self._selected_state_id is None:
            return
        self.state_rename_requested.emit(
            self._selected_state_id,
            self.state_name_input.text().strip(),
        )

    def _emit_state_delete(self) -> None:
        if self._selected_state_id is not None:
            self.state_delete_requested.emit(self._selected_state_id)

    def _emit_transition_symbols(self) -> None:
        if self._selected_transition is None:
            return
        source_id, target_id = self._selected_transition
        self.transition_symbols_changed.emit(
            source_id,
            target_id,
            self._parse_symbols(self.transition_symbols_input.text()),
        )

    def _emit_transition_delete(self) -> None:
        if self._selected_transition is None:
            return
        source_id, target_id = self._selected_transition
        self.transition_delete_requested.emit(source_id, target_id)

    def _on_initial_toggled(self, checked: bool) -> None:
        if self._selected_state_id is not None:
            self.state_initial_changed.emit(self._selected_state_id, checked)

    def _on_accepting_toggled(self, checked: bool) -> None:
        if self._selected_state_id is not None:
            self.state_accepting_changed.emit(self._selected_state_id, checked)

    @staticmethod
    def _parse_symbols(text: str) -> list[str]:
        return [token.strip() for token in text.split(",") if token.strip()]

    @staticmethod
    def _set_checkbox_value(checkbox: QCheckBox, checked: bool) -> None:
        previous_state = checkbox.blockSignals(True)
        checkbox.setChecked(checked)
        checkbox.blockSignals(previous_state)
