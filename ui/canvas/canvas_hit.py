# ============================================================
# GridForge V2 — Presentation Canvas Hit Target
# ============================================================
"""Immutable presentation-side pointer hit metadata.

This module contains no Qt or Core dependencies. It describes what the
presentation/input boundary found under the pointer; it does not own selection,
SLD persistence, or electrical topology.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

Point = tuple[float, float]
RoutePoints = tuple[Point, ...]

class CanvasHitKind(str, Enum):
    """Semantic presentation categories produced by canvas hit testing."""

    NONE = "none"
    NODE = "node"
    CONNECTION = "connection"
    SIMPLE_WIRE_SEGMENT = "simple_wire_segment"

@dataclass(frozen=True, slots=True)
class CanvasHitTarget:
    """Immutable presentation hit result carried by CanvasMouseEvent."""

    kind: CanvasHitKind = CanvasHitKind.NONE
    object_id: Any = None
    presentation_id: str | None = None
    core_connection_id: str | None = None
    segment_index: int | None = None
    closest_point: Point | None = None
    distance: float | None = None
    source_point: Point | None = None
    target_point: Point | None = None
    route_points: RoutePoints = ()
    route_ownership: str | None = None

    @classmethod
    def none(cls) -> "CanvasHitTarget":
        """Return the canonical no-hit value."""
        return cls()

    @classmethod
    def node(cls, object_id: Any) -> "CanvasHitTarget":
        """Create a node/object hit without inventing a Core identity."""
        if object_id is None:
            return cls.none()
        return cls(kind=CanvasHitKind.NODE, object_id=object_id, presentation_id=str(object_id) if isinstance(object_id, str) else None)

    @classmethod
    def connection(cls, *, object_id: Any, presentation_id: str | None, core_connection_id: str | None) -> "CanvasHitTarget":
        """Create a presentation connection hit."""
        if object_id is None and core_connection_id is None:
            return cls.none()
        return cls(kind=CanvasHitKind.CONNECTION, object_id=object_id, presentation_id=presentation_id, core_connection_id=core_connection_id)

    @classmethod
    def simple_wire_segment(
        cls, *, object_id: Any, presentation_id: str, core_connection_id: str,
        segment_index: int, closest_point: Point, distance: float,
        source_point: Point, target_point: Point, route_points: RoutePoints,
        route_ownership: str | None,
    ) -> "CanvasHitTarget":
        """Create a validated routed Simple Wire segment hit."""
        if not isinstance(core_connection_id, str) or not core_connection_id:
            return cls.none()
        if not isinstance(presentation_id, str) or not presentation_id:
            return cls.none()
        if isinstance(segment_index, bool) or not isinstance(segment_index, int) or segment_index < 0:
            return cls.none()
        if not isinstance(distance, (int, float)) or isinstance(distance, bool) or distance < 0:
            return cls.none()
        try:
            normalized_route = tuple((float(point[0]), float(point[1])) for point in route_points)
            normalized_closest = (float(closest_point[0]), float(closest_point[1]))
            normalized_source = (float(source_point[0]), float(source_point[1]))
            normalized_target = (float(target_point[0]), float(target_point[1]))
        except (TypeError, ValueError, IndexError):
            return cls.none()
        return cls(kind=CanvasHitKind.SIMPLE_WIRE_SEGMENT, object_id=object_id, presentation_id=presentation_id, core_connection_id=core_connection_id, segment_index=segment_index, closest_point=normalized_closest, distance=float(distance), source_point=normalized_source, target_point=normalized_target, route_points=normalized_route, route_ownership=None if route_ownership is None else str(route_ownership))

    @classmethod
    def from_connection_item(cls, item: Any, hit: Mapping[str, Any]) -> "CanvasHitTarget":
        """Convert the existing connection hit capability into this value object."""
        object_id = getattr(item, "object_id", None)
        presentation_id = getattr(item, "presentation_id", None)
        core_connection_id = getattr(item, "core_connection_id", None)
        if not isinstance(core_connection_id, str) or not core_connection_id:
            return cls.none()
        connection_kind = str(getattr(item, "connection_kind", "") or "").upper()
        if connection_kind == "SIMPLE_WIRE":
            return cls.simple_wire_segment(object_id=object_id, presentation_id=presentation_id, core_connection_id=core_connection_id, segment_index=hit.get("segment_index"), closest_point=hit.get("closest_point"), distance=hit.get("distance"), source_point=hit.get("source"), target_point=hit.get("target"), route_points=hit.get("route", ()), route_ownership=hit.get("route_ownership"))
        return cls.connection(object_id=object_id, presentation_id=presentation_id, core_connection_id=core_connection_id)

__all__ = ["CanvasHitKind", "CanvasHitTarget"]
