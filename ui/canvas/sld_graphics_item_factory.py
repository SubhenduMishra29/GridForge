# ============================================================
# File: ui/canvas/sld_graphics_item_factory.py
# GridForge V2 — SLD Graphics Item Factory
# Author: Subhendu Mishra
# ============================================================

"""Construct presentation-only graphics items for the SLD canvas."""

from __future__ import annotations

from ui.core.qt import QPointF
from ui.items.bus_item import BusItem
from ui.items.equipment_item import EquipmentItem
from ui.items.line_item import LineItem

from .semantic_presentation_realization import PresentationSelection
from .sld_canvas_projection import SLDCanvasConnection, SLDCanvasNode


class SLDGraphicsItemFactory:
    """Create typed SLD graphics projections from renderer-neutral descriptors."""

    _NODE_CONSTRUCTORS = {
        "bus": BusItem,
        "equipment": EquipmentItem,
    }

    def create_node(self, node: SLDCanvasNode, selection: PresentationSelection):
        if not isinstance(node, SLDCanvasNode):
            raise TypeError("node must be an SLDCanvasNode.")
        if not isinstance(selection, PresentationSelection):
            raise TypeError("selection must be a PresentationSelection.")
        item_class = self._NODE_CONSTRUCTORS.get(selection.representation_id)
        if item_class is None:
            raise ValueError(f"Unsupported presentation representation: {selection.representation_id}")
        if selection.representation_id == "equipment":
            element_type = node.properties.get("element_type")
            if node.equipment_id is None:
                # Presentation-only SLD nodes do not represent Core equipment.
                # Give the graphics item an explicitly presentation-scoped
                # identity; never reuse node_id as an engineering identity.
                graphics_object_id = f"presentation:{node.node_id}"
            else:
                graphics_object_id = node.equipment_id
            item = item_class(
                object_id=graphics_object_id,
                element_type=str(element_type),
                position=QPointF(node.x, node.y),
            )
        else:
            item = item_class(
                object_id=node.node_id,
                position=QPointF(node.x, node.y),
                radius=self._node_radius(node),
            )
        return item

    def create_connection(self, connection: SLDCanvasConnection, source: QPointF, target: QPointF) -> LineItem:
        if not isinstance(connection, SLDCanvasConnection):
            raise TypeError("connection must be an SLDCanvasConnection.")
        self._validate_point(source, "source")
        self._validate_point(target, "target")
        return LineItem(object_id=connection.connection_id, start=source, end=target)

    @staticmethod
    def _node_radius(node: SLDCanvasNode) -> float:
        value = node.properties.get("radius", BusItem.DEFAULT_RADIUS)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
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
