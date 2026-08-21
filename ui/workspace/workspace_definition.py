# ============================================================
# GridForge V2
# ============================================================
#
# File:
#     ui/workspace/workspace_definition.py
#
# Purpose:
#     Immutable, Qt-independent logical Workspace definitions.
#
# Architectural boundary:
#     This module defines Workspace intent only.
#
# It does NOT:
#     - create Qt widgets;
#     - access QMainWindow;
#     - create docks;
#     - realize layouts;
#     - own panels;
#     - manage plugin lifecycle;
#     - activate Workspaces.
#
# ============================================================

"""
GridForge V2 — Workspace Definition.

Defines the immutable logical structures consumed by the
WorkspaceManager and WorkspaceLayout.

A WorkspaceDefinition describes:

    - Workspace identity;
    - Workspace title;
    - logical panel/editor placements;
    - panel area;
    - optional logical grouping;
    - visibility;
    - ordering;
    - optional metadata.

No Qt dependency is permitted in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .panel_area import PanelArea


# ============================================================
# Workspace Placement
# ============================================================


@dataclass(frozen=True, slots=True)
class WorkspacePlacement:
    """
    Immutable logical placement of one panel/editor.

    Placement describes Workspace policy only. It does not own
    or construct the corresponding panel.
    """

    panel_id: str
    area: PanelArea
    group: str | None = None
    visible: bool = True
    order: int = 0

    def __post_init__(self) -> None:
        """Validate the logical placement."""

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


# ============================================================
# Workspace Definition
# ============================================================


@dataclass(frozen=True, slots=True)
class WorkspaceDefinition:
    """
    Immutable description of one named GridForge Workspace.

    The definition contains logical intent only. It contains no
    Qt state and performs no realization.
    """

    workspace_id: str
    title: str
    placements: tuple[
        WorkspacePlacement,
        ...
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
        """Validate the logical Workspace definition."""

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


# ============================================================
# Public API
# ============================================================


__all__ = [
    "WorkspaceDefinition",
    "WorkspacePlacement",
]
