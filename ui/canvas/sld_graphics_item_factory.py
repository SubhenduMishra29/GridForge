# ============================================================
# File: ui/canvas/sld_graphics_item_factory.py
# GridForge V2 — SLD Graphics Item Factory
# Author: Subhendu Mishra
# ============================================================

"""Construct presentation-only graphics items from resolved SLD descriptors."""

from __future__ import annotations

from ui.core.qt import QPointF
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.equipment_factory import EquipmentFactory
from ui.items.bus_item import BusItem
from ui.items.equipment_item import EquipmentItem
from ui.items.line_item import LineItem

from .semantic_presentation_realization import PresentationSelection
from .sld_canvas_projection import SLDCanvasConnection, SLDCanvasNode


class SLDGraphicsItemFactory:
    """Construction boundary between resolved descriptors and graphics."""

    def __init__(self, equipment_registry: EquipmentRegistry, symbol_registry: SymbolRegistry) -> None:
        if not isinstance(equipment_registry, EquipmentRegistry):
            raise TypeError("equipment_registry must be an EquipmentRegistry")
        if not isinstance(symbol_registry, SymbolRegistry):
            raise TypeError("symbol_registry must be a SymbolRegistry")
        equipment_registry.validate_symbol_anchors(symbol_registry)
        self._equipment_registry = equipment_registry
        self._symbol_registry = symbol_registry
        self._equipment_factory = EquipmentFactory(equipment_registry, symbol_registry)

    @property
    def symbol_registry(self) -> SymbolRegistry:
        return self._symbol_registry

    def create_node(self, node: SLDCanvasNode, selection: PresentationSelection):
        if not isinstance(node, SLDCanvasNode):
            raise TypeError("node must be an SLDCanvasNode")
        if not isinstance(selection, PresentationSelection):
            raise TypeError("selection must be a PresentationSelection")
        graphics_object_id = node.equipment_id or f"presentation:{node.node_id}"
        position = QPointF(node.x, node.y)
        if selection.equipment_type == "bus":
            return BusItem(object_id=graphics_object_id, position=position,
                           radius=self._node_radius(node))
        definition = self._symbol_registry.require(selection.symbol_id)
        equipment = self._equipment_factory.create(
            selection.equipment_type,
            graphics_object_id,
            position=(node.x, node.y),
        )
        return EquipmentItem(object_id=graphics_object_id,
                             element_type=selection.semantic_type,
                             position=position,
                             symbol_definition=definition,
                             equipment=equipment)

    def create_connection(self, connection: SLDCanvasConnection, source: QPointF, target: QPointF) -> LineItem:
        if not isinstance(connection, SLDCanvasConnection):
            raise TypeError("connection must be an SLDCanvasConnection")
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
            raise ValueError(f"{name} must not be None")
        if not callable(getattr(point, "x", None)) or not callable(getattr(point, "y", None)):
            raise TypeError(f"{name} must provide x() and y()")


__all__ = ["SLDGraphicsItemFactory"]
