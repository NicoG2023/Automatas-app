"""Side panel with the initial automaton configuration controls."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLabel, QVBoxLayout, QWidget


class EditorSidebar(QWidget):
    """Provide controls that configure the current automaton document."""

    automaton_type_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("editorSidebar")
        self.setMinimumWidth(220)
        self.setMaximumWidth(300)

        self.automaton_type_combo = QComboBox()
        self.automaton_type_combo.addItems(["AFD", "AFN"])
        self.automaton_type_combo.currentTextChanged.connect(
            self.automaton_type_changed.emit
        )

        automaton_group = QGroupBox("Autómata")
        automaton_form = QFormLayout(automaton_group)
        automaton_form.addRow("Tipo:", self.automaton_type_combo)

        help_label = QLabel(
            "Selecciona el tipo de autómata. El lienzo central será el área de construcción."
        )
        help_label.setObjectName("secondaryText")
        help_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        layout.addWidget(automaton_group)
        layout.addWidget(help_label)
        layout.addStretch(1)

    def set_automaton_type(self, automaton_type: str) -> None:
        """Select an automaton type without emitting a user-change signal."""
        previous_state = self.automaton_type_combo.blockSignals(True)
        self.automaton_type_combo.setCurrentText(automaton_type)
        self.automaton_type_combo.blockSignals(previous_state)
