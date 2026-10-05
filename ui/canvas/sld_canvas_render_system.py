# ============================================================
# File: ui/canvas/sld_canvas_render_system.py
# GridForge V2 — SLD Canvas Render System
# Author: Subhendu Mishra
# ============================================================
"""Realize renderer-neutral SLD snapshots into transient graphics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ui.core.qt import QGraphicsScene, QPointF, QGraphicsRectItem, QGraphicsTextItem
from ui.connections.connection_router import ConnectionRouter
from ui.sld.sld_endpoint_resolver import SLDEndpointResolver
from ui.sld.sld_equipment_identity import equipment_type_for_semantic
from ui.sld.sld_vocabulary import semantic_type

from .semantic_presentation_realization import SemanticPresentationRealization
from .sld_canvas_projection import SLDCanvasSnapshot
from .sld_graphics_item_factory import SLDGraphicsItemFactory
from ui.styling.presentation_style import VisualState


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
    connection_id: str | None = None
    code: str | None = None
    realization_stage: str = "node_realization"


class SLDCanvasRenderSystem:
    """Render an SLD snapshot using explicitly composed dependencies."""

    def __init__(self, scene: QGraphicsScene, item_factory: SLDGraphicsItemFactory,
                 semantic_realization: SemanticPresentationRealization, snap_system: Any = None) -> None:
        if scene is None:
            raise ValueError("scene must not be None")
        if not isinstance(item_factory, SLDGraphicsItemFactory):
            raise TypeError("item_factory must be an SLDGraphicsItemFactory")
        if not isinstance(semantic_realization, SemanticPresentationRealization):
            raise TypeError("semantic_realization must be a SemanticPresentationRealization")
        self._scene = scene
        self._item_factory = item_factory
        self._semantic_realization = semantic_realization
        self._snap_system = snap_system
        if snap_system is not None:
            if getattr(snap_system, "get_scene", lambda: None)() is not scene:
                raise ValueError("SLDCanvasRenderSystem snap_system must target the same active SLD scene.")
            if not callable(getattr(snap_system, "register_item", None)) or not callable(getattr(snap_system, "unregister_item", None)):
                raise TypeError("snap_system must expose canonical register_item()/unregister_item() lifecycle APIs.")
        self._items: dict[str, tuple[Any, ...]] = {}
        self._render_signatures: dict[str, str] = {}
        self._unsupported_presentations: dict[str, str] = {}
        self._unsupported_connections: dict[str, str] = {}
        self._degraded_node_ids: set[str] = set()
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
    def snap_system(self) -> Any:
        """Return the one presentation snap service bound to this SLD renderer."""
        return self._snap_system

    @property
    def unsupported_presentations(self) -> dict[str, str]:
        """Return authored node IDs whose presentation could not be realized."""
        return dict(self._unsupported_presentations)

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

    def synchronize(self, snapshot: SLDCanvasSnapshot) -> None:
        """Incrementally reconcile the existing scene with one immutable snapshot."""
        if not isinstance(snapshot, SLDCanvasSnapshot):
            raise TypeError("snapshot must be an SLDCanvasSnapshot")

        self._unsupported_presentations.clear()
        self._unsupported_connections.clear()
        self._render_diagnostics = ()

        desired_ids = {node.node_id for node in snapshot.nodes}
        desired_ids.update(connection.connection_id for connection in snapshot.connections)
        for item_id in tuple(self._items):
            if item_id not in desired_ids:
                self._remove_realized(item_id)

        realized: dict[str, Any] = {
            node_id: items[0]
            for node_id, items in self._items.items()
            if items
        }

        # Realize nodes first so endpoint resolution can use canonical symbol
        # anchors and existing Bus attachment geometry.
        for node in snapshot.nodes:
            signature = self._node_signature(node)
            if (
                self._render_signatures.get(node.node_id) == signature
                and node.node_id in self._items
                and node.node_id not in self._degraded_node_ids
            ):
                realized[node.node_id] = self._items[node.node_id][0]
                continue

            if node.node_id in self._items:
                self._remove_realized(node.node_id)
            try:
                selection = self._semantic_realization.realize(node)
                item = self._item_factory.create_node(node, selection)
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                code = self._node_failure_code(node, exc)
                self._unsupported_presentations[node.node_id] = message
                semantic_value = node.properties.get("element_type")
                semantic_value_text = None if semantic_value is None else str(semantic_value)
                try:
                    canonical_semantic = semantic_type(semantic_value_text) if semantic_value_text else None
                    canonical_equipment_type = (
                        equipment_type_for_semantic(canonical_semantic)
                        if canonical_semantic is not None else None
                    )
                except (TypeError, ValueError):
                    canonical_semantic = semantic_value_text
                    canonical_equipment_type = None
                diagnostic = RenderDiagnostic(
                    node_id=node.node_id,
                    equipment_id=node.equipment_id,
                    equipment_type=canonical_equipment_type,
                    symbol_id=getattr(node.presentation, "symbol_id", None),
                    requested_presentation=getattr(node.presentation, "representation_id", None),
                    category="presentation_realization",
                    message=message,
                    code=code,
                    realization_stage="SemanticPresentationRealization -> SLDGraphicsItemFactory.create_node",
                )
                self._render_diagnostics = (*self._render_diagnostics, diagnostic)
                degraded = self._create_degraded_realization(node, message, code)
                self._scene.addItem(degraded)
                self._items[node.node_id] = (degraded,)
                self._render_signatures[node.node_id] = signature
                self._degraded_node_ids.add(node.node_id)
                realized[node.node_id] = degraded
                if self._diagnostic_sink is not None:
                    self._diagnostic_sink(diagnostic)
                continue
            if callable(getattr(item, "set_visual_state", None)):
                item.set_visual_state(VisualState.NORMAL)
            self._scene.addItem(item)
            if self._snap_system is not None and callable(getattr(item, "snap_points", None)):
                self._snap_system.register_item(item)
            self._items[node.node_id] = (item,)
            self._render_signatures[node.node_id] = signature
            self._degraded_node_ids.discard(node.node_id)
            realized[node.node_id] = item

        node_by_id = {node.node_id: node for node in snapshot.nodes}
        for connection in snapshot.connections:
            signature = self._connection_signature(connection, node_by_id)
            if self._render_signatures.get(connection.connection_id) == signature and connection.connection_id in self._items:
                continue
            if connection.connection_id in self._items:
                self._remove_realized(connection.connection_id)
            if connection.source_node_id not in realized:
                self._record_connection_failure(connection, "SOURCE_NODE_NOT_FOUND", f"No realized SLD node for source {connection.source_node_id!r}.")
                continue
            if connection.target_node_id not in realized:
                self._record_connection_failure(connection, "TARGET_NODE_NOT_FOUND", f"No realized SLD node for target {connection.target_node_id!r}.")
                continue
            if connection.source_endpoint is None:
                self._record_connection_failure(connection, "SOURCE_ENDPOINT_NOT_FOUND", "Persisted SLD connection has no source endpoint identity.")
                continue
            if connection.target_endpoint is None:
                self._record_connection_failure(connection, "TARGET_ENDPOINT_NOT_FOUND", "Persisted SLD connection has no target endpoint identity.")
                continue
            try:
                source = self._endpoint_resolver.resolve(connection.source_endpoint, realized)
                target = self._endpoint_resolver.resolve(connection.target_endpoint, realized)
            except (KeyError, TypeError, ValueError) as exc:
                self._record_connection_failure(connection, "TERMINAL_ANCHOR_NOT_FOUND", f"{type(exc).__name__}: {exc}")
                continue
            route_points = connection.route.points
            if connection.route.ownership == "auto":
                route = self._connection_router.route((source.x(), source.y()), (target.x(), target.y()))
                route_points = tuple(route.points[1:-1])
            try:
                item = self._item_factory.create_connection(connection, source, target)
                item.set_visual_route(source, target, route_points, ownership=connection.route.ownership)
                if self._route_edit_controller is not None:
                    item.route_edit_requested.connect(
                        self._route_edit_controller.handle_route_edit_request
                    )
                if callable(getattr(item, "set_visual_state", None)):
                    item.set_visual_state(VisualState.NORMAL)
                self._scene.addItem(item)
                self._items[connection.connection_id] = (item,)
                self._render_signatures[connection.connection_id] = signature
            except Exception as exc:
                self._record_connection_failure(
                    connection, "CONNECTION_REALIZATION_FAILED",
                    f"{type(exc).__name__}: {exc}"
                )

    def _record_connection_failure(self, connection: Any, code: str, message: str) -> None:
        """Keep failed connection realization observable through RenderDiagnostic."""
        self._unsupported_connections[connection.connection_id] = message
        diagnostic = RenderDiagnostic(
            node_id=connection.source_node_id,
            equipment_id=None,
            equipment_type=None,
            symbol_id=None,
            requested_presentation=None,
            category="connection_realization",
            message=message,
            connection_id=connection.connection_id,
            code=code,
        )
        self._render_diagnostics = (*self._render_diagnostics, diagnostic)
        if self._diagnostic_sink is not None:
            self._diagnostic_sink(diagnostic)

    def _create_degraded_realization(self, node: Any, message: str, code: str) -> Any:
        """Create a visible/selectable presentation fallback without Core mutation."""
        item = QGraphicsRectItem(-70.0, -34.0, 140.0, 68.0)
        item.object_id = node.equipment_id or node.node_id
        item.node_id = node.node_id
        item.setToolTip(
            f"Unsupported presentation [{code}]\\n"
            f"node={node.node_id} equipment={item.object_id}\\n{message}"
        )
        text = QGraphicsTextItem(f"Unsupported Symbol\\n{item.object_id}", item)
        text.setPos(-62.0, -24.0)
        item.setPos(float(node.x), float(node.y))
        return item

    @staticmethod
    def _node_failure_code(node: Any, exc: Exception) -> str:
        """Classify node realization failures without hiding the underlying error."""
        message = str(exc)
        if node.equipment_id is None:
            return "MISSING_EQUIPMENT_ID"
        if "absent from Application read state" in message:
            return "EQUIPMENT_READ_MODEL_NOT_FOUND"
        return "PRESENTATION_REALIZATION_FAILED"

    @staticmethod
    def _node_signature(node: Any) -> str:
        presentation = getattr(node.presentation, "to_dict", lambda: None)()
        properties = tuple(sorted((str(key), repr(value)) for key, value in node.properties.items()))
        return repr((node.node_id, node.equipment_id, node.x, node.y, presentation, properties))

    @staticmethod
    def _connection_signature(connection: Any, node_by_id: dict[str, Any] | None = None) -> str:
        route = getattr(connection.route, "to_dict", lambda: None)()
        properties = tuple(sorted((str(key), repr(value)) for key, value in connection.properties.items()))
        source_node = None if node_by_id is None else node_by_id.get(connection.source_node_id)
        target_node = None if node_by_id is None else node_by_id.get(connection.target_node_id)
        geometry = (getattr(source_node, "x", None), getattr(source_node, "y", None), getattr(target_node, "x", None), getattr(target_node, "y", None))
        return repr((connection.connection_id, connection.source_node_id, connection.target_node_id, geometry,
                     connection.source_endpoint, connection.target_endpoint,
                     connection.connection_kind, connection.presentation_owner,
                     connection.projection_source, route, properties))

    def _remove_realized(self, item_id: str) -> None:
        items = self._items.pop(item_id, ())
        for item in items:
            if self._snap_system is not None and callable(getattr(self._snap_system, "unregister_item", None)):
                self._snap_system.unregister_item(item)
            if item is not None and item.scene() is self._scene:
                self._scene.removeItem(item)
        self._render_signatures.pop(item_id, None)
        self._degraded_node_ids.discard(item_id)

    def clear(self) -> None:
        for items in tuple(self._items.values()):
            for item in items:
                if self._snap_system is not None and callable(getattr(self._snap_system, "unregister_item", None)):
                    self._snap_system.unregister_item(item)
                if item is not None and item.scene() is self._scene:
                    self._scene.removeItem(item)
        if self._snap_system is not None and callable(getattr(self._snap_system, "clear_candidates", None)):
            self._snap_system.clear_candidates()
        self._items.clear()
        self._render_signatures.clear()
        self._degraded_node_ids.clear()
        self._unsupported_presentations.clear()
        self._unsupported_connections.clear()
        self._render_diagnostics = ()

    def dispose(self) -> None:
        self.clear()


__all__ = ["RenderDiagnostic", "SLDCanvasRenderSystem"]
