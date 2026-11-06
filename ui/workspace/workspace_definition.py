# ============================================================
# File: ui/workspace/workspace_definition.py
# GridForge V2 — Workspace Definition
# Author: Subhendu Mishra
# ============================================================

"""Immutable, Qt-independent canonical workspace intent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .area import AreaDefinition
from .editor import EditorDefinition


@dataclass(frozen=True, slots=True)
class WorkspaceDefinition:
    """Canonical workspace policy expressed only as ordered Areas."""

    workspace_id: str
    title: str
    areas: tuple[AreaDefinition, ...] = field(default_factory=tuple)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.workspace_id, str) or not self.workspace_id.strip():
            raise ValueError("workspace_id must be a non-empty string.")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string.")
        if not isinstance(self.areas, tuple):
            raise TypeError("areas must be a tuple.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        area_ids: set[str] = set()
        for area in self.areas:
            if not isinstance(area, AreaDefinition):
                raise TypeError("areas must contain AreaDefinition objects.")
            if area.area_id in area_ids:
                raise ValueError(f"Duplicate workspace area: {area.area_id!r}")
            area_ids.add(area.area_id)

    def editor_definitions(self) -> tuple[EditorDefinition, ...]:
        """Return the immutable editor definitions hosted by this workspace."""
        return tuple(area.editor for area in self.areas)


__all__ = ["WorkspaceDefinition", "AreaDefinition", "EditorDefinition"]
