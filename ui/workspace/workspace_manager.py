"""
GridForge V2 — Workspace Manager.

Coordinates workspace definitions and logical workspace state.

This class does NOT:
    - create panels;
    - create Qt widgets;
    - manipulate QMainWindow;
    - call addDockWidget();
    - call tabifyDockWidget();
    - decide electrical semantics;
    - modify Core state.

It is the workspace policy boundary.
"""

from __future__ import annotations

from typing import Iterable

from .workspace_definition import WorkspaceDefinition
from .workspace_layout import WorkspaceLayout
from .workspace_state import WorkspaceState


class WorkspaceManager:
    """
    Registry and coordinator for GridForge workspaces.
    """

    def __init__(self) -> None:
        self._definitions: dict[
            str,
            WorkspaceDefinition,
        ] = {}

        self._state: WorkspaceState | None = None

    # ========================================================
    # Definitions
    # ========================================================

    def register(
        self,
        definition: WorkspaceDefinition,
        *,
        replace: bool = False,
    ) -> None:
        """
        Register a workspace definition.
        """

        if not isinstance(
            definition,
            WorkspaceDefinition,
        ):
            raise TypeError(
                "definition must be a "
                "WorkspaceDefinition."
            )

        workspace_id = definition.workspace_id

        if (
            workspace_id in self._definitions
            and not replace
        ):
            raise ValueError(
                f"Workspace already registered: "
                f"{workspace_id!r}"
            )

        self._definitions[
            workspace_id
        ] = definition

    # --------------------------------------------------------

    def unregister(
        self,
        workspace_id: str,
    ) -> WorkspaceDefinition | None:
        """
        Remove a workspace definition.

        This does not modify Qt state.
        """

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
        Return a workspace definition.
        """

        return self._definitions.get(
            workspace_id
        )

    # --------------------------------------------------------

    def require(
        self,
        workspace_id: str,
    ) -> WorkspaceDefinition:
        """
        Return a workspace definition or raise KeyError.
        """

        definition = self.get(
            workspace_id
        )

        if definition is None:
            raise KeyError(
                f"Workspace is not registered: "
                f"{workspace_id!r}"
            )

        return definition

    # --------------------------------------------------------

    @property
    def workspace_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return registered workspace IDs.
        """

        return tuple(
            self._definitions.keys()
        )

    # ========================================================
    # Activation
    # ========================================================

    def activate(
        self,
        workspace_id: str,
    ) -> WorkspaceState:
        """
        Activate a registered workspace.

        Activation changes only logical workspace state.

        Qt realization is deliberately outside this class.
        """

        definition = self.require(
            workspace_id
        )

        layout = WorkspaceLayout.from_placements(
            definition.placements
        )

        self._state = WorkspaceState(
            workspace_id=definition.workspace_id,
            layout=layout,
        )

        return self._state

    # --------------------------------------------------------

    @property
    def state(
        self,
    ) -> WorkspaceState | None:
        """
        Return the current logical workspace state.
        """

        return self._state

    # --------------------------------------------------------

    @property
    def active_workspace_id(
        self,
    ) -> str | None:
        """
        Return the active workspace ID.
        """

        if self._state is None:
            return None

        return self._state.workspace_id

    # ========================================================
    # Layout Mutation
    # ========================================================

    def set_layout(
        self,
        layout: WorkspaceLayout,
    ) -> WorkspaceState:
        """
        Replace the active workspace layout.

        Does not perform Qt operations.
        """

        if not isinstance(
            layout,
            WorkspaceLayout,
        ):
            raise TypeError(
                "layout must be a WorkspaceLayout."
            )

        if self._state is None:
            raise RuntimeError(
                "No workspace is active."
            )

        self._state = WorkspaceState(
            workspace_id=self._state.workspace_id,
            layout=layout,
        )

        return self._state

    # ========================================================
    # Reset
    # ========================================================

    def reset_active_workspace(
        self,
    ) -> WorkspaceState:
        """
        Restore the active workspace definition.
        """

        if self._state is None:
            raise RuntimeError(
                "No workspace is active."
            )

        return self.activate(
            self._state.workspace_id
        )

    # ========================================================
    # Clear
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all workspace definitions and state.
        """

        self._definitions.clear()
        self._state = None


__all__ = [
    "WorkspaceManager",
]
