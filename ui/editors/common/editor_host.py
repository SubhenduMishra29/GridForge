# ============================================================
# File: ui/editors/common/editor_host.py
# GridForge V2 — Engineering Editor Host
# Author: Subhendu Mishra
# ============================================================

"""Qt realization of the canonical Area → Editor → Region composition."""

from __future__ import annotations

from typing import Any

from ui.core.qt import QFrame, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget


class EngineeringEditorHost(QWidget):
    """Presentation-only host for active Area, Editor and Region context."""

    def __init__(self, *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editors: dict[str, QWidget] = {}
        self._editor_context: Any | None = None
        self._active_area: Any | None = None
        self._active_editor_id: str | None = None
        self._active_region_id: str | None = None
        self._maximized_area_id: str | None = None
        self._stack = QStackedWidget(self)
        self._stack.setObjectName("GridForgeEditorStack")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

    @property
    def editor_ids(self) -> tuple[str, ...]:
        return tuple(self._editors)

    @property
    def active_editor_id(self) -> str | None:
        return self._active_editor_id

    @property
    def active_area(self) -> Any | None:
        return self._active_area

    @property
    def editor_context(self) -> Any | None:
        return self._editor_context

    @property
    def maximized_area_id(self) -> str | None:
        return self._maximized_area_id

    def register_editor(self, editor_id: str, widget: QWidget) -> None:
        if not isinstance(editor_id, str) or not editor_id.strip():
            raise ValueError("editor_id must be a non-empty string.")
        if not isinstance(widget, QWidget):
            raise TypeError("widget must be QWidget.")
        if editor_id in self._editors:
            raise ValueError(f"Editor already registered: {editor_id!r}")
        self._editors[editor_id] = widget
        self._stack.addWidget(widget)

    def activate(
        self,
        editor_id: str,
        *,
        area: Any | None = None,
        region_id: str | None = None,
        context: Any | None = None,
    ) -> None:
        widget = self._editors.get(editor_id)
        if widget is None:
            raise KeyError(f"Unknown editor: {editor_id!r}")
        self._stack.setCurrentWidget(widget)
        self._active_editor_id = editor_id
        self._active_area = area
        self._active_region_id = region_id
        self._editor_context = context

    def deactivate(self) -> None:
        self._active_editor_id = None
        self._active_area = None
        self._active_region_id = None
        self._editor_context = None
        self._maximized_area_id = None

    def set_editor_context(self, context: Any | None) -> None:
        """Install the current immutable EditorContext snapshot."""
        self._editor_context = context

    def set_area_maximized(self, area_id: str | None, maximized: bool) -> None:
        if maximized:
            if not isinstance(area_id, str) or not area_id.strip():
                raise ValueError("area_id is required when maximizing an Area.")
            if self._active_area is not None and getattr(self._active_area, "area_id", area_id) != area_id:
                raise RuntimeError(f"Area {area_id!r} is not the active Area.")
            self._maximized_area_id = area_id
            self.setProperty("gridforge_area_maximized", True)
        else:
            self._maximized_area_id = None
            self.setProperty("gridforge_area_maximized", False)

    def widget(self, editor_id: str) -> QWidget | None:
        return self._editors.get(editor_id)


class EditorRegionFrame(QFrame):
    """Reusable Qt realization of one logical Region."""

    def __init__(self, title: str = "", *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(f"GridForgeRegion_{title.lower().replace(' ', '_') or 'region'}")
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
