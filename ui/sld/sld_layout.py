# ============================================================
# File: ui/sld/sld_layout.py
# GridForge V2 — SLD Layout Boundary
# Author: Subhendu Mishra
# ============================================================

"""Presentation-only SLD layout policy.

SLDLayout calculates or converts visual placements. It does not store saved
node geometry. Persistent graphical position belongs to SLDDocument/SLDModel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class SLDPlacement:
    """Immutable presentation placement keyed by stable object identity."""

    object_id: str
    x: float
    y: float

    def __post_init__(self) -> None:
        if not isinstance(self.object_id, str) or not self.object_id.strip():
            raise ValueError("object_id must be a non-empty string")
        if isinstance(self.x, bool) or not isinstance(self.x, (int, float)):
            raise TypeError("x must be numeric")
        if isinstance(self.y, bool) or not isinstance(self.y, (int, float)):
            raise TypeError("y must be numeric")


class SLDLayout:
    """Provide deterministic, derived SLD presentation geometry."""

    def arrange(self, object_ids: Iterable[str]) -> tuple[SLDPlacement, ...]:
        """Create deterministic placeholder geometry for dummy rendering."""
        return tuple(
            SLDPlacement(str(object_id), float(index * 160), 0.0)
            for index, object_id in enumerate(object_ids)
        )

    def apply(
        self,
        positions: Mapping[str, tuple[float, float]],
    ) -> tuple[SLDPlacement, ...]:
        """Convert externally supplied geometry into immutable placements."""
        return tuple(
            SLDPlacement(str(object_id), position[0], position[1])
            for object_id, position in positions.items()
        )


__all__ = ["SLDLayout", "SLDPlacement"]
