# ============================================================
# File: ui/panels/study_cases_panel.py
# GridForge V2 — Study Cases and Results Panel
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from typing import Callable, Iterable
from uuid import UUID

from ui.core.qt import (
    QComboBox, QFormLayout, QLabel, QLineEdit, QListWidget,
    QPushButton, QVBoxLayout, QWidget,
)


class StudyCasesPanelWidget(QWidget):
    """Presentation surface for Application-managed Study Cases and results."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_study_cases")
        self._list = QListWidget(self)
        self._run_handler: Callable[[UUID], object] | None = None
        self._create_handler: Callable[..., object] | None = None
        self._result_selection_handler: Callable[[UUID | None], object] | None = None
        self._case_rows: tuple[object, ...] = ()

        self._case_name = QLineEdit(self)
        self._case_name.setPlaceholderText("Optional Study Case name")
        self._study_type = QComboBox(self)
        self._study_type.addItem("Power Flow", "power_flow")
        self._study_type.addItem("Short-Circuit", "short_circuit")
        self._study_type.addItem("Transient Stability", "transient_stability")
        self._slack_bus = QComboBox(self)
        self._fault_bus = QComboBox(self)
        self._pv_buses = QLineEdit(self)
        self._pv_buses.setPlaceholderText("Optional PV Bus IDs, comma-separated")
        self._base_mva = QLineEdit(self)
        self._base_mva.setPlaceholderText("System base MVA")
        self._fault_type = QComboBox(self)
        for label, value in (("Three-phase (3PH)", "3PH"), ("Single-line-to-ground (LG)", "LG"),
                             ("Line-to-line (LL)", "LL"), ("Double-line-to-ground (LLG)", "LLG")):
            self._fault_type.addItem(label, value)
        self._fault_r = QLineEdit(self)
        self._fault_r.setPlaceholderText("Fault resistance in ohms (default 0)")
        self._fault_x = QLineEdit(self)
        self._fault_x.setPlaceholderText("Fault reactance in ohms (default 0)")
        self._end_time = QLineEdit(self)
        self._end_time.setText("10.0")
        self._dt = QLineEdit(self)
        self._dt.setText("0.01")

        form = QFormLayout()
        form.addRow("Case name", self._case_name)
        form.addRow("Study type", self._study_type)
        form.addRow("Slack Bus (PF / transient init.)", self._slack_bus)
        form.addRow("PV Bus IDs (comma-separated)", self._pv_buses)
        form.addRow("System base MVA", self._base_mva)
        form.addRow("Fault Bus (short-circuit)", self._fault_bus)
        form.addRow("Fault type", self._fault_type)
        form.addRow("Fault resistance (Ω)", self._fault_r)
        form.addRow("Fault reactance (Ω)", self._fault_x)
        form.addRow("Transient end time (s)", self._end_time)
        form.addRow("Transient step (s)", self._dt)
        self._create = QPushButton("Create Study Case", self)
        self._create.clicked.connect(self._create_study_case)

        self._result_heading = QLabel("Study Results", self)
        self._result_list = QListWidget(self)
        self._run = QPushButton("Run Study", self)
        self._run.clicked.connect(self._run_selected)
        self._list.currentRowChanged.connect(self._on_case_selected)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Create Study Case", self))
        layout.addLayout(form)
        layout.addWidget(self._create)
        layout.addWidget(self._list)
        layout.addWidget(self._run)
        layout.addWidget(self._result_heading)
        layout.addWidget(self._result_list)
        self.set_result_details("Select a completed study to inspect its results.", ())

    def set_available_buses(self, bus_ids: Iterable[str]) -> None:
        """Refresh Bus choices from the Application network read model."""
        normalized = tuple(sorted({str(bus_id).strip() for bus_id in bus_ids if str(bus_id).strip()}))
        for combo in (self._slack_bus, self._fault_bus):
            previous = combo.currentText()
            existing = tuple(combo.itemText(index) for index in range(1, combo.count()))
            if existing == normalized:
                continue
            combo.clear()
            combo.addItem("Select Bus")
            combo.addItems(normalized)
            if previous in normalized:
                combo.setCurrentText(previous)

    def set_cases(self, cases: Iterable[object]) -> None:
        previous_id = self.selected_case_id()
        self._case_rows = tuple(cases)
        previous_signal_state = self._list.blockSignals(True)
        try:
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
            restored_index = next((i for i, row in enumerate(self._case_rows)
                                   if getattr(row, "study_id", None) == previous_id), -1)
            if restored_index >= 0:
                self._list.setCurrentRow(restored_index)
            elif self._case_rows:
                self._list.setCurrentRow(0)
        finally:
            self._list.blockSignals(previous_signal_state)
        self._on_case_selected(self._list.currentRow())
        if not self._case_rows:
            self.set_result_details("No study results are available.", ())

    def set_create_handler(self, handler: Callable[..., object] | None) -> None:
        self._create_handler = handler

    def set_run_handler(self, handler: Callable[[UUID], object] | None) -> None:
        self._run_handler = handler

    def set_result_selection_handler(self, handler: Callable[[UUID | None], object] | None) -> None:
        self._result_selection_handler = handler
        if handler is not None:
            handler(self.selected_case_id())

    def set_result_details(self, title: str, lines: Iterable[str]) -> None:
        self._result_heading.setText(str(title))
        self._result_list.clear()
        values = tuple(str(line) for line in lines)
        self._result_list.addItems(values if values else ("No numerical result payload is available.",))

    def select_case(self, study_id: UUID) -> None:
        index = next((i for i, row in enumerate(self._case_rows)
                      if getattr(row, "study_id", None) == study_id), -1)
        if index >= 0:
            self._list.setCurrentRow(index)

    def selected_case(self) -> object | None:
        index = self._list.currentRow()
        return self._case_rows[index] if 0 <= index < len(self._case_rows) else None

    def selected_case_id(self) -> UUID | None:
        row = self.selected_case()
        study_id = getattr(row, "study_id", None) if row is not None else None
        return study_id if isinstance(study_id, UUID) else None

    def _on_case_selected(self, _index: int) -> None:
        if self._result_selection_handler is not None:
            self._result_selection_handler(self.selected_case_id())

    def _create_study_case(self) -> None:
        if self._create_handler is None:
            return
        created = self._create_handler(
            str(self._study_type.currentData()),
            self._case_name.text(),
            self._slack_bus.currentText(),
            tuple(v.strip() for v in self._pv_buses.text().split(",") if v.strip()),
            self._base_mva.text(),
            self._fault_bus.currentText(),
            str(self._fault_type.currentData()),
            self._fault_r.text().strip() or "0",
            self._fault_x.text().strip() or "0",
            self._end_time.text(),
            self._dt.text(),
        )
        if created is not None:
            self._case_name.clear()
            self._pv_buses.clear()

    def _run_selected(self) -> None:
        study_id = self.selected_case_id()
        if study_id is not None and self._run_handler is not None:
            self._run_handler(study_id)


__all__ = ["StudyCasesPanelWidget"]
