from __future__ import annotations

from typing import Callable, Iterable

from ui.core.qt import QListWidget, QPushButton, QVBoxLayout, QWidget


class StudyCasesPanelWidget(QWidget):
    """Presentation surface for application-managed study cases."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_study_cases")
        self._list = QListWidget(self)
        self._run_handler: Callable[[str], object] | None = None
        self._run = QPushButton("Run Study", self)
        self._run.clicked.connect(self._run_selected)
        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        layout.addWidget(self._run)

    def set_cases(self, cases: Iterable[str]) -> None:
        self._list.clear()
        self._list.addItems(tuple(str(case) for case in cases))

    def set_run_handler(self, handler: Callable[[str], object] | None) -> None:
        self._run_handler = handler

    def _run_selected(self) -> None:
        item = self._list.currentItem()
        if item is not None and self._run_handler is not None:
            self._run_handler(item.text())


__all__ = ["StudyCasesPanelWidget"]
