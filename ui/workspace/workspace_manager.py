# ============================================================
# File: ui/workspace/workspace_manager.py
# GridForge V2 — Workspace Manager
# Author: Subhendu Mishra
# ============================================================

"""Toolkit-independent owner of logical Workspace lifecycle.

WorkspaceManager owns workspace definitions and authoritative logical
WorkspaceState. Qt realization is deliberately outside this class.
"""

from __future__ import annotations

from typing import Mapping

from .workspace_definition import WorkspaceDefinition
from .workspace_layout import WorkspaceLayout
from .workspace_state import WorkspaceState


class WorkspaceManager:
    """Manage named logical workspaces and their active state."""

    def __init__(self, definitions: Mapping[str, WorkspaceDefinition] | None = None) -> None:
        self._definitions: dict[str, WorkspaceDefinition] = {}
        self._active_workspace_id: str | None = None
        self._state: WorkspaceState | None = None
        if definitions is not None:
            if not isinstance(definitions, Mapping):
                raise TypeError("definitions must be a mapping.")
            for workspace_id, definition in definitions.items():
                if not isinstance(workspace_id, str):
                    raise TypeError("definition mapping keys must be strings.")
                if not isinstance(definition, WorkspaceDefinition):
                    raise TypeError("definition mapping values must be WorkspaceDefinition objects.")
                if workspace_id != definition.workspace_id:
                    raise ValueError("definition mapping key must match definition.workspace_id.")
                self.register(definition)

    @property
    def active_workspace_id(self) -> str | None:
        return self._active_workspace_id

    @property
    def state(self) -> WorkspaceState | None:
        return self._state

    @property
    def definitions(self) -> Mapping[str, WorkspaceDefinition]:
        return dict(self._definitions)

    def register(self, definition: WorkspaceDefinition) -> None:
        if not isinstance(definition, WorkspaceDefinition):
            raise TypeError("definition must be WorkspaceDefinition.")
        if definition.workspace_id in self._definitions:
            raise ValueError(f"Workspace already registered: {definition.workspace_id!r}")
        self._definitions[definition.workspace_id] = definition

    def unregister(self, workspace_id: str) -> WorkspaceDefinition | None:
        self._validate_workspace_id(workspace_id)
        if workspace_id == self._active_workspace_id:
            raise RuntimeError("Cannot unregister the active workspace.")
        return self._definitions.pop(workspace_id, None)

    def get(self, workspace_id: str) -> WorkspaceDefinition | None:
        self._validate_workspace_id(workspace_id)
        return self._definitions.get(workspace_id)

    def contains(self, workspace_id: str) -> bool:
        self._validate_workspace_id(workspace_id)
        return workspace_id in self._definitions

    def prepare_activate(self, workspace_id: str) -> WorkspaceState:
        self._validate_workspace_id(workspace_id)
        definition = self._definitions.get(workspace_id)
        if definition is None:
            raise KeyError(f"Unknown workspace: {workspace_id!r}")
        return WorkspaceState(
            workspace_id=definition.workspace_id,
            layout=WorkspaceLayout(placements=definition.placements),
        )

    def prepare_layout(self, layout: WorkspaceLayout) -> WorkspaceState:
        if not isinstance(layout, WorkspaceLayout):
            raise TypeError("layout must be a WorkspaceLayout.")
        if self._active_workspace_id is None:
            raise RuntimeError("No workspace is currently active.")
        return WorkspaceState(workspace_id=self._active_workspace_id, layout=layout)

    def prepare_reset_active(self) -> WorkspaceState:
        if self._active_workspace_id is None:
            raise RuntimeError("No workspace is currently active.")
        return self.prepare_activate(self._active_workspace_id)

    def commit(self, state: WorkspaceState) -> WorkspaceState:
        if not isinstance(state, WorkspaceState):
            raise TypeError("state must be a WorkspaceState.")
        workspace_id = state.workspace_id
        if workspace_id not in self._definitions:
            raise KeyError(f"Cannot commit unknown workspace: {workspace_id!r}")
        if self._active_workspace_id is not None and workspace_id != self._active_workspace_id:
            raise ValueError(
                f"Cannot commit a state for workspace {workspace_id!r} while "
                f"{self._active_workspace_id!r} is active."
            )
        self._active_workspace_id = workspace_id
        self._state = state
        return state

    def activate(self, workspace_id: str) -> WorkspaceState:
        return self.commit(self.prepare_activate(workspace_id))

    def set_layout(self, layout: WorkspaceLayout) -> WorkspaceState:
        return self.commit(self.prepare_layout(layout))

    def reset_active(self) -> WorkspaceState:
        return self.commit(self.prepare_reset_active())

    @staticmethod
    def _validate_workspace_id(workspace_id: str) -> None:
        if not isinstance(workspace_id, str):
            raise TypeError("workspace_id must be a string.")
        if not workspace_id.strip():
            raise ValueError("workspace_id must not be empty.")


__all__ = ["WorkspaceManager"]
