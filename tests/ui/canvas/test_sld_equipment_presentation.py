from __future__ import annotations

from types import SimpleNamespace

from core.application.read_models import ElementReadModel
from ui.canvas.semantic_presentation_realization import SemanticPresentationRealization
from ui.canvas.sld_canvas_projection import SLDCanvasNode
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.built_in_symbol_catalogue import register_builtin_symbols
from ui.equipment.symbol.symbol_registry import SymbolRegistry


class FakeApplication:
    def read_network(self):
        return SimpleNamespace(elements=(
            ElementReadModel("breaker-1", "BREAKER", {"name": "Breaker"}, (), {}),
        ))

    def read_protection(self):
        return SimpleNamespace(relays=())


def _composition():
    equipment = EquipmentRegistry.create_default()
    symbols = SymbolRegistry()
    register_builtin_symbols(symbols)
    return (
        SemanticPresentationRealization(equipment, symbols),
        SLDGraphicsItemFactory(equipment, symbols, FakeApplication()),
    )


def _node(node_id: str, element_type: str) -> SLDCanvasNode:
    return SLDCanvasNode(node_id=node_id, equipment_id=node_id, x=10.0, y=20.0, properties={"element_type": element_type})


def test_non_bus_semantic_equipment_has_a_presentation_representation():
    realization, _ = _composition()
    selection = realization.realize(_node("tx-1", "transformer"))
    assert selection.representation_id == "symbol"
    assert selection.symbol_id == "transformer"
    assert selection.symbol_instance is not None


def test_equipment_factory_creates_presentation_only_item():
    _, factory = _composition()
    node = _node("breaker-1", "breaker")
    selection = _composition()[0].realize(node)
    item = factory.create_node(node, selection)
    assert item.object_id == "breaker-1"
    assert item.element_type == "BREAKER"
