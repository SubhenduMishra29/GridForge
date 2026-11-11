# ============================================================
# GridForge V2 — SLD route edit controller
# ============================================================
"""Presentation-only route-bend editing orchestration."""

from __future__ import annotations

from typing import Any, Mapping

from core.application.commands.draft_commands import UpdateDraftConnectionRouteCommand


class SLDRouteEditController:
    """Collect bend edits and commit them through the existing SLDController."""

    def __init__(self, sld_controller: Any, refresh_callback: Any | None = None) -> None:
        if sld_controller is None or not callable(getattr(sld_controller, "set_connection_route", None)):
            raise TypeError("sld_controller must expose set_connection_route()")
        self._controller = sld_controller
        self._refresh_callback = refresh_callback
        self._connection_id: str | None = None
        self._core_connection_id: str | None = None
        self._points: list[tuple[float, float]] = []

    def bind_refresh_callback(self, callback: Any) -> None:
        if not callable(callback):
            raise TypeError("refresh callback must be callable.")
        self._refresh_callback = callback

    def _refresh_after_edit(self) -> None:
        if self._refresh_callback is not None:
            self._refresh_callback()

    def begin(
        self,
        connection_id: str,
        points: tuple[tuple[float, float], ...] | list[tuple[float, float]],
        *,
        core_connection_id: str | None = None,
    ) -> None:
        if not isinstance(connection_id, str) or not connection_id:
            raise ValueError("connection_id must be a non-empty presentation identity")
        if core_connection_id is not None and (
            not isinstance(core_connection_id, str) or not core_connection_id
        ):
            raise ValueError("core_connection_id must be a non-empty string when provided")
        self._connection_id = connection_id
        self._core_connection_id = core_connection_id
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
        if request.get("instrumentation_wiring") is True:
            if request.get("core_connection_id") is not None:
                raise ValueError("Physical wiring route edits must not carry a Core connection identity.")
            carrier_kind = request.get("carrier_kind")
            carrier_id = request.get("carrier_id")
            segment_index = request.get("segment_index")
            points = request.get("points")
            if not isinstance(carrier_kind, str) or not carrier_kind:
                raise ValueError("Physical wiring route edit requires carrier_kind.")
            if not isinstance(carrier_id, str) or not carrier_id:
                raise ValueError("Physical wiring route edit requires carrier_id.")
            if isinstance(segment_index, bool) or not isinstance(segment_index, int) or segment_index < 1:
                raise ValueError("Physical wiring route edit requires a positive segment_index.")
            if not isinstance(points, (tuple, list)):
                raise TypeError("Physical wiring route edit requires route points.")
            if request.get("clear_route") is True:
                clearer = getattr(self._controller, "clear_instrumentation_wiring_route", None)
                if not callable(clearer):
                    raise RuntimeError("SLDController does not expose physical wiring route reset.")
                clearer(carrier_kind, carrier_id, segment_index)
                self._refresh_after_edit()
                return
            setter = getattr(self._controller, "set_instrumentation_wiring_route", None)
            if not callable(setter):
                raise RuntimeError("SLDController does not expose physical wiring route persistence.")
            setter(carrier_kind, carrier_id, segment_index, tuple(points))
            self._refresh_after_edit()
            return
        draft_connection_id = request.get("draft_connection_id")
        if isinstance(draft_connection_id, str) and draft_connection_id:
            application = getattr(self._controller, "application", None)
            reader = getattr(application, "read_draft_network", None)
            executor = getattr(application, "execute", None)
            if not callable(reader) or not callable(executor):
                raise RuntimeError("Draft route editing requires the active Application draft boundary.")
            snapshot = reader()
            if not isinstance(snapshot, Mapping):
                raise RuntimeError("No active DraftNetwork is available for route editing.")
            points = request.get("points")
            if not isinstance(points, (tuple, list)):
                raise TypeError("draft route edit request requires route points")
            result = executor(UpdateDraftConnectionRouteCommand(
                project_id=str(snapshot.get("project_id", "")),
                activation_generation=snapshot.get("activation_generation"),
                connection_id=draft_connection_id,
                route={"routing_mode": "manual", "ownership": "engineer", "points": [list(point) for point in points]},
                document_id=getattr(
                    getattr(self._controller, "active_document", None),
                    "document_id",
                    None,
                ),
            ))
            if not getattr(result, "success", False):
                raise RuntimeError(getattr(result, "message", "Draft route update was rejected."))
            return
        # Persistent SLD route geometry remains separate from DraftNetwork
        # route metadata. The Core ID verifies the existing SLD binding.
        presentation_connection_id = request.get("connection_id")
        core_connection_id = request.get("core_connection_id")
        points = request.get("points")
        if not isinstance(presentation_connection_id, str) or not presentation_connection_id:
            raise ValueError("route edit request requires presentation connection_id")
        if not isinstance(core_connection_id, str) or not core_connection_id:
            raise ValueError("route edit request requires explicit core_connection_id")
        if not isinstance(points, (tuple, list)):
            raise TypeError("route edit request requires route points")
        self.begin(
            presentation_connection_id,
            points,
            core_connection_id=core_connection_id,
        )
        self.commit()

    def commit(self) -> None:
        if self._connection_id is None:
            raise RuntimeError("No SLD route edit is active")
        try:
            # The controller/Application command is the only persistence
            # boundary.  Do not update graphics here; a successful command
            # causes the canonical SLD projection to be refreshed.
            self._controller.set_connection_route(
                self._connection_id,
                tuple(self._points),
                routing_mode="manual",
                core_connection_id=self._core_connection_id,
            )
        finally:
            # Proposed route state is interaction-local.  It must not survive
            # either acceptance or rejection of the command.
            self.cancel()

    def cancel(self) -> None:
        self._connection_id = None
        self._core_connection_id = None
        self._points = []


__all__ = ["SLDRouteEditController"]
