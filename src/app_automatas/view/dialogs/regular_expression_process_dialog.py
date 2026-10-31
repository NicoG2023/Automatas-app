"""Step-by-step visualization of automaton-to-regular-expression conversion."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app_automatas.services.regular_equations import (
    ArdenApplicationStep,
    EquationSubstitutionStep,
    RegularEquationSolution,
)
from app_automatas.services.regular_expression_presentation import (
    arden_identification_to_html,
    equation_to_html,
    expression_to_html,
    variable_to_html,
)


def _normal_window_flags() -> Qt.WindowType:
    """Return flags that make the process dialogs behave as normal windows."""
    return (
        Qt.WindowType.Window
        | Qt.WindowType.WindowTitleHint
        | Qt.WindowType.WindowSystemMenuHint
        | Qt.WindowType.WindowMinimizeButtonHint
        | Qt.WindowType.WindowMaximizeButtonHint
        | Qt.WindowType.WindowCloseButtonHint
    )


class RegularExpressionProcessDialog(QDialog):
    """Walk through the equation method used to obtain a regular expression."""

    def __init__(
        self,
        solution: RegularEquationSolution,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent, _normal_window_flags())
        self.solution = solution
        self._summary_dialog: RegularExpressionSummaryDialog | None = None
        self.setObjectName("regularExpressionProcessDialog")
        self.setWindowTitle("Autómata → expresión regular")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMinimumSize(900, 580)
        self.resize(1080, 700)
        self.setSizeGripEnabled(True)

        self.step_title = QLabel()
        self.step_title.setObjectName("regularExpressionProcessTitle")
        self.step_description = QLabel()
        self.step_description.setObjectName("secondaryText")
        self.step_description.setWordWrap(True)

        self.pages = QStackedWidget()
        self.pages.setObjectName("regularExpressionProcessPages")
        self.pages.addWidget(self._build_initial_system_page())
        for step in solution.steps:
            if isinstance(step, EquationSubstitutionStep):
                self.pages.addWidget(self._build_substitution_page(step))
            elif isinstance(step, ArdenApplicationStep):
                self.pages.addWidget(self._build_arden_page(step))
            else:  # pragma: no cover - defensive guard for future step types
                raise TypeError(f"Unsupported equation process step: {type(step).__name__}")
        self.pages.addWidget(self._build_result_page())

        self.previous_button = QPushButton("Anterior")
        self.previous_button.clicked.connect(self.previous_step)
        self.next_button = QPushButton("Siguiente")
        self.next_button.setObjectName("regularExpressionProcessPrimaryButton")
        self.next_button.clicked.connect(self.next_step)
        self.summary_button = QPushButton("Ver resumen")
        self.summary_button.setObjectName("regularExpressionSummaryButton")
        self.summary_button.clicked.connect(self.show_summary)
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.close)
        self.step_counter = QLabel()
        self.step_counter.setObjectName("secondaryText")

        navigation = QHBoxLayout()
        navigation.addWidget(self.step_counter)
        navigation.addWidget(self.summary_button)
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
        """Return the one-based page currently displayed."""
        return self.pages.currentIndex() + 1

    def next_step(self) -> None:
        if self.pages.currentIndex() < self.pages.count() - 1:
            self.pages.setCurrentIndex(self.pages.currentIndex() + 1)
            self._sync_step_header()

    def previous_step(self) -> None:
        if self.pages.currentIndex() > 0:
            self.pages.setCurrentIndex(self.pages.currentIndex() - 1)
            self._sync_step_header()

    def show_summary(self) -> None:
        """Open one window containing the complete derivation."""
        if self._summary_dialog is None:
            self._summary_dialog = RegularExpressionSummaryDialog(self.solution, self)
            self._summary_dialog.finished.connect(self._clear_summary_dialog)
            self._summary_dialog.show()
        else:
            self._summary_dialog.showNormal()
            self._summary_dialog.raise_()
            self._summary_dialog.activateWindow()

    def _clear_summary_dialog(self, _result: int) -> None:
        self._summary_dialog = None

    def _sync_step_header(self) -> None:
        index = self.pages.currentIndex()
        last_index = self.pages.count() - 1

        if index == 0:
            title = "1. Construir el sistema inicial de ecuaciones"
            description = (
                "Cada estado se representa mediante una variable A. Las transiciones "
                "aportan términos aAj y los estados de aceptación agregan λ."
            )
        elif index == last_index:
            title = f"{index + 1}. Expresión regular equivalente"
            description = (
                "Al terminar las sustituciones y las aplicaciones del lema de Arden, "
                "la ecuación del estado inicial ya no contiene variables."
            )
        else:
            process_step = self.solution.steps[index - 1]
            if isinstance(process_step, EquationSubstitutionStep):
                source = process_step.source.variable.render()
                target = process_step.target_before.variable.render()
                title = f"{index + 1}. Reemplazar {source} en {target}"
                description = (
                    "Se sustituye la ecuación ya resuelta dentro de la ecuación que "
                    "todavía la contiene. Solo se distribuye cuando hace falta exponer "
                    "los términos recursivos para aplicar Arden."
                )
            else:
                variable = process_step.variable.render()
                title = f"{index + 1}. Aplicar el lema de Arden en {variable}"
                description = (
                    "Se identifica la forma X = AX ∪ B y se despeja la variable "
                    "mediante X = A*B."
                )

        self.step_title.setText(title)
        self.step_description.setText(description)
        self.step_counter.setText(f"Paso {index + 1} de {self.pages.count()}")
        self.previous_button.setEnabled(index > 0)
        self.next_button.setEnabled(index < last_index)

    def _build_initial_system_page(self) -> QWidget:
        equations = "".join(
            _math_line(equation_to_html(equation.variable, equation.expression))
            for equation in self.solution.initial_system.equations
        )
        order = " &rarr; ".join(
            f"<i>{state}</i>" for state in self.solution.elimination_order
        )
        body = (
            _section("Sistema inicial", equations)
            + _section("Orden de eliminación", _math_line(order))
        )
        return self._rich_page(body, "regularExpressionInitialSystem")

    def _build_substitution_page(self, step: EquationSubstitutionStep) -> QWidget:
        body = _section(
            "Antes",
            _math_line(
                equation_to_html(
                    step.target_before.variable,
                    step.target_before.expression,
                )
            ),
        )
        body += _section(
            "Usamos",
            _math_line(equation_to_html(step.source.variable, step.source.expression)),
        )
        body += _section(
            "Sustitución directa",
            _math_line(
                equation_to_html(
                    step.target_before.variable,
                    step.substituted_expression,
                )
            ),
        )
        if step.substituted_expression != step.target_after.expression:
            body += _section(
                "Después de distribuir",
                _math_line(
                    equation_to_html(
                        step.target_after.variable,
                        step.target_after.expression,
                    )
                ),
            )
        return self._rich_page(body, "regularExpressionSubstitutionStep")

    def _build_arden_page(self, step: ArdenApplicationStep) -> QWidget:
        body = _section(
            "Antes",
            _math_line(
                equation_to_html(
                    step.equation_before.variable,
                    step.equation_before.expression,
                )
            ),
        )
        body += _section(
            "Identificación",
            _math_line(
                arden_identification_to_html(
                    step.coefficient,
                    step.variable,
                    step.remainder,
                )
            ),
        )
        body += _section(
            "Lema de Arden",
            _math_line("<i>X</i> = <i>A</i><i>X</i> &cup; <i>B</i>")
            + _math_line("<i>X</i> = <i>A</i><sup>*</sup><i>B</i>"),
        )
        body += _section(
            "Resultado",
            _math_line(
                equation_to_html(
                    step.equation_after.variable,
                    step.equation_after.expression,
                )
            ),
        )
        return self._rich_page(body, "regularExpressionArdenStep")

    def _build_result_page(self) -> QWidget:
        body = _section(
            "Ecuación final",
            _math_line(
                equation_to_html(
                    self.solution.final_equation.variable,
                    self.solution.final_equation.expression,
                )
            ),
        )
        body += _section(
            "Expresión regular equivalente",
            _math_line(expression_to_html(self.solution.expression), emphasis=True),
        )
        return self._rich_page(body, "regularExpressionFinalResult")

    @staticmethod
    def _rich_page(body: str, object_name: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)

        browser = QTextBrowser()
        browser.setObjectName(object_name)
        browser.setOpenExternalLinks(False)
        browser.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        browser.setHtml(_html_document(body))
        browser.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        layout.addWidget(browser, 1)
        return page


class RegularExpressionSummaryDialog(QDialog):
    """Show the full automaton-to-regex derivation in a single scrollable view."""

    def __init__(
        self,
        solution: RegularEquationSolution,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent, _normal_window_flags())
        self.solution = solution
        self.setObjectName("regularExpressionSummaryDialog")
        self.setWindowTitle("Resumen — Autómata → expresión regular")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMinimumSize(900, 600)
        self.resize(1120, 760)
        self.setSizeGripEnabled(True)

        title = QLabel("Procedimiento completo")
        title.setObjectName("regularExpressionProcessTitle")
        description = QLabel(
            "Sistema inicial, sustituciones, aplicaciones del lema de Arden y "
            "expresión regular equivalente en una sola vista."
        )
        description.setObjectName("secondaryText")
        description.setWordWrap(True)

        self.browser = QTextBrowser()
        self.browser.setObjectName("regularExpressionSummary")
        self.browser.setOpenExternalLinks(False)
        self.browser.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.browser.setHtml(_html_document(_summary_body(solution)))
        self.browser.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)
        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.browser, 1)
        layout.addLayout(actions)


def _summary_body(solution: RegularEquationSolution) -> str:
    equations = "".join(
        _math_line(equation_to_html(equation.variable, equation.expression))
        for equation in solution.initial_system.equations
    )
    order = " &rarr; ".join(f"<i>{state}</i>" for state in solution.elimination_order)
    body = _summary_step(
        1,
        "Sistema inicial de ecuaciones",
        _section("Sistema inicial", equations)
        + _section("Orden de eliminación", _math_line(order)),
    )

    for index, step in enumerate(solution.steps, start=2):
        if isinstance(step, EquationSubstitutionStep):
            step_body = _section(
                "Antes",
                _math_line(
                    equation_to_html(
                        step.target_before.variable,
                        step.target_before.expression,
                    )
                ),
            )
            step_body += _section(
                "Usamos",
                _math_line(equation_to_html(step.source.variable, step.source.expression)),
            )
            step_body += _section(
                "Sustitución directa",
                _math_line(
                    equation_to_html(
                        step.target_before.variable,
                        step.substituted_expression,
                    )
                ),
            )
            if step.substituted_expression != step.target_after.expression:
                step_body += _section(
                    "Después de distribuir",
                    _math_line(
                        equation_to_html(
                            step.target_after.variable,
                            step.target_after.expression,
                        )
                    ),
                )
            title = (
                f"Reemplazar {step.source.variable.render()} en "
                f"{step.target_before.variable.render()}"
            )
        else:
            step_body = _section(
                "Antes",
                _math_line(
                    equation_to_html(
                        step.equation_before.variable,
                        step.equation_before.expression,
                    )
                ),
            )
            step_body += _section(
                "Identificación",
                _math_line(
                    arden_identification_to_html(
                        step.coefficient,
                        step.variable,
                        step.remainder,
                    )
                ),
            )
            step_body += _section(
                "Lema de Arden",
                _math_line("<i>X</i> = <i>A</i><i>X</i> &cup; <i>B</i>")
                + _math_line("<i>X</i> = <i>A</i><sup>*</sup><i>B</i>"),
            )
            step_body += _section(
                "Resultado",
                _math_line(
                    equation_to_html(
                        step.equation_after.variable,
                        step.equation_after.expression,
                    )
                ),
            )
            title = f"Aplicar el lema de Arden en {step.variable.render()}"
        body += _summary_step(index, title, step_body)

    final_index = len(solution.steps) + 2
    final_body = _section(
        "Ecuación final",
        _math_line(
            equation_to_html(
                solution.final_equation.variable,
                solution.final_equation.expression,
            )
        ),
    )
    final_body += _section(
        "Expresión regular equivalente",
        _math_line(expression_to_html(solution.expression), emphasis=True),
    )
    body += _summary_step(final_index, "Expresión regular equivalente", final_body)
    return body


def _summary_step(number: int, title: str, body: str) -> str:
    return (
        '<div class="summary-step">'
        f'<div class="step-heading">{number}. {title}</div>'
        f"{body}"
        "</div>"
    )


def _section(title: str, contents: str) -> str:
    return (
        '<div class="section">'
        f'<div class="section-title">{title}</div>'
        f"{contents}"
        "</div>"
    )


def _math_line(contents: str, *, emphasis: bool = False) -> str:
    css_class = "math final-math" if emphasis else "math"
    return f'<div class="{css_class}">{contents}</div>'


def _html_document(body: str) -> str:
    return f"""
    <html>
      <head>
        <style>
          body {{ margin: 4px; font-size: 15px; }}
          .section {{ margin: 8px 0 22px 0; }}
          .section-title {{ font-size: 16px; font-weight: 600; margin-bottom: 8px; }}
          .math {{ font-family: serif; font-size: 21px; margin: 5px 0; white-space: nowrap; }}
          .final-math {{ font-size: 24px; font-weight: 600; }}
          .summary-step {{ margin: 6px 0 30px 0; padding-bottom: 16px; }}
          .step-heading {{ font-size: 18px; font-weight: 700; margin-bottom: 12px; }}
          sub, sup {{ font-size: 70%; }}
        </style>
      </head>
      <body>{body}</body>
    </html>
    """
