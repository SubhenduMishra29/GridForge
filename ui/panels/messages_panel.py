from __future__ import annotations

from typing import Iterable

from ui.core.qt import QListWidget, QVBoxLayout, QWidget


class MessagesPanelWidget(QWidget):
    """Presentation surface for application events and validation messages."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_messages")
        self._list = QListWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self._list)

    def set_messages(self, messages: Iterable[str]) -> None:
        self._list.clear()
        self._list.addItems(tuple(str(message) for message in messages))

    def append_message(self, message: str) -> None:
        self._list.addItem(str(message))


__all__ = ["MessagesPanelWidget"]
