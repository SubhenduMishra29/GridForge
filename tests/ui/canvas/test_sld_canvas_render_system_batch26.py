from __future__ import annotations

from types import SimpleNamespace

import pytest

from core.application.read_models import ElementReadModel
from ui.canvas.semantic_presentation_realization import SemanticPresentationRealization
from ui.canvas.sld_canvas_projection import SLDCanvasNode, SLDCanvasSnapshot
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.built_in_symbol_catalogue import register_builtin_symbols
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.items.bus_item import BusItem
from ui.items.equipment_item import EquipmentItem


NETWORK_TYPES = (
    "BUS",
    "TRANSFORMER",
    "BREAKER",
    "SWITCH",
    "DISCONNECTOR",
    "FUSE",
    "LINE",
    "CABLE",
    "GENERATOR",
    "SYNCHRONOUS_MACHINE",
    "LOAD",
    "MOTOR",
    "SHUNT",
    "CAPACITOR",
    "REACTOR",
    "SOLAR",
    "BATTERY",
    "GRID",
    "CT",
    "PT",
    "CVT",
)

RELAY_TYPE = "RELAY"


class FakeApplication:
    def __init__(self, element_types: tuple[str, ...]) -> None:
        self._elements = tuple(
            ElementReadModel(
                object_id=f"{element_type.lower()}-1",
                element_type=element_type,
                labels={"name": element_type},
                connectivity_refs=(),
                attributes={},
            )
            for element_type in element_types
        )

    def read_network(self):
        return SimpleNamespace(elements=self._elements)

    def read_protection(self):
        return SimpleNamespace(relays=(
            SimpleNamespace(object_id="relay-1", name="Relay 1"),
        ))


class RecordingScene:
    def __init__(self) -> None:
        self.items: list[object] = []

    def addItem(self, item: object) -> None:
        self.items.append(item)


def _composition():
    equipment_registry = EquipmentRegistry.create_default()
    symbol_registry = SymbolRegistry()
    register_builtin_symbols(symbol_registry)
    application = FakeApplication(NETWORK_TYPES)
    realization = SemanticPresentationRealization(equipment_registry, symbol_registry)
    factory = SLDGraphicsItemFactory(equipment_registry, symbol_registry, application)
    return realization, factory, application


@pytest.mark.parametrize("element_type", NETWORK_TYPES)
def test_batch26_factory_realizes_every_builtin_network_equipment_type(element_type: str) -> None:
    realization, factory, _ = _composition()
    equipment_id = f"{element_type.lower()}-1"
    node = SLDCanvasNode(
        node_id=f"sld-{equipment_id}",
        equipment_id=equipment_id,
        x=125.0,
        y=240.0,
        properties={"element_type": element_type},
    )

    selection = realization.realize(node)
    item = factory.create_node(node, selection)

    if element_type == "BUS":
        assert isinstance(item, BusItem)
    else:
        assert isinstance(item, EquipmentItem)
    assert item.object_id == equipment_id
    assert item.get_scene_position() == (125.0, 240.0)


def test_batch26_factory_realizes_relay_from_protection_read_model() -> None:
    realization, factory, _ = _composition()
    node = SLDCanvasNode(
        node_id="sld-relay-1",
        equipment_id="relay-1",
        x=75.0,
        y=95.0,
        properties={"element_type": RELAY_TYPE},
    )

    selection = realization.realize(node)
    item = factory.create_node(node, selection)

    assert isinstance(item, EquipmentItem)
    assert item.object_id == "relay-1"
    assert item.element_type == "RELAY"


def test_batch26_renderer_realizes_non_bus_equipment_when_read_model_identity_matches() -> None:
    realization, factory, _ = _composition()
    scene = RecordingScene()
    renderer = SLDCanvasRenderSystem(scene, factory, realization)
    node = SLDCanvasNode(
        node_id="sld-breaker-1",
        equipment_id="breaker-1",
        x=300.0,
        y=410.0,
        properties={"element_type": "BREAKER"},
    )

    renderer.synchronize(SLDCanvasSnapshot(nodes=(node,), connections=()))

    assert len(scene.items) == 1
    assert isinstance(scene.items[0], EquipmentItem)
    assert scene.items[0].object_id == "breaker-1"
    assert renderer.render_diagnostics == ()


@pytest.mark.parametrize("equipment_id", [None, "does-not-exist"])
def test_batch26_renderer_reports_missing_or_invalid_identity_without_fabrication(equipment_id: str | None) -> None:
    realization, factory, _ = _composition()
    scene = RecordingScene()
    renderer = SLDCanvasRenderSystem(scene, factory, realization)
    node = SLDCanvasNode(
        node_id="sld-invalid",
        equipment_id=equipment_id,
        x=20.0,
        y=30.0,
        properties={"element_type": "BREAKER"},
    )

    renderer.synchronize(SLDCanvasSnapshot(nodes=(node,), connections=()))

    assert scene.items == []
    assert renderer.has_render_failures
    assert renderer.render_diagnostics
    diagnostic = renderer.render_diagnostics[0]
    assert diagnostic.node_id == "sld-invalid"
    assert diagnostic.equipment_id == equipment_id
    assert diagnostic.equipment_type == "BREAKER"
    assert diagnostic.category == "presentation_realization"
    assert diagnostic.message


def test_batch26_renderer_preserves_committed_position() -> None:
    realization, factory, _ = _composition()
    scene = RecordingScene()
    renderer = SLDCanvasRenderSystem(scene, factory, realization)
    node = SLDCanvasNode(
        node_id="sld-transformer-1",
        equipment_id="transformer-1",
        x=512.5,
        y=618.25,
        properties={"element_type": "TRANSFORMER"},
    )

    renderer.synchronize(SLDCanvasSnapshot(nodes=(node,), connections=()))

    item = scene.items[0]
    assert isinstance(item, EquipmentItem)
    assert item.get_scene_position() == (512.5, 618.25)
