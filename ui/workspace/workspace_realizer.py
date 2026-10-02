# ============================================================
# File: ui/workspace/workspace_realizer.py
# GridForge V2 — Area/Editor/Region Realizer
# Author: Subhendu Mishra
# ============================================================

"""Canonical Workspace → Area → Editor → Region Qt realization boundary.

Dock/panel bindings remain only as an explicit compatibility surface for
legacy utility panels. They are never read from WorkspaceDefinition or
WorkspaceLayout and therefore cannot define workspace policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ui.core.qt import QDockWidget, Qt

from .workspace_layout import WorkspaceLayout
from .engineering_context import EditorContext


class WorkspaceRealizationError(RuntimeError):
    """Raised when a canonical workspace cannot be realized."""


@dataclass(frozen=True, slots=True)
class DockBinding:
    """Legacy panel/dock binding isolated from canonical workspace state."""

    panel_id: str
    dock_widget: QDockWidget


class WorkspaceRealizer:
    """Realize canonical Areas and their Editors through the editor host."""

    def __init__(self, *, main_window=None, editor_host: Any | None = None) -> None:
        if editor_host is None:
            raise ValueError("WorkspaceRealizer requires an EngineeringEditorHost.")
        self._main_window = main_window
        self._editor_host = editor_host
        self._bindings: dict[str, DockBinding] = {}
        self._realized_layout: WorkspaceLayout | None = None
        self._focused_area_id: str | None = None

    @property
    def editor_host(self) -> Any:
        return self._editor_host

    @property
    def main_window(self):
        return self._main_window

    @property
    def bindings(self) -> Mapping[str, DockBinding]:
        """Return compatibility bindings; canonical workspace state never uses them."""
        return dict(self._bindings)

    @property
    def realized_layout(self) -> WorkspaceLayout | None:
        return self._realized_layout

    @property
    def focused_area_id(self) -> str | None:
        return self._focused_area_id

    # ------------------------------------------------------------------
    # Explicit legacy compatibility API
    # ------------------------------------------------------------------

    def register_dock(self, *, panel_id: str, dock_widget: QDockWidget, replace: bool = False) -> None:
        if not isinstance(panel_id, str) or not panel_id.strip():
            raise ValueError("panel_id must be a non-empty string.")
        if not isinstance(dock_widget, QDockWidget):
            raise TypeError("dock_widget must be a QDockWidget.")
        if panel_id in self._bindings and not replace:
            raise ValueError(f"Dock already registered for panel: {panel_id!r}")
        self._bindings[panel_id] = DockBinding(panel_id, dock_widget)

    def unregister_dock(self, panel_id: str) -> DockBinding | None:
        return self._bindings.pop(panel_id, None)

    def get_dock(self, panel_id: str) -> QDockWidget | None:
        binding = self._bindings.get(panel_id)
        return binding.dock_widget if binding is not None else None

    def detach_all_docks(self) -> tuple[DockBinding, ...]:
        detached = tuple(self._bindings.values())
        self._bindings.clear()
        return detached

    # ------------------------------------------------------------------
    # Canonical realization
    # ------------------------------------------------------------------

    def realize(self, layout: WorkspaceLayout, *, workspace_id: str | None = None) -> None:
        if not isinstance(layout, WorkspaceLayout):
            raise TypeError("layout must be a WorkspaceLayout.")
        if not layout.areas:
            raise WorkspaceRealizationError("Workspace layout contains no Areas.")

        previous = self._realized_layout
        try:
            self._realize_areas(layout, workspace_id=workspace_id)        except BaseException:
            if previous is not None:
                try:
                    self._realize_areas(previous, workspace_id=workspace_id)                except BaseException as restore_exc:
                    raise WorkspaceRealizationError(
                        "Workspace realization failed and previous editor state could not be restored."
                    ) from restore_exc
            raise

        self._realized_layout = layout

    def _realize_areas(self, layout: WorkspaceLayout, *, workspace_id: str | None = None) -> None:
        main_areas = [
            area for area in layout.areas
            if area.visible and area.metadata.get("role") == "main"
        ]
        if not main_areas:
            raise WorkspaceRealizationError("Workspace must declare a visible main Area.")

        for area in sorted(layout.areas, key=lambda item: item.order):
            if not area.visible:
                continue
            editor = area.editor
            editor_id = editor.editor_id
            editor_type = editor.editor_type
            if area.metadata.get("role") == "main":
                target = {"study": "reports"}.get(editor_type, editor_type)
                activate = getattr(self._editor_host, "activate", None)
                if not callable(activate):
                    raise WorkspaceRealizationError("Editor host does not expose activate().")
                context = EditorContext(workspace=workspace_id, area=area, editor=editor)
                activate(target, area=area, context=context)
                self._focused_area_id = area.area_id

    def focus_area(self, area_id: str) -> None:
        if self._realized_layout is None:
            raise RuntimeError("No workspace is realized.")
        area = self._realized_layout.get_area(area_id)
        if area is None:
            raise KeyError(f"Unknown Area: {area_id!r}")
        if not area.visible:
            raise RuntimeError(f"Area {area_id!r} is not visible.")
        activate = getattr(self._editor_host, "activate", None)
        if not callable(activate):
            raise WorkspaceRealizationError("Editor host does not expose activate().")
        activate({"study": "reports"}.get(area.editor.editor_type, area.editor.editor_type), area=area)
        self._focused_area_id = area.area_id

    def maximize_area(self, area_id: str) -> None:
        self.focus_area(area_id)
        maximize = getattr(self._editor_host, "set_area_maximized", None)
        if callable(maximize):
            maximize(area_id, True)

    def restore_area(self) -> None:
        restore = getattr(self._editor_host, "set_area_maximized", None)
        if callable(restore):
            restore(self._focused_area_id, False)

    def clear_realization(self) -> None:
        deactivate = getattr(self._editor_host, "deactivate", None)
        if callable(deactivate):
            deactivate()
        self._realized_layout = None
        self._focused_area_id = None


__all__ = ["DockBinding", "WorkspaceRealizationError", "WorkspaceRealizer"]
