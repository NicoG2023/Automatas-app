"""Application bootstrap."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from app_automatas.controller.app_controller import AppController
from app_automatas.model.editor_session import EditorSession
from app_automatas.view.main_window import MainWindow


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application, or reuse the current one during tests."""
    existing = QApplication.instance()
    if existing is not None:
        return existing

    app = QApplication(list(argv) if argv is not None else sys.argv)
    app.setApplicationName("App de Autómatas")
    app.setOrganizationName("Universidad Distrital")
    return app


def build_controller() -> AppController:
    """Wire the first MVC objects together."""
    model = EditorSession()
    view = MainWindow()
    return AppController(model=model, view=view)


def main() -> int:
    """Run the desktop application."""
    app = create_application()
    controller = build_controller()
    controller.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
