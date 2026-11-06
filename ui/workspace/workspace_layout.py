# ============================================================
# File: ui/workspace/workspace_layout.py
# GridForge V2 — Workspace Layout
# Author: Subhendu Mishra
# ============================================================

"""Immutable canonical Area-based workspace arrangement."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .area import AreaDefinition


@dataclass(frozen=True, slots=True)
class WorkspaceLayout:
    """Runtime layout containing only canonical Areas."""

    areas: tuple[AreaDefinition, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.areas, tuple):
            raise TypeError("areas must be a tuple.")
        seen: set[str] = set()
        for area in self.areas:
            if not isinstance(area, AreaDefinition):
                raise TypeError("areas must contain AreaDefinition objects.")
            if area.area_id in seen:
                raise ValueError(f"Duplicate workspace area: {area.area_id!r}")
            seen.add(area.area_id)

    @classmethod
    def from_areas(cls, areas: Iterable[AreaDefinition]) -> "WorkspaceLayout":
        return cls(areas=tuple(areas))

    def editor_areas(self) -> tuple[AreaDefinition, ...]:
        return self.areas

    def get_area(self, area_id: str) -> AreaDefinition | None:
        return next((item for item in self.areas if item.area_id == area_id), None)

    def with_area(self, area: AreaDefinition) -> "WorkspaceLayout":
        updated = [item for item in self.areas if item.area_id != area.area_id]
        updated.append(area)
        return WorkspaceLayout(areas=tuple(updated))

    def without_area(self, area_id: str) -> "WorkspaceLayout":
        return WorkspaceLayout(areas=tuple(item for item in self.areas if item.area_id != area_id))


__all__ = ["WorkspaceLayout"]
