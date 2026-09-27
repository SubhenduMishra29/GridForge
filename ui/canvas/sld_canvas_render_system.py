# ============================================================
# File: ui/canvas/sld_canvas_render_system.py
# GridForge V2 — SLD Canvas Render System
# Author: Subhendu Mishra
# ============================================================
"""Realize renderer-neutral SLD snapshots into transient graphics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ui.core.qt import QGraphicsScene, QPen, QPointF
from ui.connections.connection_router import ConnectionRouter
from ui.sld.sld_endpoint_resolver import SLDEndpointResolver

from .semantic_presentation_realization import SemanticPresentationRealization
from .sld_canvas_projection import SLDCanvasSnapshot
from .sld_graphics_item_factory import SLDGraphicsItemFactory


@dataclass(frozen=True, slots=True)
class RenderDiagnostic:
    """Structured presentation-realization failure visible to UI consumers."""

    node_id: str
    equipment_id: str | None
    equipment_type: str | None
    symbol_id: str | None
    requested_presentation: str | None
    category: str
    message: str
    canvas: str = "SLD"


class SLDCanvasRenderSystem:
    """Render an SLD snapshot using explicitly composed dependencies."""

    NODE_PEN_WIDTH = 1.5
    CONNECTION_PEN_WIDTH = 2.0

    def __init__(self, scene: QGraphicsScene, item_factory: SLDGraphicsItemFactory,
                 semantic_realization: SemanticPresentationRealization) -> None:
        if scene is None:
            raise ValueError("scene must not be None")
        if not isinstance(item_factory, SLDGraphicsItemFactory):
            raise TypeError("item_factory must be an SLDGraphicsItemFactory")
        if not isinstance(semantic_realization, SemanticPresentationRealization):
            raise TypeError("semantic_realization must be a SemanticPresentationRealization")
        self._scene = scene
        self._item_factory = item_factory
        self._semantic_realization = semantic_realization
        self._items: dict[str, tuple[Any, ...]] = {}
        self._unsupported_presentations: dict[str, str] = {}
        self._unsupported_connections: dict[str, str] = {}
        self._render_diagnostics: tuple[RenderDiagnostic, ...] = ()
        self._diagnostic_sink: Callable[[RenderDiagnostic], None] | None = None
        self._connection_router = ConnectionRouter()
        self._endpoint_resolver = SLDEndpointResolver()
        self._route_edit_controller: Any = None

    @property
    def scene(self) -> QGraphicsScene:
        return self._scene

    @property
    def item_factory(self) -> SLDGraphicsItemFactory:
        return self._item_factory

    @property
    def semantic_realization(self) -> SemanticPresentationRealization:
        return self._semantic_realization

    @property
    def unsupported_presentations(self) -> dict[str, str]:
        """Return authored node IDs whose presentation could not be realized."""
        return dict(self._unsupported_presentations)

    @property
    def bind_diagnostic_sink(self, sink: Callable[[RenderDiagnostic], None] | None) -> None:
        """Bind an optional application/UI diagnostic consumer."""
        if sink is not None and not callable(sink):
            raise TypeError("diagnostic sink must be callable or None")
        self._diagnostic_sink = sink

    @property
    def render_diagnostics(self) -> tuple[RenderDiagnostic, ...]:
        """Return structured diagnostics for the latest synchronization."""
        return self._render_diagnostics

    @property
    def has_render_failures(self) -> bool:
        return bool(self._render_diagnostics or self._unsupported_connections)

    @property
    def unsupported_connections(self) -> dict[str, str]:
        """Return authored connection IDs whose presentation could not be realized."""
        return dict(self._unsupported_connections)

    def bind_route_edit_controller(self, controller: Any) -> None:
        """Bind the presentation route-edit boundary to realized connection items."""
        if controller is None or not callable(getattr(controller, "handle_route_edit_request", None)):
            raise TypeError("route edit controller must expose handle_route_edit_request().")
        self._route_edit_controller = controller
        for items in tuple(self._items.values()):
            for item in items:
                signal = getattr(item, "route_edit_requested", None)
                if signal is not None and callable(getattr(signal, "connect", None)):
                    signal.connect(controller.handle_route_edit_request)

    @staticmethod
    def _pen(width: float) -> QPen:
        pen = QPen()
        setter = getattr(pen, "setWidthF", None)
        if callable(setter):
            setter(float(width))
        else:
            pen.setWidth(int(round(width)))
        return pen

    def synchronize(self, snapshot: SLDCanvasSnapshot) -> None:
        if not isinstance(snapshot, SLDCanvasSnapshot):
            raise TypeError("snapshot must be an SLDCanvasSnapshot")
        self.clear()
        self._unsupported_presentations.clear()
        self._unsupported_connections.clear()
        self._render_diagnostics = ()
        realized: dict[str, Any] = {}
        # Realize nodes first so semantic endpoint resolution can use canonical
        # SymbolDefinition anchors and Bus attachment geometry.
        for node in snapshot.nodes:
            try:
                selection = self._semantic_realization.realize(node)
                item = self._item_factory.create_node(node, selection)
            except Exception as exc:
                # The authored SLD node remains intact. The failure is explicit
                # projection state and is also exposed through structured
                # diagnostics so blank rendering cannot masquerade as absence.
                message = f"{type(exc).__name__}: {exc}"
                self._unsupported_presentations[node.node_id] = message
                diagnostic = RenderDiagnostic(
                    node_id=node.node_id,
                    equipment_id=node.equipment_id,
                    equipment_type=str(node.properties.get("element_type")) if node.properties.get("element_type") is not None else None,
                    symbol_id=getattr(node.presentation, "symbol_id", None),
                    requested_presentation=getattr(node.presentation, "representation_id", None),
                    category="presentation_realization",
                    message=message,
                )
                self._render_diagnostics = (*self._render_diagnostics, diagnostic)
                if self._diagnostic_sink is not None:
                    self._diagnostic_sink(diagnostic)
                continue
            item.set_pen(self._pen(self.NODE_PEN_WIDTH))
            self._scene.addItem(item)
            self._items[node.node_id] = (item,)
            realized[node.node_id] = item

        for connection in snapshot.connections:
            if connection.source_endpoint is None or connection.target_endpoint is None:
                self._unsupported_connections[connection.connection_id] = "Missing canonical endpoint references."
                continue
            try:
                source = self._endpoint_resolver.resolve(connection.source_endpoint, realized)
                target = self._endpoint_resolver.resolve(connection.target_endpoint, realized)
            except (KeyError, TypeError, ValueError) as exc:
                self._unsupported_connections[connection.connection_id] = f"{type(exc).__name__}: {exc}"
                continue
            route_points = connection.route.points
            if connection.route.ownership == "auto":
                route = self._connection_router.route((source.x(), source.y()), (target.x(), target.y()))
                route_points = tuple(route.points[1:-1])
            item = self._item_factory.create_connection(connection, source, target)
            item.set_visual_route(source, target, route_points, ownership=connection.route.ownership)
            if self._route_edit_controller is not None:
                item.route_edit_requested.connect(
                    self._route_edit_controller.handle_route_edit_request
                )
            item.set_pen(self._pen(self.CONNECTION_PEN_WIDTH))
            self._scene.addItem(item)
            self._items[connection.connection_id] = (item,)

    def clear(self) -> None:
        for items in tuple(self._items.values()):
            for item in items:
                if item is not None and item.scene() is self._scene:
                    self._scene.removeItem(item)
        self._items.clear()
        self._unsupported_presentations.clear()
        self._unsupported_connections.clear()
        self._render_diagnostics = ()

    def dispose(self) -> None:
        self.clear()


__all__ = ["RenderDiagnostic", "SLDCanvasRenderSystem"]
