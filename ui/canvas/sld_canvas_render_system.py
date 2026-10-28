# ============================================================
# File: ui/canvas/sld_canvas_render_system.py
# GridForge V2 — SLD Canvas Render System
# Author: Subhendu Mishra
# ============================================================
"""Realize renderer-neutral SLD snapshots into transient graphics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable

from ui.core.qt import QGraphicsScene, QPointF, QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, Qt
from ui.connections.connection_router import ConnectionRouter
from ui.sld.sld_endpoint_resolver import SLDEndpointResolver
from ui.sld.sld_equipment_identity import equipment_type_for_semantic
from ui.sld.sld_vocabulary import semantic_type

from .semantic_presentation_realization import SemanticPresentationRealization
from .sld_canvas_projection import SLDCanvasSnapshot, SLDCanvasAnnotation, CompositeSLDCanvasSnapshot
from .sld_graphics_item_factory import SLDGraphicsItemFactory
from .draft_sld_projection import DraftSLDCanvasSnapshot, DraftSLDCanvasNode, DraftSLDCanvasConnection
from .draft_presentation_factory import DraftPresentationFactory
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

    DEFAULT_ANNOTATION_MIN_ZOOM = 0.65

    def __init__(self, scene: QGraphicsScene, item_factory: SLDGraphicsItemFactory,
                 semantic_realization: SemanticPresentationRealization, snap_system: Any = None,
                 selection_manager: Any = None,
                 annotation_min_zoom: float = DEFAULT_ANNOTATION_MIN_ZOOM) -> None:
        if scene is None:
            raise ValueError("scene must not be None")
        if not isinstance(item_factory, SLDGraphicsItemFactory):
            raise TypeError("item_factory must be an SLDGraphicsItemFactory")
        if not isinstance(semantic_realization, SemanticPresentationRealization):
            raise TypeError("semantic_realization must be a SemanticPresentationRealization")
        self._scene = scene
        self._item_factory = item_factory
        self._draft_presentation_factory = DraftPresentationFactory(
            item_factory.equipment_registry,
            item_factory.symbol_registry,
        )
        self._semantic_realization = semantic_realization
        self._snap_system = snap_system
        self._selection_manager = None
        if selection_manager is not None:
            self.bind_selection_manager(selection_manager)
        if snap_system is not None:
            if getattr(snap_system, "get_scene", lambda: None)() is not scene:
                raise ValueError("SLDCanvasRenderSystem snap_system must target the same active SLD scene.")
            if not callable(getattr(snap_system, "register_item", None)) or not callable(getattr(snap_system, "unregister_item", None)):
                raise TypeError("snap_system must expose canonical register_item()/unregister_item() lifecycle APIs.")
        if isinstance(annotation_min_zoom, bool) or not isinstance(annotation_min_zoom, (int, float)):
            raise TypeError("annotation_min_zoom must be numeric.")
        annotation_min_zoom = float(annotation_min_zoom)
        if not math.isfinite(annotation_min_zoom) or annotation_min_zoom <= 0.0:
            raise ValueError("annotation_min_zoom must be finite and greater than zero.")
        self._annotation_min_zoom = annotation_min_zoom
        self._zoom_level = 1.0
        self._annotations_zoom_visible = self._zoom_level >= self._annotation_min_zoom
        self._navigation_controller: Any = None
        self._annotation_base_visibility: dict[str, bool] = {}
        self._items: dict[str, tuple[Any, ...]] = {}
        self._render_signatures: dict[str, str] = {}
        self._unsupported_presentations: dict[str, str] = {}
        self._unsupported_connections: dict[str, str] = {}
        self._degraded_node_ids: set[str] = set()
        self._degraded_diagnostics: dict[str, RenderDiagnostic] = {}
        self._reported_diagnostics: dict[str, tuple[str, ...]] = {}
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

    def bind_navigation_controller(self, navigation_controller: Any) -> None:
        """Observe the canonical viewport zoom to keep annotation density readable."""
        if navigation_controller is None:
            raise ValueError("navigation_controller must not be None")
        add_listener = getattr(navigation_controller, "add_zoom_changed_listener", None)
        remove_listener = getattr(navigation_controller, "remove_zoom_changed_listener", None)
        get_zoom_level = getattr(navigation_controller, "get_zoom_level", None)
        if not callable(add_listener) or not callable(remove_listener) or not callable(get_zoom_level):
            raise TypeError("navigation_controller must expose zoom listener and state APIs")
        if self._navigation_controller is navigation_controller:
            self.set_zoom_level(get_zoom_level())
            return
        self._unbind_navigation_controller()
        self._navigation_controller = navigation_controller
        self.set_zoom_level(get_zoom_level())
        add_listener(self.set_zoom_level)

    def _unbind_navigation_controller(self) -> None:
        controller = self._navigation_controller
        self._navigation_controller = None
        remove_listener = getattr(controller, "remove_zoom_changed_listener", None)
        if callable(remove_listener):
            remove_listener(self.set_zoom_level)

    def set_zoom_level(self, level: float) -> None:
        """Update transient annotation visibility without changing saved SLD settings."""
        if isinstance(level, bool) or not isinstance(level, (int, float)):
            raise TypeError("zoom level must be numeric")
        level = float(level)
        if not math.isfinite(level) or level <= 0.0:
            raise ValueError("zoom level must be finite and greater than zero")
        self._zoom_level = level
        annotations_visible_at_zoom = level >= self._annotation_min_zoom
        if annotations_visible_at_zoom == self._annotations_zoom_visible:
            return
        self._annotations_zoom_visible = annotations_visible_at_zoom
        for render_id, base_visible in tuple(self._annotation_base_visibility.items()):
            items = self._items.get(render_id, ())
            for item in items:
                if item is not None:
                    item.setVisible(base_visible and annotations_visible_at_zoom)

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

    def bind_selection_manager(self, selection_manager: Any) -> None:
        """Bind the canonical transient SelectionManager for presentation reconciliation."""
        if selection_manager is None:
            raise ValueError("selection_manager must not be None")
        if not callable(getattr(selection_manager, "get_selected_ids", None)):
            raise TypeError("selection_manager must expose get_selected_ids().")
        if not callable(getattr(selection_manager, "is_selected", None)):
            raise TypeError("selection_manager must expose is_selected().")
        self._selection_manager = selection_manager

    @property
    def selection_manager(self) -> Any:
        """Return the canonical selection projection dependency, if bound."""
        return self._selection_manager

    def _restore_node_selection(self, node: Any, item: Any) -> None:
        """Project canonical Core selection onto the current permanent item."""
        equipment_id = getattr(node, "equipment_id", None)
        if equipment_id is None or self._selection_manager is None:
            return
        selected = bool(self._selection_manager.is_selected(str(equipment_id)))
        setter = getattr(item, "set_visual_selected", None)
        if callable(setter):
            setter(selected)
            return
        setter = getattr(item, "set_graphical_selected", None)
        if callable(setter):
            setter(selected)
            return
        setter = getattr(item, "setSelected", None)
        if callable(setter):
            setter(selected)

    def _restore_connection_selection(self, connection: Any, item: Any) -> None:
        """Project canonical Core connection selection onto a recreated item.

        Renderer reconciliation is presentation-only: the SelectionManager remains
        the sole semantic selection authority, and the persistent SLD presentation
        identity is never used to decide selection.
        """
        if self._selection_manager is None:
            return
        core_connection_id = getattr(connection, "properties", {}).get("core_connection_id")
        if core_connection_id is None:
            return
        selected = bool(self._selection_manager.is_selected(str(core_connection_id)))
        setter = getattr(item, "setSelected", None)
        if callable(setter):
            setter(selected)
            refresh = getattr(item, "_refresh_pen", None)
            if callable(refresh):
                refresh()
            return
        setter = getattr(item, "set_visual_selected", None)
        if callable(setter):
            setter(selected)
            return
        setter = getattr(item, "set_graphical_selected", None)
        if callable(setter):
            setter(selected)

    def bind_route_edit_controller(self, controller: Any) -> None:
        """Bind the existing route-edit controller to realized connection items."""
        if controller is None or not callable(getattr(controller, "handle_route_edit_request", None)):
            raise TypeError("route edit controller must expose handle_route_edit_request().")
        if self._route_edit_controller is controller:
            return
        self._unbind_route_edit_controller()
        self._route_edit_controller = controller
        self._bind_route_edit_items()

    def _bind_route_edit_items(self) -> None:
        controller = self._route_edit_controller
        if controller is None:
            return
        callback = controller.handle_route_edit_request
        for items in tuple(self._items.values()):
            for item in items:
                signal = getattr(item, "route_edit_requested", None)
                if signal is not None and callable(getattr(signal, "connect", None)):
                    signal.connect(callback)

    def _unbind_route_edit_item(self, item: Any) -> None:
        controller = self._route_edit_controller
        if controller is None:
            return
        signal = getattr(item, "route_edit_requested", None)
        disconnect = getattr(signal, "disconnect", None) if signal is not None else None
        if callable(disconnect):
            try:
                disconnect(controller.handle_route_edit_request)
            except (RuntimeError, TypeError):
                pass

    def _unbind_route_edit_controller(self) -> None:
        controller = self._route_edit_controller
        if controller is None:
            return
        for items in tuple(self._items.values()):
            for item in items:
                self._unbind_route_edit_item(item)
        self._route_edit_controller = None

    def synchronize(self, snapshot: SLDCanvasSnapshot | CompositeSLDCanvasSnapshot) -> None:
        """Incrementally reconcile the scene with one complete immutable snapshot."""
        if isinstance(snapshot, CompositeSLDCanvasSnapshot):
            committed = snapshot.committed
            draft = snapshot.draft
        elif isinstance(snapshot, SLDCanvasSnapshot):
            committed = snapshot
            draft = DraftSLDCanvasSnapshot(nodes=(), connections=())
        else:
            raise TypeError("snapshot must be an SLDCanvasSnapshot or CompositeSLDCanvasSnapshot")
        if not isinstance(draft, DraftSLDCanvasSnapshot):
            raise TypeError("CompositeSLDCanvasSnapshot.draft must be a DraftSLDCanvasSnapshot")

        self._unsupported_presentations.clear()
        self._unsupported_connections.clear()
        self._render_diagnostics = ()

        desired_ids = {node.node_id for node in committed.nodes}
        desired_ids.update(connection.connection_id for connection in committed.connections)
        desired_ids.update(self._annotation_render_id(annotation.block_id) for annotation in committed.annotations)
        desired_ids.update(self._draft_render_id(node.draft_id) for node in draft.nodes)
        desired_ids.update(self._draft_render_id(connection.connection_id) for connection in draft.connections)
        for diagnostic_id in tuple(self._reported_diagnostics):
            if diagnostic_id not in desired_ids:
                self._reported_diagnostics.pop(diagnostic_id, None)
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
        for node in committed.nodes:
            signature = self._node_signature(node)
            if (
                self._render_signatures.get(node.node_id) == signature
                and node.node_id in self._items
                and node.node_id not in self._degraded_node_ids
            ):
                realized[node.node_id] = self._items[node.node_id][0]
                self._restore_node_selection(node, realized[node.node_id])
                continue

            # A degraded placeholder is not a successful realization. Retry it
            # on the next explicit snapshot synchronization, but retain the
            # current visible item until a replacement is ready.
            previous_degraded = (
                self._items.get(node.node_id, (None,))[0]
                if node.node_id in self._degraded_node_ids else None
            )
            # Preserve the current item until the replacement is realized.
            previous_items = self._items.get(node.node_id, ())
            previous_item = previous_items[0] if previous_items else None
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
                self._record_diagnostic(node.node_id, diagnostic)
                self._degraded_diagnostics[node.node_id] = diagnostic
                degraded = previous_degraded
                if degraded is None and previous_item is not None:
                    # Retain the last-good visible item, but leave its prior
                    # signature untouched so the next synchronization retries.
                    previous_item.setToolTip(
                        f"SLD refresh failed [{code}]\n"
                        f"node={node.node_id} equipment={getattr(previous_item, 'object_id', node.node_id)}\n{message}"
                    )
                    self._degraded_node_ids.add(node.node_id)
                    realized[node.node_id] = previous_item
                    self._restore_node_selection(node, previous_item)
                    continue
                if degraded is None:
                    degraded = self._create_degraded_realization(node, message, code)
                    self._scene.addItem(degraded)
                    self._items[node.node_id] = (degraded,)
                else:
                    degraded.setToolTip(
                        f"Unsupported presentation [{code}]\n"
                        f"node={node.node_id} equipment={getattr(degraded, 'object_id', node.node_id)}\n{message}"
                    )
                self._render_signatures[node.node_id] = signature
                self._degraded_node_ids.add(node.node_id)
                realized[node.node_id] = degraded
                self._restore_node_selection(node, degraded)
                continue
            if callable(getattr(item, "set_visual_state", None)):
                item.set_visual_state(VisualState.NORMAL)
            self._attach_realized_item(item, register_snap=True)
            if previous_item is not None:
                self._remove_realized(node.node_id)
            self._items[node.node_id] = (item,)
            self._render_signatures[node.node_id] = signature
            self._degraded_diagnostics.pop(node.node_id, None)
            self._clear_reported_diagnostic(node.node_id)
            self._degraded_node_ids.discard(node.node_id)
            realized[node.node_id] = item
            self._restore_node_selection(node, item)

        # Draft nodes are realized after committed nodes but before either
        # connection set, so one shared scene/registry can resolve mixed endpoints.
        for node in draft.nodes:
            render_id = self._draft_render_id(node.draft_id)
            signature = self._draft_node_signature(node)
            if (
                self._render_signatures.get(render_id) == signature
                and render_id in self._items
                and render_id not in self._degraded_node_ids
            ):
                realized[render_id] = self._items[render_id][0]
                continue
            # A fallback is visible but is not a successful symbol realization.
            # Keep it in place until a real symbol can replace it.
            previous_degraded = (
                self._items.get(render_id, (None,))[0]
                if render_id in self._degraded_node_ids else None
            )
            if render_id in self._items and previous_degraded is None:
                self._remove_realized(render_id)
            try:
                item = self._draft_presentation_factory.create_node(node)
                item.setZValue(1.0)
                self._attach_realized_item(item, register_snap=True)
                if previous_degraded is not None:
                    self._remove_realized(render_id)
                self._items[render_id] = (item,)
                self._render_signatures[render_id] = signature
                self._clear_reported_diagnostic(render_id)
                self._degraded_node_ids.discard(render_id)
                realized[render_id] = item
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                code = "DRAFT_PRESENTATION_REALIZATION_FAILED"
                symbol_id = None
                # Diagnose catalogue failures by the failing lookup stage rather
                # than parsing exception text; retain the original realization
                # exception as the primary failure.
                try:
                    definition = self._item_factory.equipment_registry.require(
                        node.equipment_type
                    )
                except KeyError as lookup_error:
                    code = "DRAFT_EQUIPMENT_DEFINITION_MISSING"
                    message = f"{message}; equipment catalogue lookup: {lookup_error}"
                else:
                    symbol_id = definition.symbol_id
                    try:
                        self._item_factory.symbol_registry.require(symbol_id)
                    except KeyError as lookup_error:
                        code = "DRAFT_SYMBOL_DEFINITION_MISSING"
                        message = f"{message}; symbol catalogue lookup: {lookup_error}"
                self._unsupported_presentations[render_id] = message
                diagnostic = RenderDiagnostic(
                    node_id=render_id,
                    equipment_id=node.draft_id,
                    equipment_type=node.equipment_type,
                    symbol_id=symbol_id,
                    requested_presentation="symbol",
                    category="draft_presentation_realization",
                    message=message,
                    code=code,
                    realization_stage="DraftPresentationFactory -> SymbolPreviewItem",
                )
                self._record_diagnostic(render_id, diagnostic)
                # A failed symbol lookup must not make placed draft equipment
                # silently disappear. Keep a selectable, visible fallback in
                # the same scene and expose the underlying error as its tooltip.
                fallback = previous_degraded
                if fallback is None:
                    fallback = QGraphicsRectItem(-70.0, -34.0, 140.0, 68.0)
                    fallback.object_id = node.draft_id
                    fallback.draft_id = node.draft_id
                    fallback.is_draft_presentation = True
                    fallback.setPos(float(node.x), float(node.y))
                    fallback.setZValue(1.0)
                    label = QGraphicsTextItem(
                        f"Symbol unavailable\n{node.display_name}", fallback
                    )
                    label.setPos(-62.0, -24.0)
                    fallback.setFlag(
                        QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True
                    )
                    fallback.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
                    self._scene.addItem(fallback)
                    self._items[render_id] = (fallback,)
                fallback.setToolTip(
                    f"Draft symbol unavailable [{code}]\n"
                    f"draft={node.draft_id} type={node.equipment_type}\n{message}"
                )
                self._render_signatures[render_id] = signature
                self._degraded_node_ids.add(render_id)
                realized[render_id] = fallback

        node_by_id = {node.node_id: node for node in committed.nodes}
        for connection in committed.connections:
            signature = self._connection_signature(connection, node_by_id)
            if self._render_signatures.get(connection.connection_id) == signature and connection.connection_id in self._items:
                self._restore_connection_selection(connection, self._items[connection.connection_id][0])
                continue
            previous_items = self._items.get(connection.connection_id, ())
            previous_item = previous_items[0] if previous_items else None
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
            item = None
            try:
                item = self._item_factory.create_connection(connection, source, target)
                item.set_visual_route(source, target, route_points, ownership=connection.route.ownership)
                if self._route_edit_controller is not None:
                    item.route_edit_requested.connect(
                        self._route_edit_controller.handle_route_edit_request
                    )
                if callable(getattr(item, "set_visual_state", None)):
                    item.set_visual_state(VisualState.NORMAL)
                self._restore_connection_selection(connection, item)
                self._attach_realized_item(item)
                if previous_item is not None:
                    self._remove_realized(connection.connection_id)
                self._items[connection.connection_id] = (item,)
                self._render_signatures[connection.connection_id] = signature
                self._clear_reported_diagnostic(connection.connection_id)
            except Exception as exc:
                if item is not None:
                    self._unbind_route_edit_item(item)
                self._record_connection_failure(
                    connection, "CONNECTION_REALIZATION_FAILED",
                    f"{type(exc).__name__}: {exc}"
                )

        for connection in draft.connections:
            render_id = self._draft_render_id(connection.connection_id)
            try:
                # Resolve endpoint geometry before comparing signatures. A
                # draft node can move while the wire's endpoint identities stay
                # unchanged; geometry must therefore participate in the
                # reconciliation decision or the visible wire remains stale.
                source, source_id = self._resolve_draft_endpoint(connection.source, realized)
                target, target_id = self._resolve_draft_endpoint(connection.target, realized)
                signature = self._draft_connection_signature(
                    connection,
                    source_position=(source.x(), source.y()),
                    target_position=(target.x(), target.y()),
                )
                if (
                    self._render_signatures.get(render_id) == signature
                    and render_id in self._items
                ):
                    continue
                if render_id in self._items:
                    self._remove_realized(render_id)
                item = self._item_factory.create_draft_connection(
                    connection,
                    source,
                    target,
                    source_object_id=source_id,
                    target_object_id=target_id,
                )
                if callable(getattr(item, "set_visual_state", None)):
                    item.set_visual_state(VisualState.NORMAL)
                self._scene.addItem(item)
                self._items[render_id] = (item,)
                self._render_signatures[render_id] = signature
                self._clear_reported_diagnostic(render_id)
            except Exception as exc:
                # If endpoint resolution or recreation fails, do not leave a
                # previously realized wire at obsolete endpoint coordinates.
                if render_id in self._items:
                    self._remove_realized(render_id)
                self._record_draft_connection_failure(
                    connection,
                    "DRAFT_CONNECTION_REALIZATION_FAILED",
                    f"{type(exc).__name__}: {exc}",
                )

        # Annotation graphics are transient and derived from projected
        # Application read-model values plus persisted SLD presentation config.
        for annotation in committed.annotations:
            render_id = self._annotation_render_id(annotation.block_id)
            signature = self._annotation_signature(annotation)
            if self._render_signatures.get(render_id) == signature and render_id in self._items:
                continue
            previous_items = self._items.get(render_id, ())
            previous_item = previous_items[0] if previous_items else None
            item = QGraphicsTextItem(annotation.text)
            # Data labels are display-only; they must not intercept selection,
            # connection, or placement gestures intended for underlying SLD items.
            item.setAcceptedMouseButtons(Qt.NoButton)
            item.setPos(float(annotation.x), float(annotation.y))
            item.setVisible(bool(annotation.visible) and self._zoom_level >= self._annotation_min_zoom)
            item.setZValue(5.0)
            self._attach_realized_item(item)
            if previous_item is not None:
                self._remove_realized(render_id)
            self._annotation_base_visibility[render_id] = bool(annotation.visible)
            self._items[render_id] = (item,)
            self._render_signatures[render_id] = signature

    @staticmethod
    def _annotation_render_id(block_id: str) -> str:
        return f"annotation:{block_id}"

    @staticmethod
    def _annotation_signature(annotation: SLDCanvasAnnotation) -> str:
        return repr((
            annotation.block_id, annotation.node_id, annotation.x, annotation.y,
            annotation.text, annotation.visible,
        ))

    @staticmethod
    def _draft_render_id(identity: str) -> str:
        return f"draft:{identity}"

    @staticmethod
    def _draft_node_signature(node: DraftSLDCanvasNode) -> str:
        return repr((node.draft_id, node.equipment_type, node.display_name, node.x, node.y,
                     node.rotation, node.terminal_roles, node.presentation, node.validation_state))

    @staticmethod
    def _draft_connection_signature(
        connection: DraftSLDCanvasConnection,
        *,
        source_position: tuple[float, float],
        target_position: tuple[float, float],
    ) -> str:
        return repr((
            connection.connection_id,
            connection.source,
            connection.target,
            source_position,
            target_position,
            connection.connection_kind,
            connection.route,
            connection.validation_state,
        ))

    def _resolve_draft_endpoint(self, endpoint: Any, realized: dict[str, Any]) -> tuple[QPointF, str]:
        """Resolve Draft/Core endpoint identity through already-realized presentation items."""
        if getattr(endpoint, "is_terminal", False):
            if getattr(endpoint, "scope", "draft") == "draft":
                render_id = self._draft_render_id(str(endpoint.object_id))
                item = realized.get(render_id)
                if item is None:
                    raise KeyError(f"No realized draft item for {endpoint.object_id!r}")
                candidates = tuple(getattr(item, "snap_points", lambda: ())())
                matches = tuple(
                    candidate for candidate in candidates
                    if str(candidate.get("draft_id")) == str(endpoint.object_id)
                    and str(candidate.get("draft_terminal_role")) == str(endpoint.terminal_role)
                )
                object_id = str(endpoint.object_id)
            else:
                object_id = str(endpoint.object_id)
                item = next((value for value in realized.values()
                             if str(getattr(value, "object_id", "")) == object_id), None)
                if item is None:
                    raise KeyError(f"No realized Core item for {object_id!r}")
                candidates = tuple(getattr(item, "snap_points", lambda: ())())
                matches = tuple(
                    candidate for candidate in candidates
                    if str(candidate.get("object_id")) == object_id
                    and str(candidate.get("terminal_name")) == str(endpoint.terminal_role)
                )
        elif getattr(endpoint, "is_bus", False):
            object_id = str(endpoint.object_id)
            item = next((value for value in realized.values()
                         if str(getattr(value, "object_id", "")) == object_id), None)
            if item is None:
                raise KeyError(f"No realized Bus item for {object_id!r}")
            candidates = tuple(getattr(item, "snap_points", lambda: ())())
            matches = tuple(
                candidate for candidate in candidates
                if str(candidate.get("bus_id")) == object_id
                and str(candidate.get("attachment_id")) == str(endpoint.attachment_id)
            )
        else:
            raise TypeError(f"Unsupported draft endpoint: {endpoint!r}")
        if len(matches) != 1:
            raise ValueError(f"Endpoint {endpoint.to_dict()!r} resolved to {len(matches)} presentation candidates")
        position = matches[0].get("position")
        if position is None:
            raise ValueError("Resolved endpoint has no scene position")
        return QPointF(float(position.x()), float(position.y())), object_id

    def _record_diagnostic(self, identity: str, diagnostic: RenderDiagnostic) -> None:
        """Keep active diagnostics visible while reporting each unchanged failure once."""
        self._render_diagnostics = (*self._render_diagnostics, diagnostic)
        key = (
            diagnostic.category,
            diagnostic.node_id,
            diagnostic.connection_id or "",
            diagnostic.code,
            diagnostic.message,
        )
        if self._reported_diagnostics.get(identity) == key:
            return
        self._reported_diagnostics[identity] = key
        if self._diagnostic_sink is not None:
            self._diagnostic_sink(diagnostic)

    def _clear_reported_diagnostic(self, identity: str) -> None:
        self._reported_diagnostics.pop(identity, None)

    def _record_draft_connection_failure(self, connection: Any, code: str, message: str) -> None:
        render_id = self._draft_render_id(connection.connection_id)
        self._unsupported_connections[render_id] = message
        diagnostic = RenderDiagnostic(
            node_id=render_id,
            equipment_id=None,
            equipment_type=None,
            symbol_id=None,
            requested_presentation=None,
            category="draft_connection_realization",
            message=message,
            connection_id=render_id,
            code=code,
        )
        self._record_diagnostic(render_id, diagnostic)

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
        self._record_diagnostic(connection.connection_id, diagnostic)

    def _create_degraded_realization(self, node: Any, message: str, code: str) -> Any:
        """Create a visible/selectable presentation fallback without Core mutation."""
        item = QGraphicsRectItem(-70.0, -34.0, 140.0, 68.0)
        item.object_id = node.equipment_id or node.node_id
        item.node_id = node.node_id
        item.setToolTip(
            f"Unsupported presentation [{code}]\n"
            f"node={node.node_id} equipment={item.object_id}\n{message}"
        )
        text = QGraphicsTextItem(f"Unsupported Symbol\n{item.object_id}", item)
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
        read_model = node.read_model
        read_model_signature = None if read_model is None else (
            read_model.object_id,
            read_model.element_type,
            tuple(sorted((str(key), str(value)) for key, value in read_model.labels.items())),
            tuple(read_model.connectivity_refs),
            tuple(sorted((str(key), repr(value)) for key, value in read_model.attributes.items())),
            repr(read_model.engineering_parameters),
        )
        return repr((
            node.node_id, node.equipment_id, node.x, node.y,
            presentation, properties, read_model_signature,
        ))

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

    def _attach_realized_item(self, item: Any, *, register_snap: bool = False) -> None:
        """Attach a transient item atomically with its optional snap registration.

        If registration fails after scene insertion, roll back both presentation
        resources before propagating the failure to the caller.
        """
        self._scene.addItem(item)
        try:
            if (
                register_snap
                and self._snap_system is not None
                and callable(getattr(item, "snap_points", None))
            ):
                self._snap_system.register_item(item)
        except Exception:
            try:
                self._snap_system.unregister_item(item)
            except Exception:
                # Preserve the attachment failure; scene rollback still matters.
                pass
            finally:
                if item.scene() is self._scene:
                    self._scene.removeItem(item)
            raise

    def _remove_realized(self, item_id: str) -> None:
        items = self._items.pop(item_id, ())
        try:
            for item in items:
                self._unbind_route_edit_item(item)
                try:
                    if self._snap_system is not None and callable(getattr(self._snap_system, "unregister_item", None)):
                        self._snap_system.unregister_item(item)
                finally:
                    if item is not None and item.scene() is self._scene:
                        self._scene.removeItem(item)
        finally:
            self._render_signatures.pop(item_id, None)
            self._annotation_base_visibility.pop(item_id, None)
            self._degraded_diagnostics.pop(item_id, None)
            self._clear_reported_diagnostic(item_id)
            self._degraded_node_ids.discard(item_id)

    def clear(self) -> None:
        for items in tuple(self._items.values()):
            for item in items:
                self._unbind_route_edit_item(item)
                if self._snap_system is not None and callable(getattr(self._snap_system, "unregister_item", None)):
                    self._snap_system.unregister_item(item)
                if item is not None and item.scene() is self._scene:
                    self._scene.removeItem(item)
        if self._snap_system is not None and callable(getattr(self._snap_system, "clear_candidates", None)):
            self._snap_system.clear_candidates()
        self._items.clear()
        self._render_signatures.clear()
        self._annotation_base_visibility.clear()
        self._degraded_node_ids.clear()
        self._degraded_diagnostics.clear()
        self._reported_diagnostics.clear()
        self._unsupported_presentations.clear()
        self._unsupported_connections.clear()
        self._render_diagnostics = ()

    def dispose(self) -> None:
        self._unbind_navigation_controller()
        self.clear()
        self._unbind_route_edit_controller()


__all__ = ["RenderDiagnostic", "SLDCanvasRenderSystem"]
