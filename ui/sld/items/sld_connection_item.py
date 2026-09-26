# ============================================================
# GridForge V2 — SLD Connection Graphics Projection
# ============================================================
"""Presentation-only realization of one semantic SLD connection."""

from __future__ import annotations

from typing import Iterable

from ui.core.qt import QGraphicsPathItem, QPainterPath, QPen, QPointF, Signal


class SLDConnectionItem(QGraphicsPathItem):
    route_edit_requested = Signal(object)
    """Render resolved semantic endpoints and engineer-owned route geometry."""

    def __init__(self, object_id: str, source_object_id: str, target_object_id: str) -> None:
        for name, value in (("object_id", object_id), ("source_object_id", source_object_id), ("target_object_id", target_object_id)):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")
        super().__init__()
        self._object_id = object_id
        self._source_object_id = source_object_id
        self._target_object_id = target_object_id
        self._route_points: tuple[tuple[float, float], ...] = ()
        self._route_ownership = "auto"
        self._visual_source = QPointF()
        self._visual_target = QPointF()

    @property
    def object_id(self) -> str:
        return self._object_id

    @property
    def source_object_id(self) -> str:
        return self._source_object_id

    @property
    def target_object_id(self) -> str:
        return self._target_object_id

    @property
    def route_ownership(self) -> str:
        return self._route_ownership

    def set_pen(self, pen: QPen) -> None:
        self.setPen(QPen(pen))

    def set_visual_route(
        self,
        source: QPointF,
        target: QPointF,
        points: Iterable[tuple[float, float]] = (),
        *,
        ownership: str = "auto",
    ) -> None:
        if ownership not in {"auto", "engineer"}:
            raise ValueError("route ownership must be 'auto' or 'engineer'")
        self._visual_source = QPointF(float(source.x()), float(source.y()))
        self._visual_target = QPointF(float(target.x()), float(target.y()))
        self._route_points = tuple((float(x), float(y)) for x, y in points)
        self._route_ownership = ownership
        self._rebuild_visual_path()

    def visual_endpoints(self) -> tuple[tuple[float, float], tuple[float, float]]:
        path = self.path()
        return ((path.elementAt(0).x, path.elementAt(0).y),
                (path.elementAt(path.elementCount() - 1).x, path.elementAt(path.elementCount() - 1).y))

    def set_bend(self, index: int, x: float, y: float) -> tuple[tuple[float, float], ...]:
        """Update one presentation bend and emit an Application-bound edit request."""
        if index < 0 or index >= len(self._route_points):
            raise IndexError(index)
        points = list(self._route_points)
        points[index] = (float(x), float(y))
        self._route_points = tuple(points)
        self._rebuild_visual_path()
        self.route_edit_requested.emit({
            "connection_id": self._object_id,
            "points": self._route_points,
        })
        return self._route_points

    def _rebuild_visual_path(self) -> None:
        """Rebuild the transient visible path from the current route points."""
        path = QPainterPath(QPointF(self._visual_source))
        for x, y in self._route_points:
            path.lineTo(QPointF(float(x), float(y)))
        path.lineTo(QPointF(self._visual_target))
        self.setPath(path)

    def route_points(self) -> tuple[tuple[float, float], ...]:
        return self._route_points


__all__ = ["SLDConnectionItem"]
