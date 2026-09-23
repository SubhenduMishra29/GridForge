# ============================================================
# File: ui/canvas/sld_canvas_render_system.py
# GridForge V2 — SLD Canvas Render System
# Author: Subhendu Mishra
# ============================================================
"""Realize renderer-neutral SLD snapshots into transient graphics."""

from __future__ import annotations

from typing import Any, Callable

from ui.core.qt import QGraphicsScene, QPen, QPointF

from .semantic_presentation_realization import SemanticPresentationRealization
from .sld_canvas_projection import SLDCanvasSnapshot
from .sld_graphics_item_factory import SLDGraphicsItemFactory


class SLDCanvasRenderSystem:
    """Render an SLD snapshot using explicitly composed dependencies."""

    NODE_PEN_WIDTH = 1.5
    CONNECTION_PEN_WIDTH = 2.0

    def __init__(self, scene: QGraphicsScene, item_factory: SLDGraphicsItemFactory,
                 semantic_realization: SemanticPresentationRealization,
                 on_node_realized: Callable[[str, Any], None] | None = None) -> None:
        if scene is None:
            raise ValueError("scene must not be None")
        if not isinstance(item_factory, SLDGraphicsItemFactory):
            raise TypeError("item_factory must be an SLDGraphicsItemFactory")
        if not isinstance(semantic_realization, SemanticPresentationRealization):
            raise TypeError("semantic_realization must be a SemanticPresentationRealization")
        self._scene = scene
        self._item_factory = item_factory
        self._semantic_realization = semantic_realization
        self._on_node_realized = on_node_realized
        self._items: dict[str, tuple[Any, ...]] = {}

    @property
    def scene(self) -> QGraphicsScene:
        return self._scene

    @property
    def item_factory(self) -> SLDGraphicsItemFactory:
        return self._item_factory

    @property
    def semantic_realization(self) -> SemanticPresentationRealization:
        return self._semantic_realization

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
        positions = {node.node_id: QPointF(node.x, node.y) for node in snapshot.nodes}
        for connection in snapshot.connections:
            source = positions.get(connection.source_node_id)
            target = positions.get(connection.target_node_id)
            if source is None or target is None:
                continue
            item = self._item_factory.create_connection(connection, source, target)
            item.set_pen(self._pen(self.CONNECTION_PEN_WIDTH))
            self._scene.addItem(item)
            self._items[connection.connection_id] = (item,)
        for node in snapshot.nodes:
            selection = self._semantic_realization.realize(node)
            item = self._item_factory.create_node(node, selection)
            item.set_pen(self._pen(self.NODE_PEN_WIDTH))
            self._scene.addItem(item)
            self._items[node.node_id] = (item,)
            if self._on_node_realized is not None:
                self._on_node_realized(node.node_id, item)

    def clear(self) -> None:
        for items in tuple(self._items.values()):
            for item in items:
                if item is not None and item.scene() is self._scene:
                    self._scene.removeItem(item)
        self._items.clear()

    def dispose(self) -> None:
        self.clear()


__all__ = ["SLDCanvasRenderSystem"]
