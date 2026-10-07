# ============================================================
# Author: Subhendu Mishra
# GridForge V2 — SLD Connection Graphics Projection
# ============================================================
"""Presentation-only realization of one semantic SLD connection."""

from __future__ import annotations

from typing import Iterable
import math

from ui.core.qt import QGraphicsItem, QGraphicsPathItem, QPainterPath, QPen, QPointF, Signal
from ui.sld.sld_model import SLDEndpoint
from ui.styling.presentation_style import VisualState, visual_pen


class SLDConnectionItem(QGraphicsPathItem):
    route_edit_requested = Signal(object)
    """Render resolved semantic endpoints and engineer-owned route geometry."""

    def __init__(
        self,
        object_id: str,
        source_object_id: str,
        target_object_id: str,
        source_endpoint: SLDEndpoint | None = None,
        target_endpoint: SLDEndpoint | None = None,
        connection_kind: str | None = None,
        presentation_owner: str | None = None,
        projection_source: str | None = None,
        core_connection_id: str | None = None,
    ) -> None:
        for name, value in (("object_id", object_id), ("source_object_id", source_object_id), ("target_object_id", target_object_id)):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")
        super().__init__()
        self._presentation_id = object_id
        # Presentation and Core identities are independent; never synthesize one from the other.
        self._core_connection_id = str(core_connection_id) if core_connection_id is not None else None
        # SelectionManager uses object_id as the semantic selection key.
        self._object_id = self._core_connection_id
        self._source_object_id = source_object_id
        self._target_object_id = target_object_id
        self._source_endpoint = source_endpoint
        self._target_endpoint = target_endpoint
        self._connection_kind = connection_kind
        self._presentation_owner = presentation_owner
        self._projection_source = projection_source
        self._route_points: tuple[tuple[float, float], ...] = ()
        self._route_ownership = "auto"
        self._visual_source = QPointF()
        self._visual_target = QPointF()
        self._visual_state = VisualState.NORMAL
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, self._core_connection_id is not None)
        self.setAcceptHoverEvents(True)

    @property
    def object_id(self) -> str | None:
        return self._object_id

    @property
    def presentation_id(self) -> str:
        return self._presentation_id

    @property
    def core_connection_id(self) -> str | None:
        return self._core_connection_id

    @property
    def source_object_id(self) -> str:
        return self._source_object_id

    @property
    def target_object_id(self) -> str:
        return self._target_object_id

    @property
    def source_endpoint(self) -> SLDEndpoint | None:
        return self._source_endpoint

    @property
    def target_endpoint(self) -> SLDEndpoint | None:
        return self._target_endpoint

    @property
    def connection_kind(self) -> str | None:
        return self._connection_kind

    @property
    def presentation_owner(self) -> str | None:
        return self._presentation_owner

    @property
    def projection_source(self) -> str | None:
        return self._projection_source

    @property
    def route_ownership(self) -> str:
        return self._route_ownership

    def set_visual_state(self, state: VisualState | str) -> None:
        self._visual_state = state if isinstance(state, VisualState) else VisualState(str(state).lower())
        self._refresh_pen()

    def _refresh_pen(self) -> None:
        role = "cable" if str(self._connection_kind or "").lower() == "cable" else (
            "line" if str(self._connection_kind or "").lower() == "line" else "connection"
        )
        state = self._visual_state
        if state in {VisualState.NORMAL, VisualState.HOVER}:
            state = VisualState.SELECTED if self.isSelected() else (VisualState.HOVER if self.isUnderMouse() else VisualState.NORMAL)
        self.setPen(visual_pen(role, state, width=2.0))

    def hoverEnterEvent(self, event) -> None:
        if self._visual_state == VisualState.NORMAL:
            self._visual_state = VisualState.HOVER
        self._refresh_pen()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        if self._visual_state == VisualState.HOVER:
            self._visual_state = VisualState.NORMAL
        self._refresh_pen()
        super().hoverLeaveEvent(event)

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

    def insertion_target(self, position: tuple[float, float]) -> dict[str, object]:
        """Return immutable insertion-hit data without mutating the graphics item."""
        if str(self._connection_kind or "").upper() != "SIMPLE_WIRE":
            raise ValueError("Only persistent Simple Wire connections are insertion targets.")
        if not isinstance(position, (tuple, list)) or len(position) != 2:
            raise TypeError("position must contain exactly two coordinates.")
        px, py = float(position[0]), float(position[1])
        polyline = [
            (float(self._visual_source.x()), float(self._visual_source.y())),
            *self._route_points,
            (float(self._visual_target.x()), float(self._visual_target.y())),
        ]
        best_distance = float("inf")
        best_point = None
        best_segment = None
        for index in range(len(polyline) - 1):
            ax, ay = polyline[index]
            bx, by = polyline[index + 1]
            dx, dy = bx - ax, by - ay
            length_sq = dx * dx + dy * dy
            if length_sq <= 0.0:
                continue
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
            qx, qy = ax + t * dx, ay + t * dy
            distance = math.hypot(px - qx, py - qy)
            if distance < best_distance:
                best_distance = distance
                best_point = (qx, qy)
                best_segment = index
        if best_point is None or best_segment is None:
            raise ValueError("SLD connection has no non-zero route segment.")
        return {
            "connection_id": self._core_connection_id,
            "presentation_id": self._presentation_id,
            "route": tuple(self._route_points),
            "closest_point": best_point,
            "segment_index": best_segment,
        }
    def set_bend(self, index: int, x: float, y: float) -> tuple[tuple[float, float], ...]:
        """Propose one bend without changing the realized/persisted route.

        The graphics item is a projection of the last accepted canvas snapshot.
        A bend gesture therefore produces an interaction request only; the
        Application command decides whether the persistent SLD route changes.
        """
        if self._core_connection_id is None:
            raise RuntimeError("Cannot edit route for an SLD connection without an explicit Core connection identity.")
        if index < 0 or index >= len(self._route_points):
            raise IndexError(index)

        points = list(self._route_points)
        points[index] = (float(x), float(y))
        proposed_route = tuple(points)

        # Never assign proposed_route to _route_points here.  That tuple is the
        # last realized route from SLDCanvasProjection/SLDCanvasRenderSystem.
        self.route_edit_requested.emit({
            "connection_id": self._presentation_id,
            "core_connection_id": self._core_connection_id,
            "points": proposed_route,
        })
        return proposed_route

    def _rebuild_visual_path(self) -> None:
        """Rebuild the visible path from the last accepted realized route."""
        path = QPainterPath(QPointF(self._visual_source))
        for x, y in self._route_points:
            path.lineTo(QPointF(float(x), float(y)))
        path.lineTo(QPointF(self._visual_target))
        self.setPath(path)
        self._refresh_pen()

    def visual_state(self) -> str:
        return self._visual_state.value

    def route_points(self) -> tuple[tuple[float, float], ...]:
        return self._route_points


__all__ = ["SLDConnectionItem"]
