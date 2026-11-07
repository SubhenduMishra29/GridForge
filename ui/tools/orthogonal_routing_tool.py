# ============================================================
# File: ui/tools/orthogonal_routing_tool.py
# GridForge V2 — Live Orthogonal Routing Tool
# ============================================================
"""Live A* route preview with Application-owned electrical commit.

The tool owns only transient pointer/preview state. Stable endpoint identity
and final connectivity remain delegated to WireTool's canonical Application
command path.
"""

from __future__ import annotations

from typing import Any

from ui.connections.connection_router import ConnectionRouter
from ui.core.qt import QColor, QGraphicsPathItem, QPainterPath, QPen, QPointF, Qt

from .wire_tool import WireTool


class OrthogonalRoutingTool(WireTool):
    """Draw a live obstacle-aware orthogonal path between electrical endpoints."""

    TOOL_ID = "orthogonal-routing"
    CLEARANCE_PIXELS = 5.0
    ROUTE_CLEARANCE_PIXELS = 8.0
    PREVIEW_DATA_ROLE = 0
    PREVIEW_DATA_KEY = "gridforge.orthogonal-routing.preview"

    def __init__(
        self,
        controller: Any,
        application: Any,
        selection_manager: Any,
        snap_system: Any,
        preview_layer: Any = None,
    ) -> None:
        super().__init__(
            controller=controller,
            application=application,
            selection_manager=selection_manager,
            snap_system=snap_system,
            preview_layer=preview_layer,
        )
        self._router = ConnectionRouter()
        self._route_item: QGraphicsPathItem | None = None
        self._route_points: tuple[tuple[float, float], ...] = ()
        self._route_valid = False
        self._pending_press_snap: Any = None
        self._last_route_signature: tuple[Any, ...] | None = None

    @property
    def name(self) -> str:
        return "Orthogonal Routing"

    @property
    def description(self) -> str:
        return "Route an electrical connection around equipment with a live orthogonal preview."

    def _snap(self, event: Any) -> Any:
        if self._pending_press_snap is not None:
            result = self._pending_press_snap
            self._pending_press_snap = None
            return result
        return super()._snap(event)

    def on_mouse_press(self, event: Any) -> bool:
        self._ensure_active()
        if self._preview.source_endpoint is None:
            self._route_points = ()
            self._route_valid = False
            return super().on_mouse_press(event)

        # Resolve and route against the exact target snap that will be passed
        # to WireTool's existing endpoint-identity and Application command path.
        target_snap = super()._snap(event)
        if target_snap is None or getattr(getattr(target_snap, "snap_type", None), "name", None) != "OBJECT":
            self._route_valid = False
            self._route_points = ()
            self._show_preview()
            self._report_feedback("Orthogonal routing requires a stable electrical endpoint to commit.")
            return True
        target_position = self._position_tuple(target_snap.position)
        self._current_position = target_position
        if not self._calculate_route(target_position, target_snap):
            self._show_preview()
            self._report_feedback(self._failure_reason or "No valid orthogonal route is available.")
            return True
        self._pending_press_snap = target_snap
        self._last_snap_result = target_snap
        self._current_position = target_position
        self._show_preview()
        return super().on_mouse_press(event)

    def _execute_connection(self, endpoint_from: Any, endpoint_to: Any, *, source_snap: Any, target_snap: Any) -> Any:
        if not self._route_valid or len(self._route_points) < 2:
            raise ValueError("Orthogonal routing cannot commit without a valid computed route.")
        # ConnectionRouter returns both electrical endpoint positions and
        # interior bends. SLDRoute stores only interior presentation bends;
        # the canonical endpoint identities remain in the Application command.
        route = {
            "routing_mode": "orthogonal",
            "ownership": "engineer",
            "points": [list(point) for point in self._route_points[1:-1]],
        }
        return super()._execute_connection(
            endpoint_from,
            endpoint_to,
            source_snap=source_snap,
            target_snap=target_snap,
            presentation_route=route,
        )

    def on_mouse_move(self, event: Any) -> bool:
        handled = super().on_mouse_move(event)
        if self._preview.source_endpoint is None or self._current_position is None:
            return handled
        snap = self._last_snap_result
        is_endpoint = snap is not None and getattr(getattr(snap, "snap_type", None), "name", None) == "OBJECT"
        target_position = self._position_tuple(snap.position) if is_endpoint else self._position_tuple(self._current_position)
        self._calculate_route(target_position, snap if is_endpoint else None)
        if not is_endpoint:
            # Geometrically routable is not electrically connectable: a free
            # cursor position has no stable endpoint identity and stays red.
            self._route_valid = False
        self._show_preview()
        return True

    def _calculate_route(self, target_position: tuple[float, float], target_snap: Any = None) -> bool:
        if self._start_position is None or self._start_snap is None:
            self._route_valid = False
            self._route_points = ()
            self._failure_reason = "Select a source electrical endpoint first."
            return False
        source_id = str(getattr(self._start_snap, "object_id", "") or "")
        target_id = str(getattr(target_snap, "object_id", "") or "")
        excluded_ids = {value for value in (source_id, target_id) if value}
        try:
            obstacles, existing_routes = self._routing_context(excluded_ids)
            clearance = self.CLEARANCE_PIXELS / self._view_scale()
            signature = (
                self._start_position,
                source_id,
                target_position,
                target_id,
                tuple(obstacles),
                tuple(existing_routes),
                clearance,
            )
            if signature == self._last_route_signature:
                return self._route_valid
            self._last_route_signature = signature
            self._route_points = self._router.route(
                self._start_position,
                target_position,
                obstacles=obstacles,
                existing_routes=existing_routes,
                clearance=clearance,
                route_clearance=self.ROUTE_CLEARANCE_PIXELS / self._view_scale(),
            ).points
        except (TypeError, ValueError, RuntimeError) as exc:
            self._route_valid = False
            self._route_points = ()
            self._failure_reason = f"No orthogonal route: {exc}"
            return False
        self._route_valid = True
        self._failure_reason = ""
        return True

    def _routing_context(self, excluded_ids: set[str]) -> tuple[list[tuple[float, float, float, float]], list[tuple[tuple[float, float], ...]]]:
        layer = self._preview_layer
        scene_getter = getattr(layer, "get_scene", None)
        scene = scene_getter() if callable(scene_getter) else getattr(layer, "scene", None)
        if scene is None or not callable(getattr(scene, "items", None)):
            raise RuntimeError("Orthogonal routing requires the active SLD scene through PreviewLayer.")
        obstacles: list[tuple[float, float, float, float]] = []
        existing_routes: list[tuple[tuple[float, float], ...]] = []
        seen_routes: set[int] = set()
        for item in tuple(scene.items()):
            if item is None:
                continue
            data_getter = getattr(item, "data", None)
            if callable(data_getter) and data_getter(self.PREVIEW_DATA_ROLE) == self.PREVIEW_DATA_KEY:
                continue
            endpoints_getter = getattr(item, "visual_endpoints", None)
            route_getter = getattr(item, "route_points", None)
            if callable(endpoints_getter) and callable(route_getter):
                item_key = id(item)
                if item_key in seen_routes:
                    continue
                seen_routes.add(item_key)
                try:
                    source, target = endpoints_getter()
                    points = (self._scene_point(item, source),) + tuple(
                        self._scene_point(item, point) for point in tuple(route_getter())
                    ) + (self._scene_point(item, target),)
                    if len(points) >= 2:
                        existing_routes.append(points)
                except (AttributeError, TypeError, ValueError, RuntimeError):
                    continue
                continue
            parent_getter = getattr(item, "parentItem", None)
            if callable(parent_getter) and parent_getter() is not None:
                continue
            object_id = getattr(item, "object_id", None)
            if object_id is None or str(object_id) in excluded_ids:
                continue
            bounds_getter = getattr(item, "sceneBoundingRect", None)
            if not callable(bounds_getter):
                continue
            try:
                bounds = bounds_getter()
                rect = (float(bounds.left()), float(bounds.top()), float(bounds.right()), float(bounds.bottom()))
            except (TypeError, ValueError, RuntimeError):
                continue
            if rect[2] > rect[0] and rect[3] > rect[1]:
                obstacles.append(rect)
        return obstacles, existing_routes

    @staticmethod
    def _scene_point(item: Any, point: Any) -> tuple[float, float]:
        if hasattr(point, "x") and hasattr(point, "y"):
            x, y = float(point.x()), float(point.y())
        else:
            x, y = float(point[0]), float(point[1])
        mapper = getattr(item, "mapToScene", None)
        if callable(mapper):
            mapped = mapper(QPointF(x, y))
            return float(mapped.x()), float(mapped.y())
        return x, y

    def _view_scale(self) -> float:
        controller = self.controller
        view = None
        for name in ("get_view", "get_graphics_view"):
            getter = getattr(controller, name, None)
            if callable(getter):
                try:
                    view = getter()
                except (RuntimeError, TypeError):
                    view = None
                if view is not None:
                    break
        if view is None:
            view = getattr(controller, "graphics_view", None) or getattr(controller, "view", None)
        transform_getter = getattr(view, "transform", None)
        if callable(transform_getter):
            try:
                scale = abs(float(transform_getter().m11()))
                if scale > 1e-9:
                    return scale
            except (AttributeError, TypeError, ValueError, RuntimeError):
                pass
        layer = self._preview_layer
        scene_getter = getattr(layer, "get_scene", None)
        scene = scene_getter() if callable(scene_getter) else getattr(layer, "scene", None)
        views_getter = getattr(scene, "views", None)
        if callable(views_getter):
            try:
                views = tuple(views_getter())
                if views:
                    scale = abs(float(views[0].transform().m11()))
                    if scale > 1e-9:
                        return scale
            except (AttributeError, TypeError, ValueError, RuntimeError):
                pass
        zoom_getter = getattr(controller, "get_zoom_level", None)
        if callable(zoom_getter):
            try:
                scale = abs(float(zoom_getter()))
                if scale > 1e-9:
                    return scale
            except (TypeError, ValueError, RuntimeError):
                pass
        return 1.0

    def _show_preview(self) -> None:
        layer = self._preview_layer
        if layer is None:
            return
        points = self._route_points if self._route_valid and len(self._route_points) >= 2 else ()
        if not points and self._start_position is not None and self._current_position is not None:
            # Keep a conspicuous invalid guide visible instead of silently
            # removing the preview when no collision-free route exists.
            points = (self._start_position, self._position_tuple(self._current_position))
        if len(points) < 2:
            self._remove_route_item()
            return
        path = QPainterPath()
        path.moveTo(QPointF(*points[0]))
        for point in points[1:]:
            path.lineTo(QPointF(*point))
        if self._route_item is None:
            self._route_item = QGraphicsPathItem()
            self._route_item.setData(self.PREVIEW_DATA_ROLE, self.PREVIEW_DATA_KEY)
            self._route_item.setZValue(15.0)
            add = getattr(layer, "add", None)
            if not callable(add):
                self._route_item = None
                return
            add(self._route_item)
        color = "#1976D2" if self._route_valid else "#D32F2F"
        pen = QPen(QColor(color), 2.0, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        self._route_item.setPen(pen)
        self._route_item.setPath(path)
        tooltip = (
            "Live orthogonal route preview — not committed connectivity."
            if self._route_valid
            else "INVALID ROUTE — no collision-free path; this guide cannot be committed."
        )
        self._route_item.setToolTip(tooltip)

    def _remove_route_item(self) -> None:
        item = self._route_item
        self._route_item = None
        if item is None:
            return
        remove = getattr(self._preview_layer, "remove", None)
        if callable(remove):
            remove(item)

    def _clear_state(self) -> None:
        self._remove_route_item()
        self._route_points = ()
        self._route_valid = False
        self._pending_press_snap = None
        self._last_route_signature = None
        super()._clear_state()

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state.update({"route_valid": self._route_valid, "route_points": self._route_points, "clearance_pixels": self.CLEARANCE_PIXELS})
        return state


__all__ = ["OrthogonalRoutingTool"]
