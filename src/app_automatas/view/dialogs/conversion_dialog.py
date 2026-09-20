"""Independent view for an AFD generated from an AFN."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.view.canvas.automaton_scene import AutomatonScene
from app_automatas.view.canvas.automaton_view import AutomatonView
from app_automatas.view.dialogs.conversion_process_dialog import ConversionProcessDialog


class ConversionDialog(QDialog):
    """Show a generated DFA without replacing the source NFA editor."""

    def __init__(
        self,
        automaton: DFA,
        theme_mode: str,
        parent: QWidget | None = None,
        source_nfa: NFA | None = None,
    ) -> None:
        super().__init__(parent)
        self.generated_automaton = automaton
        self.source_nfa = source_nfa
        self._theme_mode = theme_mode
        self.process_dialog: ConversionProcessDialog | None = None
        self.setObjectName("conversionDialog")
        self.setWindowTitle("AFD generado desde AFN")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMinimumSize(980, 560)
        self.resize(1280, 720)

        self.scene = AutomatonScene()
        self.scene.set_theme(theme_mode)
        self.scene.set_editor_tool("select")
        self.canvas = AutomatonView(self.scene)
        self.canvas.set_editor_tool("select")
        self.scene.state_position_changed.connect(self._on_state_moved)
        self.scene.rebuild_automaton(automaton.states, automaton.transitions)
        self.canvas.enable_zoom_mode(auto_fit=True)

        self.transition_table = self._build_transition_table()
        table_panel = self._build_table_panel()

        title = QLabel("AFD generado por construcción de subconjuntos")
        title.setObjectName("conversionTitle")
        help_text = QLabel(
            "El AFN original permanece intacto. Puedes arrastrar los estados para reorganizar este AFD."
        )
        help_text.setObjectName("secondaryText")
        help_text.setWordWrap(True)

        alphabet = ", ".join(sorted(automaton.alphabet)) or "Vacío"
        alphabet_label = QLabel(f"Alfabeto: {{{alphabet}}}")
        alphabet_label.setObjectName("secondaryText")

        self.process_button = QPushButton("Ver Proceso")
        self.process_button.setObjectName("conversionProcessButton")
        self.process_button.setToolTip(
            "Ver paso a paso la tabla, expansión de conjuntos, renombrado, dibujo y análisis de alcanzabilidad."
        )
        self.process_button.setEnabled(source_nfa is not None)
        self.process_button.clicked.connect(self._show_process)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.process_button)
        header.addWidget(alphabet_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("conversionSplitter")
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.canvas)
        splitter.addWidget(table_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([880, 360])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addLayout(header)
        layout.addWidget(help_text)
        layout.addWidget(splitter, 1)

    def set_theme(self, theme_mode: str) -> None:
        """Refresh generated canvas items when the application theme changes."""
        self._theme_mode = theme_mode
        self.scene.set_theme(theme_mode)
        if self.process_dialog is not None:
            self.process_dialog.set_theme(theme_mode)

    def _show_process(self) -> None:
        if self.source_nfa is None:
            return
        if self.process_dialog is not None:
            self.process_dialog.raise_()
            self.process_dialog.activateWindow()
            return
        dialog = ConversionProcessDialog(self.source_nfa, self._theme_mode, self)
        self.process_dialog = dialog
        dialog.finished.connect(self._clear_process_dialog)
        dialog.show()

    def _clear_process_dialog(self, _result: int) -> None:
        self.process_dialog = None

    def _build_table_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("conversionTablePanel")
        panel.setMinimumWidth(320)

        title = QLabel("Tabla de transiciones")
        title.setObjectName("conversionTableTitle")
        legend = QLabel("→ inicial   ·   * aceptación   ·   — sin transición")
        legend.setObjectName("secondaryText")
        legend.setWordWrap(True)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addWidget(legend)
        layout.addWidget(self.transition_table, 1)
        return panel

    def _build_transition_table(self) -> QTableWidget:
        symbols = tuple(sorted(self.generated_automaton.alphabet))
        states = self.generated_automaton.states

        table = QTableWidget(len(states), len(symbols) + 1)
        table.setObjectName("conversionTransitionTable")
        table.setHorizontalHeaderLabels(("Estado", *symbols))
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setHighlightSections(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for column in range(1, len(symbols) + 1):
            table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)

        for row, state in enumerate(states):
            state_item = QTableWidgetItem(self._render_state_label(state.identifier))
            state_item.setTextAlignment(
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
            )
            table.setItem(row, 0, state_item)

            for column, symbol in enumerate(symbols, start=1):
                destinations = sorted(
                    self.generated_automaton.destinations(state.identifier, symbol)
                )
                destination = destinations[0] if destinations else "—"
                item = QTableWidgetItem(destination)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, column, item)

        table.resizeRowsToContents()
        return table

    def _render_state_label(self, identifier: str) -> str:
        state = self.generated_automaton.get_state(identifier)
        markers: list[str] = []
        if state.is_initial:
            markers.append("→")
        if state.is_accepting:
            markers.append("*")
        prefix = "".join(markers)
        return f"{prefix} {identifier}" if prefix else identifier

    def _on_state_moved(self, identifier: str, x: float, y: float) -> None:
        self.generated_automaton.get_state(identifier).set_position(x, y)
