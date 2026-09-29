from __future__ import annotations

from typing import Any, Iterable, Mapping

from ui.core.qt import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class ElementListPanelWidget(QWidget):
    """Read-only presentation surface for application element rows."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_element_list")
        self._table = QTableWidget(self)
        self._table.setObjectName("ElementListTable")
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(("ID", "Name", "Type", "Nominal Voltage", "Status"))
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(QLabel("Element List", self))
        layout.addWidget(self._table)

    def set_rows(self, rows: Iterable[Mapping[str, Any]]) -> None:
        materialized = tuple(rows)
        self._table.setRowCount(len(materialized))
        for index, row in enumerate(materialized):
            values = (
                row.get("id", row.get("element_id", "")),
                row.get("name", row.get("type", "Element")),
                row.get("type", ""),
                row.get("nominal_voltage", row.get("nominalVoltage", "")),
                row.get("status", "Normal"),
            )
            for column, value in enumerate(values):
                self._table.setItem(index, column, QTableWidgetItem(str(value)))


__all__ = ["ElementListPanelWidget"]
