"""Controls and status display for step-by-step automaton simulation."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app_automatas.services.simulation import (
    DFASimulationSnapshot,
    NFASimulationSnapshot,
)

SimulationSnapshot = DFASimulationSnapshot | NFASimulationSnapshot


class SimulationPanel(QWidget):
    """Present input, playback controls and the current automaton simulation state."""

    start_requested = Signal(str)
    next_requested = Signal()
    play_requested = Signal()
    pause_requested = Signal()
    reset_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("simulationPanel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._available = True
        self._automaton_type = "AFD"

        title = QLabel("Simulación")
        title.setObjectName("simulationTitle")
        self.result_label = QLabel("Sin iniciar")
        self.result_label.setObjectName("simulationResult")
        self.result_label.setProperty("simulationStatus", "idle")

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.result_label)

        self.input_edit = QLineEdit()
        self.input_edit.setObjectName("simulationInput")
        self.input_edit.setPlaceholderText("Cadena a probar (vacía permitida)")
        self.input_edit.setToolTip(
            "Escribe una cadena usando únicamente símbolos del alfabeto. "
            "Déjala vacía para probar una cadena vacía de entrada."
        )
        self.start_button = QPushButton("Iniciar")
        self.start_button.setObjectName("simulationPrimaryButton")
        self.start_button.clicked.connect(self._emit_start)
        self.input_edit.returnPressed.connect(self._emit_start)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        input_row.addWidget(QLabel("Cadena:"))
        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(self.start_button)

        self.next_button = QPushButton("Siguiente paso")
        self.play_button = QPushButton("Reproducir")
        self.pause_button = QPushButton("Pausar")
        self.reset_button = QPushButton("Reiniciar")
        self.next_button.clicked.connect(self.next_requested.emit)
        self.play_button.clicked.connect(self.play_requested.emit)
        self.pause_button.clicked.connect(self.pause_requested.emit)
        self.reset_button.clicked.connect(self.reset_requested.emit)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        controls.addWidget(self.next_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.reset_button)
        controls.addStretch(1)

        self.state_caption = QLabel("Estado actual:")
        self.transition_caption = QLabel("Transición:")
        self.state_value = self._value_label("—")
        self.symbol_value = self._value_label("—")
        self.transition_value = self._value_label("—")
        self.processed_value = self._value_label("Vacía")
        self.remaining_value = self._value_label("Vacía")
        self.reason_value = self._value_label("—")
        self.reason_value.setWordWrap(True)

        details = QGridLayout()
        details.setHorizontalSpacing(12)
        details.setVerticalSpacing(7)
        details.addWidget(self.state_caption, 0, 0)
        details.addWidget(self.state_value, 0, 1)
        details.addWidget(QLabel("Símbolo:"), 0, 2)
        details.addWidget(self.symbol_value, 0, 3)
        details.addWidget(self.transition_caption, 0, 4)
        details.addWidget(self.transition_value, 0, 5)
        details.addWidget(QLabel("Procesado:"), 1, 0)
        details.addWidget(self.processed_value, 1, 1, 1, 2)
        details.addWidget(QLabel("Restante:"), 1, 3)
        details.addWidget(self.remaining_value, 1, 4, 1, 2)
        details.addWidget(QLabel("Detalle:"), 2, 0)
        details.addWidget(self.reason_value, 2, 1, 1, 5)
        details.setColumnStretch(1, 1)
        details.setColumnStretch(2, 0)
        details.setColumnStretch(3, 1)
        details.setColumnStretch(4, 0)
        details.setColumnStretch(5, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(10)
        layout.addLayout(header)
        layout.addLayout(input_row)
        layout.addLayout(controls)
        layout.addLayout(details)

        self.set_idle()

    @staticmethod
    def _value_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("simulationValue")
        label.setTextInteractionFlags(label.textInteractionFlags())
        return label

    def _emit_start(self) -> None:
        self.start_requested.emit(self.input_edit.text())

    def set_automaton_type(self, automaton_type: str) -> None:
        """Adapt captions while keeping simulation available for DFA and NFA."""
        if automaton_type not in {"AFD", "AFN"}:
            raise ValueError(f"Unsupported automaton type: {automaton_type}")
        self._automaton_type = automaton_type
        self._available = True
        if automaton_type == "AFN":
            self.state_caption.setText("Estados activos:")
            self.transition_caption.setText("Transiciones:")
        else:
            self.state_caption.setText("Estado actual:")
            self.transition_caption.setText("Transición:")
        self.set_idle()

    def set_available(self, available: bool) -> None:
        """Compatibility helper retained for older callers."""
        self._available = available
        self.set_idle() if available else self.set_idle("No disponible")

    def set_idle(self, message: str = "Sin iniciar") -> None:
        self._set_result(message, "idle")
        self.input_edit.setEnabled(self._available)
        self.start_button.setEnabled(self._available)
        self.state_value.setText("—")
        self.symbol_value.setText("—")
        self.transition_value.setText("—")
        self.processed_value.setText("Vacía")
        self.remaining_value.setText("Vacía")
        self.reason_value.setText("—")
        self.next_button.setEnabled(False)
        self.play_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.reset_button.setEnabled(False)

    def show_snapshot(
        self,
        snapshot: SimulationSnapshot,
        *,
        playing: bool = False,
    ) -> None:
        """Render one immutable DFA or NFA simulator snapshot."""
        statuses = {
            "ready": ("Lista", "ready"),
            "running": ("En curso", "running"),
            "accepted": ("Aceptada", "accepted"),
            "rejected": ("Rechazada", "rejected"),
        }
        result_text, result_status = statuses[snapshot.status]
        self._set_result(result_text, result_status)
        self.symbol_value.setText(snapshot.last_symbol or snapshot.next_symbol or "—")
        self.processed_value.setText(self._render_input_fragment(snapshot.processed_input))
        self.remaining_value.setText(self._render_input_fragment(snapshot.remaining_input))
        self.reason_value.setText(snapshot.rejection_reason or "—")

        if isinstance(snapshot, DFASimulationSnapshot):
            self.state_caption.setText("Estado actual:")
            self.transition_caption.setText("Transición:")
            self.state_value.setText(snapshot.current_state_id)
            if snapshot.last_transition is None:
                self.transition_value.setText("—")
            else:
                source_id, target_id = snapshot.last_transition
                self.transition_value.setText(f"{source_id} → {target_id}")
        else:
            self.state_caption.setText("Estados activos:")
            self.transition_caption.setText("Transiciones:")
            self.state_value.setText(self._render_states(snapshot.active_state_ids))
            self.transition_value.setText(
                self._render_transitions(snapshot.last_transitions)
            )

        active = not snapshot.is_finished
        self.next_button.setEnabled(active and not playing)
        self.play_button.setEnabled(active and not playing)
        self.pause_button.setEnabled(active and playing)
        self.reset_button.setEnabled(True)
        self.input_edit.setEnabled(self._available and not playing)
        self.start_button.setEnabled(self._available and not playing)

    def set_playing(self, playing: bool, snapshot: SimulationSnapshot) -> None:
        self.show_snapshot(snapshot, playing=playing)

    @staticmethod
    def _render_input_fragment(text: str) -> str:
        return text if text else "Vacía"

    @staticmethod
    def _render_states(state_ids: frozenset[str]) -> str:
        if not state_ids:
            return "Ninguno"
        return "{" + ", ".join(sorted(state_ids)) + "}"

    @staticmethod
    def _render_transitions(transitions: tuple[tuple[str, str], ...]) -> str:
        if not transitions:
            return "—"
        return "; ".join(f"{source} → {target}" for source, target in transitions)

    def _set_result(self, text: str, status: str) -> None:
        self.result_label.setText(text)
        self.result_label.setProperty("simulationStatus", status)
        style = self.result_label.style()
        style.unpolish(self.result_label)
        style.polish(self.result_label)
        self.result_label.update()
