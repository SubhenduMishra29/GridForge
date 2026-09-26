# ============================================================
# GridForge V2 — SLD route edit controller
# ============================================================
"""Presentation-only route-bend editing orchestration."""

from __future__ import annotations

from typing import Any


class SLDRouteEditController:
    """Collect bend edits and commit them through the existing SLDController."""

    def __init__(self, sld_controller: Any) -> None:
        if sld_controller is None or not callable(getattr(sld_controller, "set_connection_route", None)):
            raise TypeError("sld_controller must expose set_connection_route()")
        self._controller = sld_controller
        self._connection_id: str | None = None
        self._points: list[tuple[float, float]] = []

    def begin(self, connection_id: str, points: tuple[tuple[float, float], ...] | list[tuple[float, float]]) -> None:
        if not isinstance(connection_id, str) or not connection_id:
            raise ValueError("connection_id must be a non-empty string")
        self._connection_id = connection_id
        self._points = [(float(x), float(y)) for x, y in points]

    def move_bend(self, index: int, x: float, y: float) -> None:
        if self._connection_id is None:
            raise RuntimeError("No SLD route edit is active")
        if index < 0 or index >= len(self._points):
            raise IndexError(index)
        self._points[index] = (float(x), float(y))

    def handle_route_edit_request(self, request: Any) -> None:
        """Commit one graphics-item route edit through SLDController/Application."""
        if not isinstance(request, dict):
            raise TypeError("route edit request must be a mapping")
        connection_id = request.get("connection_id")
        points = request.get("points")
        if not isinstance(connection_id, str) or not connection_id:
            raise ValueError("route edit request requires connection_id")
        if not isinstance(points, (tuple, list)):
            raise TypeError("route edit request requires route points")
        self.begin(connection_id, points)
        self.commit()

    def commit(self) -> None:
        if self._connection_id is None:
            raise RuntimeError("No SLD route edit is active")
        self._controller.set_connection_route(self._connection_id, tuple(self._points), routing_mode="manual")
        self.cancel()

    def cancel(self) -> None:
        self._connection_id = None
        self._points = []


__all__ = ["SLDRouteEditController"]
