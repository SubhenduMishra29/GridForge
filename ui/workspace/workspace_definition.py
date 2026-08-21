# ============================================================

# File: ui/workspace/workspace_definition.py

# GridForge V2 — Workspace Definition

# ============================================================

"""
GridForge V2 — Workspace Definition.

Describes a named workspace configuration.

WorkspaceDefinition describes workspace intent and composition.
It is immutable, Qt-independent, and performs no UI operations.

WorkspaceDefinition owns workspace policy such as:

```
- workspace identity;
- workspace title;
- panel/editor placement;
- logical PanelArea;
- grouping;
- visibility;
- ordering.
```

It does NOT own:

```
- Qt widgets;
- QMainWindow;
- dock creation;
- dock realization;
- panel ownership;
- plugin lifecycle.
```

"""

from **future** import annotations

from dataclasses import dataclass, field
from typing import Mapping, Tuple

from .panel_area import PanelArea

# ============================================================

# Workspace Placement

# ============================================================

@dataclass(frozen=True, slots=True)
class WorkspacePlacement:
"""
Logical placement of one panel/editor.

```
This is workspace policy, not panel ownership.

Placement information is intentionally kept outside
PanelSpec / PanelsPlugin.
"""

panel_id: str

area: PanelArea

group: str | None = None

visible: bool = True

order: int = 0

def __post_init__(self) -> None:
    if not isinstance(
        self.panel_id,
        str,
    ):
        raise TypeError(
            "panel_id must be a string."
        )

    if not self.panel_id.strip():
        raise ValueError(
            "panel_id must not be empty."
        )

    if not isinstance(
        self.area,
        PanelArea,
    ):
        raise TypeError(
            "area must be a PanelArea."
        )

    if self.group is not None:
        if not isinstance(
            self.group,
            str,
        ):
            raise TypeError(
                "group must be a string or None."
            )

        if not self.group.strip():
            raise ValueError(
                "group must not be empty."
            )

    if not isinstance(
        self.visible,
        bool,
    ):
        raise TypeError(
            "visible must be a bool."
        )

    if not isinstance(
        self.order,
        int,
    ):
        raise TypeError(
            "order must be an int."
        )
```

# ============================================================

# Workspace Definition

# ============================================================

@dataclass(frozen=True, slots=True)
class WorkspaceDefinition:
"""
Immutable description of one named GridForge workspace.

```
A definition describes logical workspace intent only.

It contains no Qt state and performs no realization.
"""

workspace_id: str

title: str

placements: Tuple[
    WorkspacePlacement,
    ...,
] = field(
    default_factory=tuple
)

metadata: Mapping[
    str,
    object,
] = field(
    default_factory=dict
)

def __post_init__(self) -> None:
    if not isinstance(
        self.workspace_id,
        str,
    ):
        raise TypeError(
            "workspace_id must be a string."
        )

    if not self.workspace_id.strip():
        raise ValueError(
            "workspace_id must not be empty."
        )

    if not isinstance(
        self.title,
        str,
    ):
        raise TypeError(
            "title must be a string."
        )

    if not self.title.strip():
        raise ValueError(
            "title must not be empty."
        )

    if not isinstance(
        self.placements,
        tuple,
    ):
        raise TypeError(
            "placements must be a tuple."
        )

    for placement in self.placements:
        if not isinstance(
            placement,
            WorkspacePlacement,
        ):
            raise TypeError(
                "placements must contain "
                "WorkspacePlacement objects."
            )

    if not isinstance(
        self.metadata,
        Mapping,
    ):
        raise TypeError(
            "metadata must be a mapping."
        )
```

# ============================================================

# Public API

# ============================================================

**all** = [
"WorkspaceDefinition",
"WorkspacePlacement",
]
