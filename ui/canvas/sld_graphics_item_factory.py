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

    def __init__(self, equipment_registry: EquipmentRegistry, symbol_registry: SymbolRegistry, application: object) -> None:
        if not isinstance(equipment_registry, EquipmentRegistry):
            raise TypeError("equipment_registry must be an EquipmentRegistry")
        if not isinstance(symbol_registry, SymbolRegistry):
            raise TypeError("symbol_registry must be a SymbolRegistry")
        if application is None or not callable(getattr(application, "read_network", None)):
            raise TypeError("application must provide the Application read-model API.")
        equipment_registry.validate_symbol_anchors(symbol_registry)
        self._equipment_registry = equipment_registry
        self._symbol_registry = symbol_registry
        self._application = application
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
            start, end = self._bus_span(node)
            item = BusItem(
                object_id=graphics_object_id,
                position=position,
                radius=self._node_radius(node),
                start=start,
                end=end,
            )
            item.setScale(symbol_instance.scale)
            item.setRotation(float(node.properties.get("orientation", symbol_instance.rotation)))
            item.setVisible(symbol_instance.visible)
            return item

        definition = self._symbol_registry.require(symbol_instance.symbol_id)
        read_model = self._read_model_for(node.equipment_id)
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
        )
        route = connection.route
        item.set_visual_route(source, target, route.points, ownership=route.ownership)
        return item

    def _read_model_for(self, equipment_id: str | None) -> ElementReadModel:
        if not isinstance(equipment_id, str) or not equipment_id:
            raise ValueError("Renderable equipment nodes require a canonical equipment_id.")
        network = self._application.read_network()
        for element in network.elements:
            if element.object_id == equipment_id:
                return element
        protection_reader = getattr(self._application, "read_protection", None)
        if callable(protection_reader):
            protection = protection_reader()
            for relay in protection.relays:
                if relay.object_id == equipment_id:
                    return ElementReadModel(
                        object_id=relay.object_id,
                        element_type="RELAY",
                        labels={"name": relay.name},
                        connectivity_refs=(),
                        attributes={},
                    )
        raise ValueError(f"SLD node equipment {equipment_id!r} is absent from Application read state.")

    @staticmethod
    def _bus_span(node: SLDCanvasNode) -> tuple[QPointF, QPointF]:
        raw_start = node.properties.get("start", DEFAULT_SLD_BUS_PRESENTATION.start)
        raw_end = node.properties.get("end", DEFAULT_SLD_BUS_PRESENTATION.end)
        if not isinstance(raw_start, (tuple, list)) or len(raw_start) != 2:
            raise ValueError("SLD Bus start geometry must be a two-element sequence")
        if not isinstance(raw_end, (tuple, list)) or len(raw_end) != 2:
            raise ValueError("SLD Bus end geometry must be a two-element sequence")
        return QPointF(float(raw_start[0]), float(raw_start[1])), QPointF(float(raw_end[0]), float(raw_end[1]))

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
