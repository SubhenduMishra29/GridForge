# ============================================================
# File: ui/workspace/editor.py
# GridForge V2 — Engineering Editor Contract
# Author: Subhendu Mishra
# ============================================================

"""Qt-independent logical editor definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .region import RegionDefinition


@dataclass(frozen=True, slots=True)
class EditorDefinition:
    """Describe an engineering editor and its ordered regions."""

    editor_id: str
    editor_type: str
    title: str
    regions: tuple[RegionDefinition, ...] = field(default_factory=tuple)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (("editor_id", self.editor_id), ("editor_type", self.editor_type), ("title", self.title)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        if not isinstance(self.regions, tuple):
            raise TypeError("regions must be a tuple.")
        ids: set[str] = set()
        for region in self.regions:
            if not isinstance(region, RegionDefinition):
                raise TypeError("regions must contain RegionDefinition objects.")
            if region.region_id in ids:
                raise ValueError(f"Duplicate editor region: {region.region_id!r}")
            ids.add(region.region_id)
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")


SLD_EDITOR = "sld"
CONTROL_EDITOR = "control"
PROTECTION_EDITOR = "protection"
STUDY_EDITOR = "study"
EXPLORER_EDITOR = "explorer"
PROPERTIES_EDITOR = "properties"
DIAGNOSTICS_EDITOR = "diagnostics"
TIMELINE_EDITOR = "timeline"


__all__ = [
    "EditorDefinition",
    "SLD_EDITOR",
    "CONTROL_EDITOR",
    "PROTECTION_EDITOR",
    "STUDY_EDITOR",
    "EXPLORER_EDITOR",
    "PROPERTIES_EDITOR",
    "DIAGNOSTICS_EDITOR",
    "TIMELINE_EDITOR",
]
