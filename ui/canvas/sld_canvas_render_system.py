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
from ui.items.bus_item import BusItem
from ui.items.line_item import LineItem

from .sld_canvas_projection import SLDCanvasSnapshot


class SLDCanvasRenderSystem:
    """Render an :class:`SLDCanvasSnapshot` into a QGraphicsScene."""

    NODE_RADIUS = 8.0
    NODE_PEN_WIDTH = 1.5
    CONNECTION_PEN_WIDTH = 2.0

    def __init__(self, scene: QGraphicsScene) -> None:
        if scene is None:
            raise ValueError("scene must not be None.")
        self._scene = scene
        self._items: dict[str, tuple[Any, ...]] = {}

    @property
    def scene(self) -> QGraphicsScene:
        """Return the target scene."""
        return self._scene

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

            item = LineItem(
                object_id=connection.connection_id,
                start=source,
                end=target,
            )
            item.set_pen(self._pen(self.CONNECTION_PEN_WIDTH))
            self._scene.addItem(item)
            self._items[connection.connection_id] = (item,)

        for node in snapshot.nodes:
            item = BusItem(
                object_id=node.node_id,
                position=QPointF(node.x, node.y),
                radius=self._node_radius(node),
            )
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

    @classmethod
    def _node_radius(cls, node: Any) -> float:
        """Read optional visual radius from presentation properties."""
        value = node.properties.get("radius", cls.NODE_RADIUS)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return cls.NODE_RADIUS
        if value <= 0:
            return cls.NODE_RADIUS
        return float(value)


__all__ = ["SLDCanvasRenderSystem"]
