"""
GridForge V2 — Workspace Definition.

Describes a named workspace configuration.

A WorkspaceDefinition describes intent and composition.
It does not perform Qt operations.
"""
# ui/workspace/workspace_definition.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Tuple

from .panel_area import PanelArea


@dataclass(frozen=True, slots=True)
class WorkspacePlacement:
    """
    Logical placement of one panel/editor.

    This is workspace policy, not panel ownership.
    """

    panel_id: str
    area: PanelArea
    group: str | None = None
    visible: bool = True
    order: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.panel_id, str):
            raise TypeError("panel_id must be a string.")

        if not self.panel_id.strip():
            raise ValueError(
                "panel_id must not be empty."
            )

        if not isinstance(self.area, PanelArea):
            raise TypeError(
                "area must be a PanelArea."
            )

        if self.group is not None:
            if not isinstance(self.group, str):
                raise TypeError(
                    "group must be a string or None."
                )

            if not self.group.strip():
                raise ValueError(
                    "group must not be empty."
                )

        if not isinstance(self.visible, bool):
            raise TypeError(
                "visible must be a bool."
            )

        if not isinstance(self.order, int):
            raise TypeError(
                "order must be an int."
            )


@dataclass(frozen=True, slots=True)
class WorkspaceDefinition:
    """
    Immutable description of one named GridForge workspace.
    """

    workspace_id: str
    title: str
    placements: Tuple[WorkspacePlacement, ...] = field(
        default_factory=tuple
    )
    metadata: Mapping[str, object] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.workspace_id, str):
            raise TypeError(
                "workspace_id must be a string."
            )

        if not self.workspace_id.strip():
            raise ValueError(
                "workspace_id must not be empty."
            )

        if not isinstance(self.title, str):
            raise TypeError(
                "title must be a string."
            )

        if not isinstance(self.placements, tuple):
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


__all__ = [
    "WorkspaceDefinition",
    "WorkspacePlacement",
]
