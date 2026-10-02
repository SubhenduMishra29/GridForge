# ============================================================
# File: ui/workspace/region.py
# GridForge V2 — Editor Region Contract
# Author: Subhendu Mishra
# ============================================================

"""Qt-independent logical regions used to compose engineering editors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegionDefinition:
    """Describe one lightweight presentation region."""

    region_id: str
    region_type: str
    visible: bool = True
    enabled: bool = True
    minimum_size: int = 0
    preferred_size: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.region_id, str) or not self.region_id.strip():
            raise ValueError("region_id must be a non-empty string.")
        if not isinstance(self.region_type, str) or not self.region_type.strip():
            raise ValueError("region_type must be a non-empty string.")
        if not isinstance(self.visible, bool) or not isinstance(self.enabled, bool):
            raise TypeError("visible and enabled must be bool.")
        if not isinstance(self.minimum_size, int) or self.minimum_size < 0:
            raise ValueError("minimum_size must be a non-negative int.")
        if self.preferred_size is not None and (
            not isinstance(self.preferred_size, int) or self.preferred_size < self.minimum_size
        ):
            raise ValueError("preferred_size must be None or >= minimum_size.")


HEADER_REGION = "header"
TOOL_SHELF_REGION = "tool_shelf"
CANVAS_REGION = "canvas"
SIDEBAR_REGION = "sidebar"
OVERLAY_REGION = "overlay"
STATUS_REGION = "status"
DIAGNOSTICS_REGION = "diagnostics"


__all__ = [
    "RegionDefinition",
    "HEADER_REGION",
    "TOOL_SHELF_REGION",
    "CANVAS_REGION",
    "SIDEBAR_REGION",
    "OVERLAY_REGION",
    "STATUS_REGION",
    "DIAGNOSTICS_REGION",
]
