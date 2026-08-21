# ============================================================

# File: ui/workspace/workspace_controller.py

# GridForge V2 — Workspace Controller

# ============================================================

"""
GridForge V2 — Workspace Controller.

Application-level orchestration boundary for the Workspace
subsystem.

## Architectural role

WorkspaceManager
Owns logical workspace definitions and WorkspaceState.

WorkspaceLayout
Represents the immutable logical arrangement.

WorkspaceRealizer
Translates WorkspaceLayout into operations on the existing
MainWindow host.

WorkspaceController
Coordinates WorkspaceManager and WorkspaceRealizer.

The controller deliberately contains orchestration only.

It does NOT:

```
- create MainWindow;
- create QDockWidget;
- import Qt;
- create panels;
- register panels;
- define workspace policy;
- construct WorkspaceDefinition;
- construct WorkspaceLayout;
- modify Core/domain state;
- perform electrical calculations;
- perform direct Qt operations;
- know PanelArea realization rules.
```

The composition root is responsible for constructing this
controller and injecting the already-created Manager and
Realizer.
"""

from **future** import annotations

from .workspace_layout import WorkspaceLayout
from .workspace_manager import WorkspaceManager
from .workspace_realizer import WorkspaceRealizer
from .workspace_state import WorkspaceState

# ============================================================

# Workspace Controller

# ============================================================

class WorkspaceController:
"""
Coordinate logical Workspace state with its realization.

```
The controller does not own either subsystem. It coordinates
the explicitly supplied WorkspaceManager and
WorkspaceRealizer.
"""

def __init__(
    self,
    *,
    manager: WorkspaceManager,
    realizer: WorkspaceRealizer,
) -> None:
    """
    Construct the Workspace orchestration boundary.

    Parameters
    ----------
    manager:
        Existing WorkspaceManager responsible for logical
        workspace state.

    realizer:
        Existing WorkspaceRealizer responsible for translating
        logical layout into MainWindow host operations.
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
    """
    Return the explicitly supplied WorkspaceManager.
    """

    return self._manager

@property
def realizer(
    self,
) -> WorkspaceRealizer:
    """
    Return the explicitly supplied WorkspaceRealizer.
    """

    return self._realizer

@property
def state(
    self,
) -> WorkspaceState | None:
    """
    Return the current logical WorkspaceState.

    No realization is performed.
    """

    return self._manager.state

@property
def active_workspace_id(
    self,
) -> str | None:
    """
    Return the active workspace identifier.
    """

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
# Workspace Activation
# ========================================================

def activate(
    self,
    workspace_id: str,
) -> WorkspaceState:
    """
    Activate and realize a named workspace.

    Sequence
    --------
    1. WorkspaceManager activates the logical workspace.
    2. WorkspaceManager produces WorkspaceState.
    3. WorkspaceController obtains WorkspaceLayout.
    4. WorkspaceRealizer realizes that layout.
    5. The resulting WorkspaceState is returned.

    WorkspaceManager remains the logical authority.
    WorkspaceRealizer remains the Qt realization authority.
    """

    state = self._manager.activate(
        workspace_id
    )

    self._realizer.realize(
        state.layout
    )

    return state

# ========================================================
# Layout Update
# ========================================================

def set_layout(
    self,
    layout: WorkspaceLayout,
) -> WorkspaceState:
    """
    Set and realize a new logical layout.

    WorkspaceManager remains responsible for changing the
    logical WorkspaceState.

    WorkspaceRealizer remains responsible for realization.
    """

    if not isinstance(
        layout,
        WorkspaceLayout,
    ):
        raise TypeError(
            "layout must be a WorkspaceLayout."
        )

    state = self._manager.set_layout(
        layout
    )

    self._realizer.realize(
        state.layout
    )

    return state

# ========================================================
# Reset
# ========================================================

def reset_active(
    self,
) -> WorkspaceState:
    """
    Restore and realize the active workspace's definition
    layout.
    """

    state = self._manager.reset_active()

    self._realizer.realize(
        state.layout
    )

    return state
```

# ============================================================

# Public API

# ============================================================

**all** = [
"WorkspaceController",
]
