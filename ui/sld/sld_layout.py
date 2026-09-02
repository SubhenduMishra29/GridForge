# ============================================================
# File: ui/sld/sld_layout.py
# GridForge V2 — SLD Layout Boundary
# Author: Subhendu Mishra
# ============================================================

"""Presentation-only geometry boundary for the SLD surface.

SLDLayout owns visual placement policy only. It does not own
engineering truth, Core mutation, viewport/navigation state, or
QGraphicsItem lifecycle. Canvas consumes these placements.
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
    """Store and produce deterministic SLD presentation geometry."""

    def __init__(self) -> None:
        self._positions: dict[str, tuple[float, float]] = {}

    def set_position(self, object_id: str, x: float, y: float) -> None:
        """Set presentation geometry without mutating Core state."""
        self._validate_id(object_id)
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError("x must be numeric")
        if isinstance(y, bool) or not isinstance(y, (int, float)):
            raise TypeError("y must be numeric")
        self._positions[object_id] = (float(x), float(y))

    def position(self, object_id: str) -> tuple[float, float] | None:
        """Return presentation geometry for an object."""
        self._validate_id(object_id)
        return self._positions.get(object_id)

    def remove(self, object_id: str) -> tuple[float, float] | None:
        """Remove presentation geometry only."""
        self._validate_id(object_id)
        return self._positions.pop(object_id, None)

    def clear(self) -> None:
        """Clear presentation geometry."""
        self._positions.clear()

    def snapshot(self) -> tuple[SLDPlacement, ...]:
        """Return deterministic immutable placement data."""
        return tuple(
            SLDPlacement(object_id, x, y)
            for object_id, (x, y) in self._positions.items()
        )

    def arrange(self, object_ids: Iterable[str]) -> tuple[SLDPlacement, ...]:
        """Create deterministic placeholder geometry for dummy rendering."""
        return tuple(
            SLDPlacement(str(object_id), float(index * 160), 0.0)
            for index, object_id in enumerate(object_ids)
        )

    def apply(self, positions: Mapping[str, tuple[float, float]]) -> tuple[SLDPlacement, ...]:
        """Convert externally supplied presentation positions to placements."""
        return tuple(
            SLDPlacement(str(object_id), position[0], position[1])
            for object_id, position in positions.items()
        )

    @staticmethod
    def _validate_id(object_id: str) -> None:
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError("SLD layout object_id must be a non-empty string")


__all__ = ["SLDLayout", "SLDPlacement"]
