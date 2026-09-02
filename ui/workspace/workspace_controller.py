# ============================================================
# File: ui/workspace/workspace_controller.py
# GridForge V2 — Presentation Workspace Controller
# Author: Subhendu Mishra
# ============================================================

"""Presentation-level orchestration for Workspace realization.

The controller coordinates WorkspaceManager and WorkspaceRealizer.
It does not own logical workspace state or Qt realization state.
"""

from __future__ import annotations

from .workspace_layout import WorkspaceLayout
from .workspace_manager import WorkspaceManager
from .workspace_realizer import WorkspaceRealizer
from .workspace_state import WorkspaceState


class WorkspaceController:
    """Coordinate logical Workspace state with UI realization."""

    def __init__(self, *, manager: WorkspaceManager, realizer: WorkspaceRealizer) -> None:
        if not isinstance(manager, WorkspaceManager):
            raise TypeError("manager must be a WorkspaceManager.")
        if not isinstance(realizer, WorkspaceRealizer):
            raise TypeError("realizer must be a WorkspaceRealizer.")
        self._manager = manager
        self._realizer = realizer
        self._closed = False

    @property
    def manager(self) -> WorkspaceManager:
        return self._manager

    @property
    def realizer(self) -> WorkspaceRealizer:
        return self._realizer

    @property
    def state(self) -> WorkspaceState | None:
        return self._manager.state

    @property
    def active_workspace_id(self) -> str | None:
        return self._manager.active_workspace_id

    @property
    def realized_layout(self) -> WorkspaceLayout | None:
        return self._realizer.realized_layout

    @property
    def closed(self) -> bool:
        return self._closed

    def activate(self, workspace_id: str) -> WorkspaceState:
        self._ensure_open()
        candidate = self._manager.prepare_activate(workspace_id)
        self._realizer.realize(candidate.layout)
        return self._manager.commit(candidate)

    def apply_layout(self, layout: WorkspaceLayout) -> WorkspaceState:
        self._ensure_open()
        candidate = self._manager.prepare_layout(layout)
        self._realizer.realize(candidate.layout)
        return self._manager.commit(candidate)

    def reset(self) -> WorkspaceState:
        self._ensure_open()
        candidate = self._manager.prepare_reset_active()
        self._realizer.realize(candidate.layout)
        return self._manager.commit(candidate)

    def close(self) -> None:
        """Release presentation realization and make this coordinator inert."""
        if self._closed:
            return
        self._realizer.close()
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("WorkspaceController is closed.")


__all__ = ["WorkspaceController"]
