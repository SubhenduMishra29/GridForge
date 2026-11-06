# ============================================================
# GridForge V2 — Messages / Events Panel
# Author: Subhendu Mishra
# ============================================================
from __future__ import annotations
from typing import Iterable
from ui.core.qt import QLabel, QListWidget, QVBoxLayout, QWidget

class MessagesPanelWidget(QWidget):
    """Presentation surface combining semantic Application events and validation messages."""
    def __init__(self,parent:QWidget|None=None)->None:
        super().__init__(parent); self.setObjectName("GridForgePanel_messages")
        self._validation:tuple[str,...]=(); self._events:tuple[str,...]=()
        self._list=QListWidget(self); self._list.setObjectName("MessagesEventsList")
        root=QVBoxLayout(self); root.setContentsMargins(6,6,6,6)
        title=QLabel("Messages / Events",self); title.setProperty("role","panelTitle"); root.addWidget(title); root.addWidget(self._list)
    def set_messages(self,messages:Iterable[str])->None:
        self.set_validation_messages(messages)
    def set_validation_messages(self,messages:Iterable[str])->None:
        self._validation=tuple(str(x) for x in messages); self._render()
    def set_event_messages(self,messages:Iterable[str])->None:
        self._events=tuple(str(x) for x in messages); self._render()
    def append_message(self,message:str)->None:
        self._events=(*self._events,str(message)); self._render()
    def _render(self)->None:
        self._list.clear()
        if self._validation: self._list.addItems(self._validation)
        if self._events: self._list.addItems(self._events)
__all__=["MessagesPanelWidget"]
