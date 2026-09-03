# ============================================================
# File: ui/canvas/sld_graphics_item_factory.py
# GridForge V2 — SLD Graphics Item Factory
# Author: Subhendu Mishra
# ============================================================

"""Construct presentation-only graphics items for the SLD canvas.

This factory is deliberately narrower than a renderer or renderer registry.
It maps renderer-neutral SLD canvas descriptors to the locked graphics item
implementations. It does not perform layout, topology resolution, styling,
application commands, or Core-domain mutation.
"""

from __future__ import annotations

from ui.core.qt import QPointF
from ui.items.bus_item import BusItem
from ui.items.line_item import LineItem

from .sld_canvas_projection import SLDCanvasConnection, SLDCanvasNode


class SLDGraphicsItemFactory:
    """Create typed SLD graphics projections from renderer-neutral descriptors."""

    def create_node(self, node: SLDCanvasNode) -> BusItem:
        """Create the presentation projection for one SLD node."""
        if not isinstance(node, SLDCanvasNode):
            raise TypeError("node must be an SLDCanvasNode.")

        return BusItem(
            object_id=node.node_id,
            position=QPointF(node.x, node.y),
            radius=self._node_radius(node),
        )

    def create_connection(
        self,
        connection: SLDCanvasConnection,
        source: QPointF,
        target: QPointF,
    ) -> LineItem:
        """Create the presentation projection for one SLD connection."""
        if not isinstance(connection, SLDCanvasConnection):
            raise TypeError("connection must be an SLDCanvasConnection.")
        self._validate_point(source, "source")
        self._validate_point(target, "target")

        return LineItem(
            object_id=connection.connection_id,
            start=source,
            end=target,
        )

    @staticmethod
    def _node_radius(node: SLDCanvasNode) -> float:
        """Read optional presentation radius without introducing rendering policy."""
        value = node.properties.get("radius", BusItem.DEFAULT_RADIUS)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return BusItem.DEFAULT_RADIUS
        if value <= 0:
            return BusItem.DEFAULT_RADIUS
        return float(value)

    @staticmethod
    def _validate_point(point: QPointF, name: str) -> None:
        if point is None:
            raise ValueError(f"{name} must not be None.")
        if not callable(getattr(point, "x", None)):
            raise TypeError(f"{name} must provide x().")
        if not callable(getattr(point, "y", None)):
            raise TypeError(f"{name} must provide y().")


__all__ = ["SLDGraphicsItemFactory"]
