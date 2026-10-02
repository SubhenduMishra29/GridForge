# ============================================================
# File: ui/editors/common/editor_host.py
# GridForge V2 — Engineering Editor Host
# Author: Subhendu Mishra
# ============================================================

"""Qt realization of the canonical Area → Editor → Region composition."""

from __future__ import annotations

from typing import Any

from ui.core.qt import QFrame, QGraphicsView, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget


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

    @property
    def active_region_widget(self) -> QWidget | None:
        """Return the realized widget for the active Region, when available."""
        if self._active_editor_id is None or self._active_region_id is None:
            return None
        editor = self._editors.get(self._active_editor_id)
        resolver = getattr(editor, "region_widget", None) if editor is not None else None
        return resolver(self._active_region_id) if callable(resolver) else None

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
        if context is not None and getattr(context, "editor", None) is not None:
            canonical_editor_id = getattr(context.editor, "editor_id", editor_id)
            if canonical_editor_id != editor_id and canonical_editor_id in self._editors:
                raise ValueError(f"Editor activation ID {editor_id!r} does not match context editor {canonical_editor_id!r}.")
        resolved_region_id = region_id or self._default_region_id(widget)
        if resolved_region_id is not None:
            resolver = getattr(widget, "region_widget", None)
            if not callable(resolver) or resolver(resolved_region_id) is None:
                raise KeyError(f"Editor {editor_id!r} does not realize Region {resolved_region_id!r}.")
        if context is not None and callable(getattr(context, "with_updates", None)):
            context = context.with_updates(view_state=self._read_view_state(widget))
        self._stack.setCurrentWidget(widget)
        self._active_editor_id = editor_id
        self._active_area = area
        self._active_region_id = resolved_region_id
        self._editor_context = context
        apply_context = getattr(widget, "set_editor_context", None)
        if callable(apply_context):
            apply_context(context)

    @staticmethod
    def _read_view_state(widget: QWidget) -> dict[str, object]:
        view = widget if isinstance(widget, QGraphicsView) else widget.findChild(QGraphicsView)
        if view is None:
            return {
                "zoom": None,
                "pan": None,
                "grid_visibility": getattr(widget, "grid_visible", None),
                "snap_state": getattr(widget, "snap_enabled", None),
                "overlay_state": getattr(widget, "overlay_state", None),
                "routing_preferences": getattr(widget, "routing_preferences", None),
                "display_preferences": getattr(widget, "display_preferences", None),
            }
        return {
            "zoom": float(view.transform().m11()),
            "pan": (int(view.horizontalScrollBar().value()), int(view.verticalScrollBar().value())),
            "grid_visibility": getattr(widget, "grid_visible", None),
            "snap_state": getattr(widget, "snap_enabled", None),
            "overlay_state": getattr(widget, "overlay_state", None),
            "routing_preferences": getattr(widget, "routing_preferences", None),
            "display_preferences": getattr(widget, "display_preferences", None),
        }

    @staticmethod
    def _default_region_id(widget: QWidget) -> str | None:
        resolver = getattr(widget, "default_region_id", None)
        value = resolver() if callable(resolver) else getattr(widget, "DEFAULT_REGION_ID", None)
        return str(value) if value is not None else None

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
