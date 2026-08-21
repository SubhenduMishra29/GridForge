# ============================================================
# File: ui/workspace/workspace_manager.py
# GridForge V2 — Workspace Manager
# ============================================================

"""
GridForge V2 — Workspace Manager.

Owns named logical workspace definitions and the current
logical WorkspaceState.

Architectural boundary
----------------------

WorkspaceManager owns:

    - workspace definitions;
    - active workspace identity;
    - current logical WorkspaceState;
    - preparation of candidate WorkspaceState transitions;
    - commitment of validated logical state transitions.

WorkspaceManager does NOT own:

    - Qt;
    - QMainWindow;
    - QDockWidget;
    - panel creation;
    - dock placement;
    - dock visibility realization;
    - tabification;
    - MainWindow lifecycle;
    - WorkspaceRealizer.

Transaction boundary
--------------------

WorkspaceManager uses a two-phase logical transition model:

    prepare_*()
        ↓
    candidate WorkspaceState
        ↓
    external realization
        ↓
    commit(candidate)
        ↓
    authoritative logical state

The manager never performs realization itself.

This allows WorkspaceController to coordinate:

    WorkspaceManager
        →
    WorkspaceRealizer
        →
    WorkspaceManager.commit()

If realization fails, commit() is not called and the
manager's authoritative logical state remains unchanged.
"""

from __future__ import annotations

from typing import Mapping

from .workspace_definition import WorkspaceDefinition
from .workspace_layout import WorkspaceLayout
from .workspace_state import WorkspaceState


# ============================================================
# Workspace Manager
# ============================================================


