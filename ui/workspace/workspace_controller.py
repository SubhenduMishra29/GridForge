# ============================================================
# File: ui/workspace/workspace_controller.py
# GridForge V2 — Presentation Workspace Controller
# Author: Subhendu Mishra
# ============================================================

"""Presentation-level orchestration for Workspace realization.

Responsibilities
----------------
WorkspaceController coordinates:

    WorkspaceManager
        ↓
    WorkspaceState candidate
        ↓
    WorkspaceRealizer
        ↓
    WorkspaceManager.commit()

This is a Presentation/UI coordinator. It is NOT an
Application-layer controller and must not become the Core↔UI
integration boundary. That boundary will be introduced later
through an explicit interface.

The controller does NOT:

    - import Qt;
    - construct MainWindow;
    - construct WorkspaceDefinition;
    - construct WorkspaceLayout;
    - create panels;
    - register docks;
    - manipulate QDockWidget;
    - define workspace policy;
    - access Core/domain state;
    - perform electrical calculations.

Transactional invariant
-----------------------

The WorkspaceManager is not committed until the corresponding
WorkspaceRealizer operation succeeds.

Therefore:

    prepare()
        ↓
    realize()
        ↓
    commit()

If realization raises an exception, commit() is never called
and the manager's authoritative logical state remains unchanged.
"""

from __future__ import annotations

from .workspace_layout import WorkspaceLayout
from .workspace_manager import WorkspaceManager
from .workspace_realizer import WorkspaceRealizer
from .workspace_state import WorkspaceState


class WorkspaceController:
    """Coordinate logical Workspace state with UI realization.

    WorkspaceManager remains the logical authority.
    WorkspaceRealizer remains the realization authority.
    WorkspaceController owns neither subsystem; it only
    coordinates their presentation-level interaction.
    """

    def __init__(
        self,
        *,
        manager: WorkspaceManager,
        realizer: WorkspaceRealizer,
    ) -> None:
        """Construct the Presentation workspace coordinator."""
        if not isinstance(manager, WorkspaceManager):
            raise TypeError("manager must be a WorkspaceManager.")
        if not isinstance(realizer, WorkspaceRealizer):
            raise TypeError("realizer must be a WorkspaceRealizer.")
        self._manager = manager
        self._realizer = realizer

    @property
    def manager(self) -> WorkspaceManager:
        """Return the WorkspaceManager."""
        return self._manager

    @property
    def realizer(self) -> WorkspaceRealizer:
        """Return the WorkspaceRealizer."""
        return self._realizer

    @property
    def state(self) -> WorkspaceState | None:
        """Return the authoritative logical WorkspaceState."""
        return self._manager.state

    @property
    def active_workspace_id(self) -> str | None:
        """Return the active workspace identifier."""
        return self._manager.active_workspace_id

    @property
    def realized_layout(self) -> WorkspaceLayout | None:
        """Return the last successfully realized layout."""
        return self._realizer.realized_layout

    def activate(self, workspace_id: str) -> WorkspaceState:
        """Prepare, realize, and commit a workspace activation."""
        candidate = self._manager.prepare_activate(workspace_id)
        self._realizer.realize(candidate.layout)
        return self._manager.commit(candidate)

    def apply_layout(self, layout: WorkspaceLayout) -> WorkspaceState:
        """Prepare, realize, and commit a layout change."""
        candidate = self._manager.prepare_layout_change(layout)
        self._realizer.realize(candidate.layout)
        return self._manager.commit(candidate)

    def reset(self) -> WorkspaceState:
        """Prepare, realize, and commit the default workspace."""
        candidate = self._manager.prepare_reset()
        self._realizer.realize(candidate.layout)
        return self._manager.commit(candidate)


__all__ = ["WorkspaceController"]
