from __future__ import annotations

from typing import Any, Iterable, Mapping

from ui.core.qt import QLabel, QListWidget, QVBoxLayout, QWidget


class ElementListPanelWidget(QWidget):
    """Read-only presentation surface for application element rows."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_element_list")
        self._list = QListWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Element List", self))
        layout.addWidget(self._list)

    def set_rows(self, rows: Iterable[Mapping[str, Any]]) -> None:
        self._list.clear()
        for row in rows:
            element_id = row.get("id", row.get("element_id", ""))
            label = row.get("name", row.get("type", "Element"))
            self._list.addItem(f"{label} — {element_id}")


__all__ = ["ElementListPanelWidget"]
