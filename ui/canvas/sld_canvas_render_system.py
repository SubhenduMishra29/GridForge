# ============================================================
# File: ui/canvas/sld_canvas_render_system.py
# GridForge V2 — SLD Canvas Render System
# Author: Subhendu Mishra
# ============================================================
"""Realize an SLD canvas snapshot as transient graphics projections.

This renderer is intentionally downstream of SLDCanvasProjection. It consumes
only renderer-neutral SLD canvas snapshots and never receives Core objects.
Existing BusItem and LineItem contracts are deliberately untouched; this
system provides the clean realization path for SLD document data.
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import (
    QBrush,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QPen,
    QPointF,
)

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

    def synchronize(self, snapshot: SLDCanvasSnapshot) -> None:
        """Replace the graphical SLD projection from a snapshot."""
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

            item = QGraphicsLineItem(
                source.x(),
                source.y(),
                target.x(),
                target.y(),
            )
            item.setPen(QPen(self.CONNECTION_PEN_WIDTH))
            self._scene.addItem(item)
            self._items[connection.connection_id] = (item,)

        for node in snapshot.nodes:
            item = QGraphicsEllipseItem(
                -self.NODE_RADIUS,
                -self.NODE_RADIUS,
                self.NODE_RADIUS * 2.0,
                self.NODE_RADIUS * 2.0,
            )
            item.setPos(node.x, node.y)
            item.setPen(QPen(self.NODE_PEN_WIDTH))
            item.setBrush(QBrush())
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
