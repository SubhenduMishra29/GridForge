# ============================================================
# File: ui/workspace/workspace_definition.py
# GridForge V2 — Workspace Definition
# Author: Subhendu Mishra
# ============================================================

"""Immutable, Qt-independent workspace intent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .area import AreaDefinition
from .editor import EditorDefinition
from .panel_area import PanelArea


@dataclass(frozen=True, slots=True)
class WorkspacePlacement:
    """Legacy-compatible logical placement retained during migration."""

    panel_id: str
    area: PanelArea
    group: str | None = None
    visible: bool = True
    order: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.panel_id, str) or not self.panel_id.strip():
            raise ValueError("panel_id must be a non-empty string.")
        if not isinstance(self.area, PanelArea):
            raise TypeError("area must be a PanelArea.")
        if self.group is not None and (not isinstance(self.group, str) or not self.group.strip()):
            raise ValueError("group must be a non-empty string or None.")
        if not isinstance(self.visible, bool):
            raise TypeError("visible must be bool.")
        if not isinstance(self.order, int):
            raise TypeError("order must be int.")


@dataclass(frozen=True, slots=True)
class WorkspaceDefinition:
    """Immutable Workspace policy expressed as Areas/Editors plus compatibility placements."""

    workspace_id: str
    title: str
    placements: tuple[WorkspacePlacement, ...] = field(default_factory=tuple)
    areas: tuple[AreaDefinition, ...] = field(default_factory=tuple)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.workspace_id, str) or not self.workspace_id.strip():
            raise ValueError("workspace_id must be a non-empty string.")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string.")
        if not isinstance(self.placements, tuple):
            raise TypeError("placements must be a tuple.")
        if not isinstance(self.areas, tuple):
            raise TypeError("areas must be a tuple.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        placement_ids = set()
        for placement in self.placements:
            if not isinstance(placement, WorkspacePlacement):
                raise TypeError("placements must contain WorkspacePlacement objects.")
            if placement.panel_id in placement_ids:
                raise ValueError(f"Duplicate workspace placement: {placement.panel_id!r}")
            placement_ids.add(placement.panel_id)
        area_ids = set()
        for area in self.areas:
            if not isinstance(area, AreaDefinition):
                raise TypeError("areas must contain AreaDefinition objects.")
            if area.area_id in area_ids:
                raise ValueError(f"Duplicate workspace area: {area.area_id!r}")
            area_ids.add(area.area_id)

    def editor_definitions(self) -> tuple[EditorDefinition, ...]:
        """Return the immutable editor definitions hosted by this workspace."""
        return tuple(area.editor for area in self.areas)


__all__ = ["WorkspaceDefinition", "WorkspacePlacement", "AreaDefinition", "EditorDefinition"]
