from __future__ import annotations

from types import SimpleNamespace

import pytest

from ui.canvas.semantic_presentation_realization import PresentationSelection
from ui.canvas.sld_canvas_projection import SLDCanvasConnection, SLDCanvasNode
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.built_in_symbol_catalogue import register_builtin_symbols
from ui.equipment.symbol.symbol_base import SymbolBase
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.sld.sld_model import SLDRoute
from ui.sld.items.sld_connection_item import SLDConnectionItem
from ui.items.bus_item import BusItem
from ui.core.qt import QPointF


class FakeApplication:
    def read_network(self):
        return SimpleNamespace(elements=())

    def read_protection(self):
        return SimpleNamespace(relays=())


def _factory():
    equipment = EquipmentRegistry.create_default()
    symbols = SymbolRegistry()
    register_builtin_symbols(symbols)
    return SLDGraphicsItemFactory(equipment, symbols, FakeApplication())


def _bus_selection(representation_id="symbol"):
    symbol = SymbolBase("bus", "bus", representation_id=representation_id)
    return PresentationSelection("BUS", "bus", "bus", representation_id=representation_id, symbol_instance=symbol)


def test_create_node_returns_bus_item_for_bus_selection():
    factory = _factory()
    node = SLDCanvasNode("bus-1", "equipment-1", 10.0, 20.0, {"element_type": "BUS"})
    item = factory.create_node(node, _bus_selection())
    assert isinstance(item, BusItem)
    assert item.object_id == "equipment-1"
    assert item.get_scene_position() == (10.0, 20.0)


def test_factory_rejects_missing_presentation_selection():
    factory = _factory()
    node = SLDCanvasNode("bus-1", "equipment-1", 10.0, 20.0, {"element_type": "BUS"})
    with pytest.raises(TypeError, match="selection"):
        factory.create_node(node, None)


def test_factory_rejects_unsupported_presentation_selection():
    factory = _factory()
    node = SLDCanvasNode("bus-1", "equipment-1", 10.0, 20.0, {"element_type": "BUS"})
    with pytest.raises(ValueError, match="representation"):
        factory.create_node(node, _bus_selection("unsupported"))


def test_create_connection_returns_presentation_connection_item():
    factory = _factory()
    connection = SLDCanvasConnection(
        connection_id="line-1",
        source_node_id="bus-1",
        target_node_id="bus-2",
        source_endpoint=None,
        target_endpoint=None,
        route=SLDRoute(),
        connection_kind="SIMPLE_WIRE",
        presentation_owner="SLD",
        projection_source="test",
        properties={"core_connection_id": "SIMPLE-WIRE-001"},
    )
    item = factory.create_connection(connection, QPointF(10.0, 20.0), QPointF(40.0, 50.0))
    assert isinstance(item, SLDConnectionItem)
    assert item.presentation_id == "line-1"
    assert item.core_connection_id == "SIMPLE-WIRE-001"
    assert item.object_id == "SIMPLE-WIRE-001"


def test_factory_rejects_invalid_node_descriptor():
    with pytest.raises(TypeError, match="SLDCanvasNode"):
        _factory().create_node(SimpleNamespace(node_id="bus-1"), _bus_selection())


def test_factory_rejects_invalid_connection_descriptor():
    with pytest.raises(TypeError, match="SLDCanvasConnection"):
        _factory().create_connection(SimpleNamespace(connection_id="line-1"), QPointF(), QPointF())

def test_factory_keeps_missing_core_connection_identity_non_selectable() -> None:
    factory = _factory()
    connection = SLDCanvasConnection(
        connection_id="line-orphan",
        source_node_id="bus-1",
        target_node_id="bus-2",
        source_endpoint=None,
        target_endpoint=None,
        route=SLDRoute(),
        connection_kind="SIMPLE_WIRE",
        presentation_owner="SLD",
        projection_source="test",
        properties={},
    )
    item = factory.create_connection(connection, QPointF(10.0, 20.0), QPointF(40.0, 50.0))
    assert item.presentation_id == "line-orphan"
    assert item.core_connection_id is None
    assert item.object_id is None
