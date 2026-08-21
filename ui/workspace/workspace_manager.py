```python
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

Logical transitions use a two-phase model:

    prepare_*()
        ↓
    candidate WorkspaceState
        ↓
    external realization
        ↓
    commit(candidate)
        ↓
    authoritative logical state

If external realization fails, commit() is not called and the
manager's authoritative logical state remains unchanged.
"""

from __future__ import annotations

from typing import Mapping

from .workspace_definition import WorkspaceDefinition
from .workspace_layout import WorkspaceLayout
from .workspace_state import WorkspaceState


class WorkspaceManager:
    """
    Manage named logical workspaces.

    This class is completely toolkit-independent.
    """

    def __init__(
        self,
        definitions: Mapping[str, WorkspaceDefinition] | None = None,
    ) -> None:
        self._definitions: dict[str, WorkspaceDefinition] = {}
        self._active_workspace_id: str | None = None
        self._state: WorkspaceState | None = None

        if definitions is not None:
            if not isinstance(definitions, Mapping):
                raise TypeError(
                    "definitions must be a mapping."
                )

            for workspace_id, definition in definitions.items():
                if not isinstance(workspace_id, str):
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

                if workspace_id != definition.workspace_id:
                    raise ValueError(
                        "definition mapping key must match "
                        "definition.workspace_id."
                    )

                self.register(definition)

    # ========================================================
    # Properties
    # ========================================================

    @property
    def active_workspace_id(self) -> str | None:
        """Return the active workspace identifier."""

        return self._active_workspace_id

    @property
    def state(self) -> WorkspaceState | None:
        """Return the current authoritative logical state."""

        return self._state

    @property
    def definitions(
        self,
    ) -> Mapping[str, WorkspaceDefinition]:
        """
        Return a defensive copy of the workspace definitions.
        """

        return dict(self._definitions)

    # ========================================================
    # Registration
    # ========================================================

    def register(
        self,
        definition: WorkspaceDefinition,
    ) -> None:
        """Register one workspace definition."""

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
                f"Workspace already registered: {workspace_id!r}"
            )

        self._definitions[workspace_id] = definition

    def unregister(
        self,
        workspace_id: str,
    ) -> WorkspaceDefinition | None:
        """
        Unregister a workspace definition.

        The active workspace cannot be removed.
        """

        self._validate_workspace_id(workspace_id)

        if workspace_id == self._active_workspace_id:
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
        """Return a registered workspace definition."""

        self._validate_workspace_id(workspace_id)

        return self._definitions.get(workspace_id)

    def contains(
        self,
        workspace_id: str,
    ) -> bool:
        """Return whether a workspace is registered."""

        self._validate_workspace_id(workspace_id)

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

        No authoritative manager state is changed.
        """

        self._validate_workspace_id(workspace_id)

        definition = self._definitions.get(workspace_id)

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
        Prepare a replacement layout for the active workspace.

        No authoritative manager state is changed.
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
    # Preparation — Reset
    # ========================================================

    def prepare_reset_active(
        self,
    ) -> WorkspaceState:
        """
        Prepare restoration of the active workspace definition.

        No authoritative manager state is changed.
        """

        if self._active_workspace_id is None:
            raise RuntimeError(
                "No workspace is currently active."
            )

        return self.prepare_activate(
            self._active_workspace_id
        )

    # ========================================================
    # Commit
    # ========================================================

    def commit(
        self,
        state: WorkspaceState,
    ) -> WorkspaceState:
        """
        Commit a previously prepared WorkspaceState.

        The state must belong to a registered workspace.

        If a workspace is already active, the committed state
        must belong to that same workspace.
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

        if (
            self._active_workspace_id is not None
            and workspace_id != self._active_workspace_id
        ):
            raise ValueError(
                "Cannot commit a state for workspace "
                f"{workspace_id!r} while "
                f"{self._active_workspace_id!r} is active."
            )

        self._active_workspace_id = workspace_id
        self._state = state

        return state

    # ========================================================
    # Logical Convenience API
    # ========================================================

    def activate(
        self,
        workspace_id: str,
    ) -> WorkspaceState:
        """
        Activate a workspace at the logical layer only.

        This method does not perform UI realization.

        Application-level orchestration should use:

            prepare_activate()
            realize()
            commit()
        """

        state = self.prepare_activate(
            workspace_id
        )

        return self.commit(state)

    def set_layout(
        self,
        layout: WorkspaceLayout,
    ) -> WorkspaceState:
        """
        Set a layout at the logical layer only.

        This method does not perform UI realization.

        Application-level orchestration should use:

            prepare_layout()
            realize()
            commit()
        """

        state = self.prepare_layout(
            layout
        )

        return self.commit(state)

    def reset_active(
        self,
    ) -> WorkspaceState:
        """
        Reset the active workspace at the logical layer only.

        This method does not perform UI realization.
        """

        state = self.prepare_reset_active()

        return self.commit(state)

    # ========================================================
    # Internal Validation
    # ========================================================

    @staticmethod
    def _validate_workspace_id(
        workspace_id: str,
    ) -> None:
        """Validate a workspace identifier."""

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


__all__ = [
    "WorkspaceManager",
]
```
