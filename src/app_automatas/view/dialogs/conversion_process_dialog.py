"""Step-by-step pedagogical visualization of NFA-to-DFA conversion."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app_automatas.model.dfa import DFA
from app_automatas.model.nfa import NFA
from app_automatas.services.nfa_to_dfa_process import (
    ConversionProcess,
    TransitionRow,
    build_conversion_process,
    render_subset,
)
from app_automatas.view.canvas.automaton_scene import AutomatonScene
from app_automatas.view.canvas.automaton_view import AutomatonView


class ConversionProcessDialog(QDialog):
    """Walk through the same five conversion stages used in class notes."""

    def __init__(
        self,
        source_nfa: NFA,
        theme_mode: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("conversionProcessDialog")
        self.setWindowTitle("Proceso de conversión AFN → AFD")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMinimumSize(980, 620)
        self.resize(1220, 760)
        self._theme_mode = theme_mode
        self.process: ConversionProcess = build_conversion_process(source_nfa)

        self.step_title = QLabel()
        self.step_title.setObjectName("conversionProcessTitle")
        self.step_description = QLabel()
        self.step_description.setObjectName("secondaryText")
        self.step_description.setWordWrap(True)

        self.pages = QStackedWidget()
        self.pages.setObjectName("conversionProcessPages")
        self.pages.addWidget(self._build_step_one())
        self.pages.addWidget(self._build_step_two())
        self.pages.addWidget(self._build_step_three())
        self.pages.addWidget(self._build_step_four())
        self.pages.addWidget(self._build_step_five())

        self.previous_button = QPushButton("Anterior")
        self.previous_button.clicked.connect(self.previous_step)
        self.next_button = QPushButton("Siguiente")
        self.next_button.setObjectName("conversionProcessPrimaryButton")
        self.next_button.clicked.connect(self.next_step)
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.close)
        self.step_counter = QLabel()
        self.step_counter.setObjectName("secondaryText")

        navigation = QHBoxLayout()
        navigation.addWidget(self.step_counter)
        navigation.addStretch(1)
        navigation.addWidget(self.previous_button)
        navigation.addWidget(self.next_button)
        navigation.addWidget(self.close_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addWidget(self.step_title)
        layout.addWidget(self.step_description)
        layout.addWidget(self.pages, 1)
        layout.addLayout(navigation)

        self._sync_step_header()

    @property
    def current_step(self) -> int:
        """Return the one-based step number currently displayed."""
        return self.pages.currentIndex() + 1

    def next_step(self) -> None:
        if self.pages.currentIndex() < self.pages.count() - 1:
            self.pages.setCurrentIndex(self.pages.currentIndex() + 1)
            self._sync_step_header()

    def previous_step(self) -> None:
        if self.pages.currentIndex() > 0:
            self.pages.setCurrentIndex(self.pages.currentIndex() - 1)
            self._sync_step_header()

    def set_theme(self, theme_mode: str) -> None:
        self._theme_mode = theme_mode
        self.complete_scene.set_theme(theme_mode)
        self.final_scene.set_theme(theme_mode)

    def _sync_step_header(self) -> None:
        index = self.pages.currentIndex()
        titles = (
            "1. Obtener la tabla de transiciones del AFN",
            "2. Identificar y expandir los conjuntos",
            "3. Cambiar los nombres a k₀, k₁, …",
            "4. Dibujar el AFD completo",
            "5. Analizar el AFD y obtener el AFD final",
        )
        descriptions = (
            "Se parte de una fila por cada estado original del AFN y se calcula su destino para cada símbolo.",
            "Cada conjunto no vacío que aparezca como destino se convierte en una nueva fila. Se repite hasta que no aparezcan conjuntos nuevos.",
            "Cada fila de la tabla se reemplaza por un nombre determinista k0, k1, … para construir el AFD con etiquetas simples.",
            "Se dibuja literalmente el AFD que describe la tabla renombrada, antes de eliminar estados o ramas. En este punto aparecen todos los estados k de la tabla.",
            "Se parte del estado inicial, se determinan los estados alcanzables y se eliminan los estados inaccesibles junto con sus transiciones. El dibujo resultante es el AFD final.",
        )
        self.step_title.setText(titles[index])
        self.step_description.setText(descriptions[index])
        self.step_counter.setText(f"Paso {index + 1} de {self.pages.count()}")
        self.previous_button.setEnabled(index > 0)
        self.next_button.setEnabled(index < self.pages.count() - 1)

    def _build_step_one(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        table = self._build_subset_table(
            self.process.original_rows,
            state_header="Δ",
            object_name="conversionProcessOriginalTable",
        )
        self._add_centered_table(layout, table)
        return page

    def _build_step_two(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        added = len(self.process.expanded_rows) - len(self.process.original_rows)
        note = QLabel(
            f"Se agregaron {added} conjunto(s) nuevo(s) como filas de la tabla."
            if added
            else "No fue necesario agregar conjuntos nuevos."
        )
        note.setObjectName("secondaryText")
        layout.addWidget(note)
        table = self._build_subset_table(
            self.process.expanded_rows,
            state_header="Δ",
            object_name="conversionProcessExpandedTable",
        )
        self._add_centered_table(layout, table)
        return page

    def _build_step_three(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)

        mapping = QLabel(
            "   ·   ".join(
                f"{render_subset(subset)} → {name}"
                for subset, name in self.process.names
            )
        )
        mapping.setObjectName("conversionMappingText")
        mapping.setWordWrap(True)
        layout.addWidget(mapping)
        table = self._build_renamed_table()
        self._add_centered_table(layout, table)
        return page

    def _build_step_four(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)

        note = QLabel(
            "Se dibujan todos los estados y transiciones de la tabla renombrada. "
            "Todavía no se elimina ningún estado, aunque después resulte inaccesible."
        )
        note.setObjectName("secondaryText")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.complete_scene, complete_canvas = self._build_dfa_canvas(
            self.process.complete_dfa
        )
        complete_canvas.setObjectName("conversionCompleteDfaCanvas")
        layout.addWidget(complete_canvas, 1)
        return page

    def _build_step_five(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)

        reachable = ", ".join(self.process.reachable_names)
        if self.process.unreachable_names:
            removed = ", ".join(self.process.unreachable_names)
            note_text = (
                f"Estados alcanzables desde el estado inicial: {reachable}.  "
                f"Estados inaccesibles: {removed}.  "
                "Se eliminan esos estados y todas las transiciones conectadas exclusivamente a ellos."
            )
        else:
            note_text = (
                f"Estados alcanzables desde el estado inicial: {reachable}.  "
                "No hay estados inaccesibles, así que el AFD final coincide con el AFD completo."
            )

        note = QLabel(note_text)
        note.setObjectName("conversionReachabilityNote")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.final_scene, final_canvas = self._build_dfa_canvas(
            self.process.reachable_dfa
        )
        final_canvas.setObjectName("conversionFinalDfaCanvas")
        layout.addWidget(final_canvas, 1)
        return page

    def _build_subset_table(
        self,
        rows: tuple[TransitionRow, ...],
        *,
        state_header: str,
        object_name: str,
    ) -> QTableWidget:
        table = self._new_table(len(rows), object_name)
        table.setHorizontalHeaderLabels((state_header, *self.process.symbols))
        original_count = len(self.process.original_rows)
        initial_subset = self.process.original_rows[0][0]

        for row_index, (subset, cells) in enumerate(rows):
            label = render_subset(subset)
            markers = self._subset_markers(subset, initial_subset)
            if markers:
                label = f"{markers} {label}"
            item = QTableWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if row_index >= original_count:
                item.setData(Qt.ItemDataRole.UserRole, "generated")
            table.setItem(row_index, 0, item)
            for column, (_symbol, destination) in enumerate(cells, start=1):
                cell = QTableWidgetItem(render_subset(destination))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_index, column, cell)

        self._configure_table_headers(table)
        return table

    def _build_renamed_table(self) -> QTableWidget:
        rows = self.process.expanded_rows
        table = self._new_table(len(rows), "conversionProcessRenamedTable")
        table.setHorizontalHeaderLabels(("Δ", *self.process.symbols))
        name_map = self.process.name_map
        initial_subset = self.process.original_rows[0][0]

        for row_index, (subset, cells) in enumerate(rows):
            name = name_map[subset]
            markers = self._subset_markers(subset, initial_subset)
            label = f"{markers} {name}" if markers else name
            state_item = QTableWidgetItem(label)
            state_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_index, 0, state_item)
            for column, (_symbol, destination) in enumerate(cells, start=1):
                target = "∅" if not destination else name_map[destination]
                cell = QTableWidgetItem(target)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_index, column, cell)

        self._configure_table_headers(table)
        return table

    def _new_table(self, rows: int, object_name: str) -> QTableWidget:
        table = QTableWidget(rows, len(self.process.symbols) + 1)
        table.setObjectName(object_name)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setAlternatingRowColors(False)
        table.setSizeAdjustPolicy(QAbstractItemView.SizeAdjustPolicy.AdjustToContents)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setHighlightSections(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.setCornerButtonEnabled(False)
        return table

    def _configure_table_headers(self, table: QTableWidget) -> None:
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        for column in range(1, table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        table.horizontalHeader().setMinimumSectionSize(110)
        table.horizontalHeader().setFixedHeight(58)
        table.resizeColumnsToContents()

        for column in range(table.columnCount()):
            minimum = 132 if column == 0 else 150
            table.setColumnWidth(column, max(minimum, table.columnWidth(column)))

        table.verticalHeader().setDefaultSectionSize(58)
        for row in range(table.rowCount()):
            table.setRowHeight(row, 58)

        width = table.frameWidth() * 2 + sum(
            table.columnWidth(column) for column in range(table.columnCount())
        )
        height = table.frameWidth() * 2 + table.horizontalHeader().height() + sum(
            table.rowHeight(row) for row in range(table.rowCount())
        )
        table.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        table.setFixedSize(width + 2, height + 2)

    def _add_centered_table(self, layout: QVBoxLayout, table: QTableWidget) -> None:
        layout.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(table, 0, Qt.AlignmentFlag.AlignCenter)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(1)

    def _subset_markers(self, subset: frozenset[str], initial_subset: frozenset[str]) -> str:
        markers = "→" if subset == initial_subset else ""
        name = self.process.name_map[subset]
        if self.process.complete_dfa.get_state(name).is_accepting:
            markers += "*"
        return markers

    def _build_dfa_canvas(self, automaton: DFA) -> tuple[AutomatonScene, AutomatonView]:
        scene = AutomatonScene()
        scene.set_theme(self._theme_mode)
        scene.set_editor_tool("select")
        canvas = AutomatonView(scene)
        canvas.set_editor_tool("select")
        scene.rebuild_automaton(automaton.states, automaton.transitions)
        canvas.enable_zoom_mode(auto_fit=True)
        scene.state_position_changed.connect(
            lambda identifier, x, y, current=automaton: current.get_state(identifier).set_position(x, y)
        )
        return scene, canvas
