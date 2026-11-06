# ============================================================
# GridForge V2 — Element List Panel
# Author: Subhendu Mishra
# ============================================================
from __future__ import annotations
from typing import Any, Iterable, Mapping
from ui.core.qt import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

class ElementListPanelWidget(QWidget):
    """Read-only element projection synchronized with canonical selection."""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_element_list")
        self._rows: tuple[Mapping[str, Any], ...] = ()
        self._selection_manager: Any | None = None
        self._updating_selection = False
        self._table = QTableWidget(self)
        self._table.setObjectName("ElementListTable")
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(("ID","Name","Type","Nominal Voltage","Status"))
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.itemSelectionChanged.connect(self._on_row_selected)
        layout=QVBoxLayout(self); layout.setContentsMargins(6,6,6,6)
        title=QLabel("Element List",self); title.setProperty("role","panelTitle"); layout.addWidget(title); layout.addWidget(self._table)
    def bind_selection_manager(self, selection_manager: Any) -> None:
        if selection_manager is None or not callable(getattr(selection_manager,"select_single",None)): raise TypeError("selection_manager must provide select_single().")
        self._selection_manager=selection_manager
    def set_rows(self, rows: Iterable[Mapping[str, Any]]) -> None:
        self._rows=tuple(rows)
        selected={str(x) for x in self._selection_manager.get_selected_ids()} if self._selection_manager is not None else set()
        self._updating_selection=True
        try:
            self._table.setRowCount(len(self._rows))
            for i,row in enumerate(self._rows):
                values=(row.get("id",row.get("element_id","")),row.get("name",row.get("type","Element")),row.get("type",""),row.get("nominal_voltage",row.get("nominalVoltage","")),row.get("status","Normal"))
                for col,value in enumerate(values): self._table.setItem(i,col,QTableWidgetItem(str(value)))
                if str(values[0]) in selected: self._table.selectRow(i)
        finally: self._updating_selection=False
    def _on_row_selected(self) -> None:
        if self._updating_selection or self._selection_manager is None: return
        rows=self._table.selectionModel().selectedRows()
        if not rows: return
        row=rows[0].row()
        if 0 <= row < len(self._rows):
            object_id=self._rows[row].get("id",self._rows[row].get("element_id"))
            if object_id is not None: self._selection_manager.select_single(str(object_id))
__all__=["ElementListPanelWidget"]
