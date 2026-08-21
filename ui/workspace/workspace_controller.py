```python
# ============================================================
# File: ui/workspace/workspace_controller.py
# GridForge V2 — Workspace Controller
# ============================================================

"""
GridForge V2 — Workspace Controller.

Application-level orchestration boundary for the Workspace
subsystem.

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
    """
    Coordinate logical Workspace state with UI realization.

    WorkspaceManager remains the logical authority.

    WorkspaceRealizer remains the realization authority.

    WorkspaceController owns neither subsystem; it only
    orchestrates their interaction.
    """

    def __init__(
        self,
        *,
        manager: WorkspaceManager,
        realizer: WorkspaceRealizer,
    ) -> None:
        """
        Construct the Workspace orchestration boundary.
        """

        if not isinstance(
            manager,
            WorkspaceManager,
        ):
            raise TypeError(
                "manager must be a WorkspaceManager."
            )

        if not isinstance(
            realizer,
            WorkspaceRealizer,
        ):
            raise TypeError(
                "realizer must be a WorkspaceRealizer."
            )

        self._manager = manager
        self._realizer = realizer

    # ========================================================
    # Properties
    # ========================================================

    @property
    def manager(
        self,
    ) -> WorkspaceManager:
        """Return the WorkspaceManager."""

        return self._manager

    @property
    def realizer(
        self,
    ) -> WorkspaceRealizer:
        """Return the WorkspaceRealizer."""

        return self._realizer

    @property
    def state(
        self,
    ) -> WorkspaceState | None:
        """
        Return the authoritative logical WorkspaceState.

        This does not trigger realization.
        """

        return self._manager.state

    @property
    def active_workspace_id(
        self,
    ) -> str | None:
        """Return the active workspace identifier."""

        return self._manager.active_workspace_id

    @property
    def realized_layout(
        self,
    ) -> WorkspaceLayout | None:
        """
        Return the last successfully realized layout.
        """

        return self._realizer.realized_layout

    # ========================================================
    # Activation
    # ========================================================

    def activate(
        self,
        workspace_id: str,
    ) -> WorkspaceState:
        """
        Prepare, realize, and commit a workspace activation.

        Transaction:

            manager.prepare_activate()
                    ↓
            realizer.realize()
                    ↓
            manager.commit()

        If realization fails, the manager is not committed.
        """

        candidate = self._manager.prepare_activate(
            workspace_id
        )

        self._realizer.realize(
            candidate.layout
        )

        return self._manager.commit(
            candidate
        )

    # ========================================================
    # Layout Update
    # ========================================================

    def set_layout(
        self,
        layout: WorkspaceLayout,
    ) -> WorkspaceState:
        """
        Prepare, realize, and commit a layout change.

        If realization fails, the manager's previous state
        remains authoritative.
        """

        if not isinstance(
            layout,
            WorkspaceLayout,
        ):
            raise TypeError(
                "layout must be a WorkspaceLayout."
            )

        candidate = self._manager.prepare_layout(
            layout
        )

        self._realizer.realize(
            candidate.layout
        )

        return self._manager.commit(
            candidate
        )

    # ========================================================
    # Reset
    # ========================================================

    def reset_active(
        self,
    ) -> WorkspaceState:
        """
        Prepare, realize, and commit restoration of the active
        workspace's definition layout.

        If realization fails, no logical state is committed.
        """

        candidate = self._manager.prepare_reset_active()

        self._realizer.realize(
            candidate.layout
        )

        return self._manager.commit(
            candidate
        )


# ============================================================
# Public API
# ============================================================

__all__ = [
    "WorkspaceController",
]
```
