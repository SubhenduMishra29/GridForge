# ============================================================
# File: ui/canvas/sld_canvas_render_system.py
# GridForge V2 — SLD Canvas Render System
# Author: Subhendu Mishra
# ============================================================

"""Realize an SLD canvas snapshot as transient graphics projections.

The render system is downstream of :class:`SLDCanvasProjection`. It consumes
only renderer-neutral SLD canvas snapshots and realizes them as specialized
presentation graphics. BusItem and LineItem are graphics implementations, not
sources of electrical truth.
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import QGraphicsScene, QPen, QPointF

from .sld_canvas_projection import SLDCanvasSnapshot
from .sld_graphics_item_factory import SLDGraphicsItemFactory


class SLDCanvasRenderSystem:
    """Render an :class:`SLDCanvasSnapshot` into a QGraphicsScene."""

    NODE_RADIUS = 8.0
    NODE_PEN_WIDTH = 1.5
    CONNECTION_PEN_WIDTH = 2.0

    def __init__(
        self,
        scene: QGraphicsScene,
        item_factory: SLDGraphicsItemFactory | None = None,
    ) -> None:
        if scene is None:
            raise ValueError("scene must not be None.")
        self._scene = scene
        self._item_factory = item_factory or SLDGraphicsItemFactory()
        self._items: dict[str, tuple[Any, ...]] = {}

    @property
    def scene(self) -> QGraphicsScene:
        """Return the target scene."""
        return self._scene

    @property
    def item_factory(self) -> SLDGraphicsItemFactory:
        """Return the graphics-item construction boundary."""
        return self._item_factory

    @staticmethod
    def _pen(width: float) -> QPen:
        """Create a pen with a portable width-setting API."""
        pen = QPen()
        set_width_f = getattr(pen, "setWidthF", None)
        if callable(set_width_f):
            set_width_f(float(width))
        else:
            pen.setWidth(int(round(width)))
        return pen

    def synchronize(self, snapshot: SLDCanvasSnapshot) -> None:
        """Replace the graphical SLD projection from a renderer-neutral snapshot."""
        if not isinstance(snapshot, SLDCanvasSnapshot):
            raise TypeError("snapshot must be an SLDCanvasSnapshot.")

        self.clear()

        positions = {
            node.node_id: QPointF(node.x, node.y)
            for node in snapshot.nodes
        }

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
            item = self._item_factory.create_node(node)
            item.set_pen(self._pen(self.NODE_PEN_WIDTH))
            self._scene.addItem(item)
            self._items[node.node_id] = (item,)

    def clear(self) -> None:
        """Remove only graphics owned by this SLD realization."""
        for items in tuple(self._items.values()):
            for item in items:
                if item is not None and item.scene() is self._scene:
                    self._scene.removeItem(item)
        self._items.clear()

    def dispose(self) -> None:
        """Release the transient SLD graphical projection."""
        self.clear()


__all__ = ["SLDCanvasRenderSystem"]
