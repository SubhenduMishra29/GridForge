# ============================================================
# File: ui/workspace/workspace_layout.py
# GridForge V2 — Workspace Layout
# Author: Subhendu Mishra
# ============================================================

"""Immutable logical workspace arrangement with Area/Editor composition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .area import AreaDefinition
from .panel_area import PanelArea
from .workspace_definition import WorkspacePlacement


@dataclass(frozen=True, slots=True)
class WorkspaceLayout:
    placements: tuple[WorkspacePlacement, ...] = field(default_factory=tuple)
    areas: tuple[AreaDefinition, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.placements, tuple):
            raise TypeError("placements must be a tuple.")
        if not isinstance(self.areas, tuple):
            raise TypeError("areas must be a tuple.")
        seen = set()
        for placement in self.placements:
            if not isinstance(placement, WorkspacePlacement):
                raise TypeError("placements must contain WorkspacePlacement objects.")
            if placement.panel_id in seen:
                raise ValueError(f"Duplicate workspace placement: {placement.panel_id!r}")
            seen.add(placement.panel_id)
        area_ids = set()
        for area in self.areas:
            if not isinstance(area, AreaDefinition):
                raise TypeError("areas must contain AreaDefinition objects.")
            if area.area_id in area_ids:
                raise ValueError(f"Duplicate workspace area: {area.area_id!r}")
            area_ids.add(area.area_id)

    @classmethod
    def from_placements(cls, placements: Iterable[WorkspacePlacement], *, areas: Iterable[AreaDefinition] = ()) -> "WorkspaceLayout":
        return cls(placements=tuple(placements), areas=tuple(areas))

    def editor_areas(self) -> tuple[AreaDefinition, ...]:
        return self.areas

    def get_area(self, panel_id: str) -> PanelArea | None:
        placement = self.get_placement(panel_id)
        return placement.area if placement is not None else None

    def get_placement(self, panel_id: str) -> WorkspacePlacement | None:
        return next((item for item in self.placements if item.panel_id == panel_id), None)

    def panels_in_area(self, area: PanelArea) -> tuple[WorkspacePlacement, ...]:
        return tuple(item for item in self.placements if item.area == area)

    def visible_panels(self) -> tuple[WorkspacePlacement, ...]:
        return tuple(item for item in self.placements if item.visible)

    def with_placement(self, placement: WorkspacePlacement) -> "WorkspaceLayout":
        updated = [item for item in self.placements if item.panel_id != placement.panel_id]
        updated.append(placement)
        return WorkspaceLayout(placements=tuple(updated), areas=self.areas)

    def without_panel(self, panel_id: str) -> "WorkspaceLayout":
        return WorkspaceLayout(
            placements=tuple(item for item in self.placements if item.panel_id != panel_id),
            areas=self.areas,
        )


__all__ = ["WorkspaceLayout"]