class WorkspaceManager:
    """
    Coordinates named logical workspaces.

    The manager is deliberately toolkit-independent.

    Logical state is changed only through commit().
    prepare_*() methods create candidate states without
    mutating the manager's authoritative state.
    """

    def __init__(
        self,
        definitions: Mapping[
            str,
            WorkspaceDefinition,
        ] | None = None,
    ) -> None:
        """
        Construct a WorkspaceManager.

        Parameters
        ----------
        definitions:
            Optional mapping of workspace IDs to immutable
            WorkspaceDefinition objects.
        """

        self._definitions: dict[
            str,
            WorkspaceDefinition,
        ] = {}

        self._active_workspace_id: str | None = None

        self._state: WorkspaceState | None = None

        if definitions is not None:
            if not isinstance(
                definitions,
                Mapping,
            ):
                raise TypeError(
                    "definitions must be a mapping."
                )

            for workspace_id, definition in definitions.items():
                if not isinstance(
                    workspace_id,
                    str,
                ):
                    raise TypeError(
                        "definition mapping keys must be strings."
                    )

                if not isinstance(
                    definition,
                    WorkspaceDefinition,
                ):
                    raise TypeError(
                        "definition mapping values must be "
                        "WorkspaceDefinition objects."
                    )

                if (
                    workspace_id
                    != definition.workspace_id
                ):
                    raise ValueError(
                        "definition mapping key must match "
                        "definition.workspace_id."
                    )

                self.register(
                    definition
                )

    # ========================================================
    # Properties
    # ========================================================

    @property
    def active_workspace_id(
        self,
    ) -> str | None:
        """
        Return the active workspace identifier.
        """

        return self._active_workspace_id

    @property
    def state(
        self,
    ) -> WorkspaceState | None:
        """
        Return the current authoritative logical state.
        """

        return self._state

    @property
    def definitions(
        self,
    ) -> Mapping[
        str,
        WorkspaceDefinition,
    ]:
        """
        Return a defensive mapping copy of definitions.

        Callers cannot mutate the manager's internal registry.
        """

        return dict(
            self._definitions
        )

    # ========================================================
    # Registration
    # ========================================================

    def register(
        self,
        definition: WorkspaceDefinition,
    ) -> None:
        """
        Register one immutable workspace definition.
        """

        if not isinstance(
            definition,
            WorkspaceDefinition,
        ):
            raise TypeError(
                "definition must be WorkspaceDefinition."
            )

        workspace_id = definition.workspace_id

        if workspace_id in self._definitions:
            raise ValueError(
                f"Workspace already registered: "
                f"{workspace_id!r}"
            )

        self._definitions[
            workspace_id
        ] = definition

    def unregister(
        self,
        workspace_id: str,
    ) -> WorkspaceDefinition | None:
        """
        Unregister a workspace definition.

        The active workspace cannot be removed.
        """

        self._validate_workspace_id(
            workspace_id
        )

        if (
            workspace_id
            == self._active_workspace_id
        ):
            raise RuntimeError(
                "Cannot unregister the active workspace."
            )

        return self._definitions.pop(
            workspace_id,
            None,
        )

    # ========================================================
    # Lookup
    # ========================================================

    def get(
        self,
        workspace_id: str,
    ) -> WorkspaceDefinition | None:
        """
        Return a registered workspace definition.
        """

        self._validate_workspace_id(
            workspace_id
        )

        return self._definitions.get(
            workspace_id
        )

    def contains(
        self,
        workspace_id: str,
    ) -> bool:
        """
        Return whether a workspace is registered.
        """

        self._validate_workspace_id(
            workspace_id
        )

        return workspace_id in self._definitions

    # ========================================================
    # Preparation — Activation
    # ========================================================

    def prepare_activate(
        self,
        workspace_id: str,
    ) -> WorkspaceState:
        """
        Prepare activation of a registered workspace.

        This method does NOT mutate authoritative manager state.

        Returns
        -------
        WorkspaceState
            Candidate state to be realized externally and then
            committed with commit().
        """

        self._validate_workspace_id(
            workspace_id
        )

        definition = self._definitions.get(
            workspace_id
        )

        if definition is None:
            raise KeyError(
                f"Unknown workspace: {workspace_id!r}"
            )

        layout = WorkspaceLayout(
            placements=definition.placements
        )

        return WorkspaceState(
            workspace_id=definition.workspace_id,
            layout=layout,
        )

    # ========================================================
    # Preparation — Layout
    # ========================================================

    def prepare_layout(
        self,
        layout: WorkspaceLayout,
    ) -> WorkspaceState:
        """
        Prepare replacement of the active workspace layout.

        This method does NOT mutate authoritative manager state.

        Returns
        -------
        WorkspaceState
            Candidate state to be realized externally and then
            committed with commit().
        """

        if not isinstance(
            layout,
            WorkspaceLayout,
        ):
            raise TypeError(
                "layout must be a WorkspaceLayout."
            )

        if self._active_workspace_id is None:
            raise RuntimeError(
                "No workspace is currently active."
            )

        return WorkspaceState(
            workspace_id=self._active_workspace_id,
            layout=layout,
        )

    # ========================================================
    # Commit
    # ========================================================

    def commit(
        self,
        state: WorkspaceState,
    ) -> WorkspaceState:
        """
        Commit a prepared WorkspaceState.

        The state must belong to a registered workspace.

        For an existing active workspace, the candidate must
        preserve the active workspace identity.

        For a first activation, no active workspace exists and
        the candidate's workspace must be registered.

        No Qt or realization is performed here.
        """

        if not isinstance(
            state,
            WorkspaceState,
        ):
            raise TypeError(
                "state must be a WorkspaceState."
            )

        workspace_id = state.workspace_id

        if workspace_id not in self._definitions:
            raise KeyError(
                f"Cannot commit unknown workspace: "
                f"{workspace_id!r}"
            )

        if self._active_workspace_id is not None:
            if (
                workspace_id
                != self._active_workspace_id
            ):
                raise ValueError(
                    "Cannot commit a state for workspace "
                    f"{workspace_id!r} while "
                    f"{self._active_workspace_id!r} "
                    "is active."
                )

        self._active_workspace_id = workspace_id
        self._state = state

        return state

    # ========================================================
    # Compatibility Activation API
    # ========================================================

    def activate(
        self,
        workspace_id: str,
    ) -> WorkspaceState:
        """
        Activate a workspace immediately at the logical layer.

        This method is retained as the logical convenience API.

        It performs:

            prepare_activate()
                ↓
            commit()

        It performs NO Qt realization.

        Application-level orchestration should normally use
        prepare_activate() + external realization + commit().
        """

        state = self.prepare_activate(
            workspace_id
        )

        return self.commit(
            state
        )

    # ========================================================
    # Compatibility Layout API
    # ========================================================

    def set_layout(
        self,
        layout: WorkspaceLayout,
    ) -> WorkspaceState:
        """
        Replace the active workspace layout immediately at the
        logical layer.

        This method performs:

            prepare_layout()
                ↓
            commit()

        It performs NO Qt realization.

        Application-level orchestration should normally use
        prepare_layout() + external realization + commit().
        """

        state = self.prepare_layout(
            layout
        )

        return self.commit(
            state
        )

    # ========================================================
    # Reset Preparation
    # ========================================================

    def prepare_reset_active(
        self,
    ) -> WorkspaceState:
        """
        Prepare restoration of the active workspace's definition.

        No authoritative state is mutated.
        """

        if self._active_workspace_id is None:
            raise RuntimeError(
                "No workspace is currently active."
            )

        return self.prepare_activate(
            self._active_workspace_id
        )

    # ========================================================
    # Reset
    # ========================================================

    def reset_active(
        self,
    ) -> WorkspaceState:
        """
        Restore the active workspace immediately at the logical
        layer.

        No Qt realization is performed.
        """

        state = self.prepare_reset_active()

        return self.commit(
            state
        )

    # ========================================================
    # Internal Validation
    # ========================================================

    @staticmethod
    def _validate_workspace_id(
        workspace_id: str,
    ) -> None:
        """
        Validate a workspace identifier.
        """

        if not isinstance(
            workspace_id,
            str,
        ):
            raise TypeError(
                "workspace_id must be a string."
            )

        if not workspace_id.strip():
            raise ValueError(
                "workspace_id must not be empty."
            )


# ============================================================
# Public API
# ============================================================

__all__ = [
    "WorkspaceManager",
]
