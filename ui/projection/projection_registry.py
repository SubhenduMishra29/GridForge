# ============================================================
# File: ui/projection/projection_registry.py
# GridForge V2 — Projection Registry
# Author: Subhendu Mishra
# ============================================================
"""Registry for UI projections keyed by stable Core object identity.

Responsibilities:
    - register and resolve projections by Core object ID;
    - reject duplicate projection ownership;
    - remove projections cleanly.

Boundary rules:
    - does not mutate Core objects;
    - does not create Qt graphics items;
    - does not own rendering or layout policy.
"""

from __future__ import annotations

from typing import Any


class ProjectionRegistry:
    """Own the mapping from stable Core IDs to UI projections."""

    def __init__(self) -> None:
        self._projections: dict[str, Any] = {}

    def register(self, projection: Any) -> None:
        """Register a projection using its stable Core object ID."""
        object_id = getattr(projection, "object_id", None)
        if not isinstance(object_id, str) or not object_id:
            raise ValueError("Projection must provide a non-empty object_id")

        if object_id in self._projections:
            raise ValueError(
                f"Projection already registered for Core object ID {object_id!r}"
            )

        self._projections[object_id] = projection

    def get(self, object_id: str) -> Any | None:
        """Return the projection for a Core object ID, if registered."""
        return self._projections.get(object_id)

    def contains(self, object_id: str) -> bool:
        """Return whether a projection is registered for the given ID."""
        return object_id in self._projections

    def remove(self, object_id: str) -> Any | None:
        """Remove and return a projection, or ``None`` when absent."""
        return self._projections.pop(object_id, None)

    def clear(self) -> None:
        """Remove all registered projections."""
        self._projections.clear()
