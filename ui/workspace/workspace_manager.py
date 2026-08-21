# ============================================================

# File: ui/workspace/workspace_manager.py

# GridForge V2 — Workspace Manager

# ============================================================

"""
GridForge V2 — Workspace Manager.

Owns named logical workspace definitions and the current
logical WorkspaceState.

## Architectural boundary

WorkspaceManager owns:

```
- workspace definitions;
- active workspace identity;
- current logical WorkspaceLayout;
- immutable WorkspaceState transitions.
```

WorkspaceManager does NOT own:

```
- Qt;
- QMainWindow;
- QDockWidget;
- panel creation;
- dock placement;
- dock visibility realization;
- tabification;
- MainWindow lifecycle.
```

WorkspaceRealizer consumes the resulting WorkspaceLayout and
translates it into MainWindow host operations.
"""

from **future** import annotations

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

```
The manager is deliberately toolkit-independent.
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
            self.register(
                definition
            )

            if workspace_id != definition.workspace_id:
                raise ValueError(
                    "definition mapping key must match "
                    "definition.workspace_id."
                )

# ========================================================
# Properties
# ========================================================

@property
def active_workspace_id(
    self,
) -> str | None:
    """Return the active workspace identifier."""

    return self._active_workspace_id

@property
def state(
    self,
) -> WorkspaceState | None:
    """Return the current immutable logical workspace state."""

    return self._state

@property
def definitions(
    self,
) -> Mapping[
    str,
    WorkspaceDefinition,
]:
    """Return a read-only mapping view of definitions."""

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
    """Return a registered workspace definition."""

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
    """Return whether a workspace is registered."""

    self._validate_workspace_id(
        workspace_id
    )

    return workspace_id in self._definitions

# ========================================================
# Activation
# ========================================================

def activate(
    self,
    workspace_id: str,
) -> WorkspaceState:
    """
    Activate a registered workspace.

    Activation changes only logical state.

    Qt realization is intentionally outside this class.
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

    state = WorkspaceState(
        workspace_id=definition.workspace_id,
        layout=layout,
    )

    self._active_workspace_id = (
        definition.workspace_id
    )

    self._state = state

    return state

# ========================================================
# Layout
# ========================================================

def set_layout(
    self,
    layout: WorkspaceLayout,
) -> WorkspaceState:
    """
    Replace the active workspace layout.

    This changes logical state only.
    """

    if not isinstance(
        layout,
        WorkspaceLayout,
    ):
        raise TypeError(
            "layout must be WorkspaceLayout."
        )

    if self._active_workspace_id is None:
        raise RuntimeError(
            "No workspace is currently active."
        )

    state = WorkspaceState(
        workspace_id=self._active_workspace_id,
        layout=layout,
    )

    self._state = state

    return state

# ========================================================
# Reset
# ========================================================

def reset_active(
    self,
) -> WorkspaceState:
    """
    Restore the active workspace to its definition layout.
    """

    if self._active_workspace_id is None:
        raise RuntimeError(
            "No workspace is currently active."
        )

    return self.activate(
        self._active_workspace_id
    )

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
```

# ============================================================

# Public API

# ============================================================

**all** = [
"WorkspaceManager",
]
