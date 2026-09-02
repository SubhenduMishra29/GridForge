# ============================================================
# File: ui/sld/sld_layout.py
# GridForge V2 — SLD Layout
# Author: Subhendu Mishra
# ============================================================
"""Presentation-only geometry store for the SLD surface.

Layout owns visual coordinates and does not own electrical truth, Core model
mutation, or QGraphicsItem lifecycle.
"""

from __future__ import annotations


class SLDLayout:
    """Store SLD visual positions keyed by stable Core object IDs."""

    def __init__(self) -> None:
        self._positions: dict[str, tuple[float, float]] = {}

    def set_position(self, object_id: str, x: float, y: float) -> None:
        """Set the presentation position for a Core object projection."""
        if not isinstance(object_id, str) or not object_id:
            raise ValueError("SLD layout object_id must be a non-empty string")
        self._positions[object_id] = (float(x), float(y))

    def position(self, object_id: str) -> tuple[float, float] | None:
        """Return a stored presentation position, if one exists."""
        return self._positions.get(object_id)

    def remove(self, object_id: str) -> tuple[float, float] | None:
        """Remove and return a presentation position, if present."""
        return self._positions.pop(object_id, None)

    def clear(self) -> None:
        """Remove all presentation positions."""
        self._positions.clear()
