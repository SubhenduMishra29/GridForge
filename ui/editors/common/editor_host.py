# ============================================================
# File: ui/editors/common/editor_host.py
# GridForge V2 — Engineering Editor Host
# Author: Subhendu Mishra
# ============================================================

"""Reusable Qt realization of the Area → Editor → Region model."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ui.core.qt import QFrame, QHBoxLayout, QLabel, QStackedWidget, QToolBar, QVBoxLayout, QWidget


class EngineeringEditorHost(QWidget):
    """Host stable editor regions without owning domain state.

    Domain editors supply their already-composed canvas/interaction widgets.
    The host only arranges presentation regions and switches editor instances.
    """

    def __init__(self, *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editors: dict[str, QWidget] = {}
        self._stack = QStackedWidget(self)
        self._stack.setObjectName("GridForgeEditorStack")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

    @property
    def editor_ids(self) -> tuple[str, ...]:
        return tuple(self._editors)

    def register_editor(self, editor_id: str, widget: QWidget) -> None:
        if not isinstance(editor_id, str) or not editor_id.strip():
            raise ValueError("editor_id must be a non-empty string.")
        if not isinstance(widget, QWidget):
            raise TypeError("widget must be QWidget.")
        if editor_id in self._editors:
            raise ValueError(f"Editor already registered: {editor_id!r}")
        self._editors[editor_id] = widget
        self._stack.addWidget(widget)

    def activate(self, editor_id: str) -> None:
        widget = self._editors.get(editor_id)
        if widget is None:
            raise KeyError(f"Unknown editor: {editor_id!r}")
        self._stack.setCurrentWidget(widget)

    def widget(self, editor_id: str) -> QWidget | None:
        return self._editors.get(editor_id)


class EditorRegionFrame(QFrame):
    """Small reusable region container for domain editor realization."""

    def __init__(self, title: str, *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(f"GridForgeRegion_{title.lower().replace(' ', '_')}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        if title:
            label = QLabel(title, self)
            label.setObjectName("GridForgeRegionTitle")
            layout.addWidget(label)
        self._content = QVBoxLayout()
        layout.addLayout(self._content)

    def set_widget(self, widget: QWidget) -> None:
        if not isinstance(widget, QWidget):
            raise TypeError("widget must be QWidget.")
        while self._content.count():
            item = self._content.takeAt(0)
            old = item.widget()
            if old is not None:
                old.setParent(None)
        self._content.addWidget(widget)


__all__ = ["EngineeringEditorHost", "EditorRegionFrame"]
