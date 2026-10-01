# ============================================================
# File: ui/canvas/sld_graphics_item_factory.py
# GridForge V2 — SLD Graphics Item Factory
# Author: Subhendu Mishra
# ============================================================

"""Construct presentation-only graphics items from resolved SLD descriptors."""

from __future__ import annotations

from core.application.read_models import ElementReadModel
from ui.core.qt import QPointF
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.equipment_factory import EquipmentFactory
from ui.items.bus_item import BusItem
from ui.items.equipment_item import EquipmentItem
from ui.sld.items.sld_connection_item import SLDConnectionItem

from .semantic_presentation_realization import PresentationSelection
from ui.sld.bus_presentation import DEFAULT_SLD_BUS_PRESENTATION
from .sld_canvas_projection import SLDCanvasConnection, SLDCanvasNode


class SLDGraphicsItemFactory:
    """Construction boundary between resolved descriptors and graphics."""

    def __init__(
        self,
        equipment_registry: EquipmentRegistry,
        symbol_registry: SymbolRegistry,
    ) -> None:
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
        symbol_instance = selection.symbol_instance
        if symbol_instance is None:
            raise ValueError("PresentationSelection must contain a canonical symbol instance.")
        if selection.representation_id != symbol_instance.representation_id:
            raise ValueError("Presentation selection representation does not match its symbol instance.")
        if selection.representation_id != "symbol":
            raise ValueError(f"Unsupported SLD representation: {selection.representation_id!r}")

        if selection.equipment_type == "bus":
            definition = self._bus_definition(node)
            start = QPointF(*definition.start)
            end = QPointF(*definition.end)
            item = BusItem(
                object_id=graphics_object_id,
                position=position,
                radius=self._node_radius(node),
                start=start,
                end=end,
                attachment_count=definition.attachment_count,
            )
            item.setScale(symbol_instance.scale)
            item.setRotation(definition.orientation_deg + symbol_instance.rotation)
            item.setScale(symbol_instance.scale * (-1.0 if symbol_instance.get_property("mirror_x", False) else 1.0))
            item.setVisible(symbol_instance.visible)
            return item

        definition = self._symbol_registry.require(symbol_instance.symbol_id)
        read_model = self._read_model_for_node(node, selection.equipment_type)
        equipment = self._equipment_factory.create_from_read_model(
            read_model,
            selection.equipment_type,
            position=(node.x, node.y),
            symbol_instance=symbol_instance,
        )
        return EquipmentItem(
            object_id=graphics_object_id,
            element_type=selection.semantic_type,
            position=position,
            symbol_definition=definition,
            equipment=equipment,
            symbol_instance=symbol_instance,
        )

    def create_connection(self, connection: SLDCanvasConnection, source: QPointF, target: QPointF) -> SLDConnectionItem:
        if not isinstance(connection, SLDCanvasConnection):
            raise TypeError("connection must be an SLDCanvasConnection")
        self._validate_point(source, "source")
        self._validate_point(target, "target")
        item = SLDConnectionItem(
            object_id=connection.connection_id,
            source_object_id=connection.source_node_id,
            target_object_id=connection.target_node_id,
            source_endpoint=connection.source_endpoint,
            target_endpoint=connection.target_endpoint,
            connection_kind=connection.connection_kind,
            presentation_owner=connection.presentation_owner,
            projection_source=connection.projection_source,
        )
        route = connection.route
        item.set_visual_route(source, target, route.points, ownership=route.ownership)
        return item

    @staticmethod
    def _read_model_for_node(node: SLDCanvasNode, equipment_type: str) -> ElementReadModel:
        """Build a presentation snapshot only from the projected SLD node.

        The graphics factory is deliberately downstream of the Application
        read/projection boundary. It must never query Application/Core state to
        decide whether an already-projected SLD node is renderable.
        """
        equipment_id = node.equipment_id or str(
            node.properties.get("equipment_id") or node.node_id
        )
        if not equipment_id:
            raise ValueError("Renderable equipment nodes require a stable equipment identity.")

        properties = dict(node.properties)
        projected_labels = properties.pop("labels", {})
        projected_attributes = properties.pop("attributes", {})
        terminal_ids = properties.pop(
            "terminal_ids",
            properties.pop("connectivity_refs", ()),
        )
        element_type = properties.pop("element_type", equipment_type)

        labels = dict(projected_labels) if isinstance(projected_labels, Mapping) else {}
        attributes = dict(projected_attributes) if isinstance(projected_attributes, Mapping) else {}
        if "name" in properties and "name" not in labels:
            labels["name"] = str(properties.pop("name"))
        if not labels:
            labels["name"] = str(equipment_id)

        if not isinstance(terminal_ids, (tuple, list)):
            terminal_ids = ()
        attributes.update(properties)

        return ElementReadModel(
            object_id=str(equipment_id),
            element_type=str(element_type),
            labels=labels,
            connectivity_refs=tuple(str(value) for value in terminal_ids),
            attributes=attributes,
        )

    @staticmethod
    def _bus_definition(node: SLDCanvasNode):
        return DEFAULT_SLD_BUS_PRESENTATION.from_mapping(node.properties)

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
