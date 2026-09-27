from __future__ import annotations

from typing import Callable, Iterable
from uuid import UUID

from ui.core.qt import QListWidget, QPushButton, QVBoxLayout, QWidget


class StudyCasesPanelWidget(QWidget):
    """Presentation surface for application-managed study cases."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_study_cases")
        self._list = QListWidget(self)
        self._run_handler: Callable[[UUID], object] | None = None
        self._case_rows: tuple[object, ...] = ()
        self._run = QPushButton("Run Study", self)
        self._run.clicked.connect(self._run_selected)
        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        layout.addWidget(self._run)

    def set_cases(self, cases: Iterable[object]) -> None:
        self._case_rows = tuple(cases)
        self._list.clear()
        labels = []
        for row in self._case_rows:
            study_type = str(getattr(row, "study_type", "study"))
            status = str(getattr(row, "status", "unknown"))
            freshness = "" if bool(getattr(row, "current", True)) else " [STALE]"
            display_name = str(getattr(row, "display_name", study_type))
            message = str(getattr(row, "message", "") or "")
            suffix = f" — {message}" if message else ""
            labels.append(f"{display_name} [{status}]{freshness}{suffix}")
        self._list.addItems(tuple(labels))

    def set_run_handler(self, handler: Callable[[UUID], object] | None) -> None:
        self._run_handler = handler

    def selected_case(self) -> object | None:
        index = self._list.currentRow()
        if index < 0 or index >= len(self._case_rows):
            return None
        return self._case_rows[index]

    def selected_case_id(self) -> UUID | None:
        row = self.selected_case()
        if row is None:
            return None
        study_id = getattr(row, "study_id", None)
        if isinstance(study_id, UUID):
            return study_id
        try:
            return UUID(str(study_id))
        except (TypeError, ValueError):
            return None

    def _run_selected(self) -> None:
        study_id = self.selected_case_id()
        if study_id is not None and self._run_handler is not None:
            self._run_handler(study_id)


__all__ = ["StudyCasesPanelWidget"]
