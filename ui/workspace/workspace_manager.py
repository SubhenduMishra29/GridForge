# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/workspace/workspace_manager.py
#
# Purpose:
#     Manages multiple GridForge workspaces.
#
# Architectural Role:
#     Provides the application-level workspace lifecycle boundary.
#
# Responsibilities:
#     - register workspaces;
#     - remove workspaces;
#     - activate a workspace;
#     - retrieve the active workspace.
#
# Does NOT:
#     - create Qt widgets;
#     - manage docks;
#     - render canvases.
#
# ============================================================

"""
GridForge V2 — Workspace Manager.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .workspace import Workspace


class WorkspaceManager:
    """
    Application-level registry of GridForge workspaces.
    """

    def __init__(self) -> None:
        self._workspaces: Dict[
            str,
            Workspace,
        ] = {}

        self._active_workspace_id: Optional[
            str
        ] = None

    @property
    def active_workspace_id(
        self,
    ) -> Optional[str]:
        return self._active_workspace_id

    @property
    def active_workspace(
        self,
    ) -> Optional[Workspace]:
        if self._active_workspace_id is None:
            return None

        return self._workspaces.get(
            self._active_workspace_id
        )

    def register(
        self,
        workspace: Workspace,
    ) -> None:
        if workspace.workspace_id in self._workspaces:
            raise ValueError(
                f"Workspace already registered: "
                f"{workspace.workspace_id}"
            )

        self._workspaces[
            workspace.workspace_id
        ] = workspace

        if self._active_workspace_id is None:
            self.activate(
                workspace.workspace_id
            )

    def unregister(
        self,
        workspace_id: str,
    ) -> Workspace:
        workspace = self._workspaces.pop(
            workspace_id,
            None,
        )

        if workspace is None:
            raise KeyError(workspace_id)

        if (
            self._active_workspace_id
            == workspace_id
        ):
            workspace.close()

            self._active_workspace_id = None

            if self._workspaces:
                self._active_workspace_id = next(
                    iter(self._workspaces)
                )

        return workspace

    def get(
        self,
        workspace_id: str,
    ) -> Optional[Workspace]:
        return self._workspaces.get(
            workspace_id
        )

    def require(
        self,
        workspace_id: str,
    ) -> Workspace:
        workspace = self.get(
            workspace_id
        )

        if workspace is None:
            raise KeyError(workspace_id)

        return workspace

    def activate(
        self,
        workspace_id: str,
    ) -> Workspace:
        workspace = self.require(
            workspace_id
        )

        self._active_workspace_id = (
            workspace_id
        )

        return workspace

    def workspaces(
        self,
    ) -> Iterable[Workspace]:
        return tuple(
            self._workspaces.values()
        )

    def clear(self) -> None:
        for workspace in self._workspaces.values():
            workspace.close()

        self._workspaces.clear()
        self._active_workspace_id = None

    def __len__(self) -> int:
        return len(self._workspaces)
