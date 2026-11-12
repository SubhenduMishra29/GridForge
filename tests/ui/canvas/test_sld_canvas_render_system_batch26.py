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
from ui.core.qt import QApplication, QGraphicsScene, QGraphicsLineItem
from ui.items.signal_provenance_item import SignalProvenanceItem
import os


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    return app if app is not None else QApplication([])


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
        read_model=ElementReadModel(object_id="breaker-1", element_type="BREAKER", labels={"name": "Breaker 1"}, connectivity_refs=(), attributes={}),
    )

    renderer.synchronize(SLDCanvasSnapshot(nodes=(node,), connections=()))

    assert scene.items == []
    assert renderer.has_render_failures
    assert renderer.render_diagnostics
    diagnostic = renderer.render_diagnostics[0]
    assert diagnostic.node_id == "sld-invalid"
    assert diagnostic.equipment_id == equipment_id
    assert diagnostic.equipment_type == "breaker"
    assert diagnostic.category == "presentation_realization"
    assert diagnostic.code in {"MISSING_EQUIPMENT_ID", "EQUIPMENT_READ_MODEL_NOT_FOUND"}
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



def test_batch26_renderer_removes_deleted_node_and_recreates_same_identity_without_duplicates(qapp) -> None:
    realization, factory, _ = _composition()
    scene = QGraphicsScene()
    renderer = SLDCanvasRenderSystem(scene, factory, realization)
    original_node = SLDCanvasNode(
        node_id="sld-breaker-lifecycle-1",
        equipment_id="breaker-1",
        x=300.0,
        y=410.0,
        properties={"element_type": "BREAKER"},
    )

    renderer.synchronize(SLDCanvasSnapshot(nodes=(original_node,), connections=()))
    original_items = tuple(item for item in scene.items() if isinstance(item, EquipmentItem))
    assert len(original_items) == 1
    original_item = original_items[0]
    assert original_item.object_id == "breaker-1"

    # Core equipment deletion removes the node from the complete SLD snapshot.
    renderer.synchronize(SLDCanvasSnapshot(nodes=(), connections=()))
    assert scene.items() == []
    assert original_item.scene() is None

    # Undo restores the same persistent SLD node identity. The renderer must
    # create exactly one fresh graphics projection, not retain or duplicate the
    # deleted Qt item.
    restored_node = SLDCanvasNode(
        node_id="sld-breaker-lifecycle-1",
        equipment_id="breaker-1",
        x=300.0,
        y=410.0,
        properties={"element_type": "BREAKER"},
    )
    renderer.synchronize(SLDCanvasSnapshot(nodes=(restored_node,), connections=()))

    restored_items = tuple(item for item in scene.items() if isinstance(item, EquipmentItem))
    assert len(restored_items) == 1
    assert restored_items[0] is not original_item
    assert restored_items[0].object_id == "breaker-1"
    assert restored_items[0].scene() is scene
    renderer.dispose()
    assert scene.items() == []



class _RecordingSnapSystem:
    def __init__(self, scene):
        self._scene = scene
        self.registered = []

    def get_scene(self):
        return self._scene

    def register_item(self, item):
        self.registered.append(item)

    def unregister_item(self, item):
        if item in self.registered:
            self.registered.remove(item)


def test_batch26_hidden_layer_keeps_snap_registration_and_applies_opacity_and_order(qapp) -> None:
    realization, factory, _ = _composition()
    scene = QGraphicsScene()
    snap_system = _RecordingSnapSystem(scene)
    renderer = SLDCanvasRenderSystem(scene, factory, realization, snap_system=snap_system)
    node = SLDCanvasNode(
        node_id="sld-hidden-layer-breaker",
        equipment_id="breaker-1",
        x=120.0,
        y=160.0,
        properties={"element_type": "BREAKER"},
        layer_id="physical",
        layer_visible=False,
        layer_opacity=0.35,
        layer_order=2,
    )

    renderer.synchronize(SLDCanvasSnapshot(nodes=(node,), connections=()))

    items = tuple(item for item in scene.items() if isinstance(item, EquipmentItem))
    assert len(items) == 1
    item = items[0]
    assert not item.isVisible()
    assert item.opacity() == pytest.approx(0.35)
    assert item.zValue() == pytest.approx(220.0)
    # Visibility is a paint/hit-test policy. Canonical snap anchors remain registered.
    assert snap_system.registered == [item]
    assert item.snap_points()
    renderer.dispose()
    assert snap_system.registered == []


def test_batch26_layer_metadata_change_invalidates_node_render_signature(qapp) -> None:
    realization, factory, _ = _composition()
    scene = QGraphicsScene()
    renderer = SLDCanvasRenderSystem(scene, factory, realization)
    hidden = SLDCanvasNode(
        node_id="sld-layer-signature-breaker",
        equipment_id="breaker-1",
        x=120.0,
        y=160.0,
        properties={"element_type": "BREAKER"},
        layer_id="protection",
        layer_visible=False,
        layer_opacity=0.5,
        layer_order=1,
    )
    renderer.synchronize(SLDCanvasSnapshot(nodes=(hidden,), connections=()))
    first = next(item for item in scene.items() if isinstance(item, EquipmentItem))

    visible = SLDCanvasNode(
        node_id="sld-layer-signature-breaker",
        equipment_id="breaker-1",
        x=120.0,
        y=160.0,
        properties={"element_type": "BREAKER"},
        layer_id="protection",
        layer_visible=True,
        layer_opacity=0.8,
        layer_order=3,
    )
    renderer.synchronize(SLDCanvasSnapshot(nodes=(visible,), connections=()))
    current = next(item for item in scene.items() if isinstance(item, EquipmentItem))
    assert current is not first
    assert current.isVisible()
    assert current.opacity() == pytest.approx(0.8)
    assert current.zValue() == pytest.approx(320.0)
    renderer.dispose()


def test_annotation_layout_prioritizes_identity_and_hides_colliding_secondary_labels(qapp):
    from ui.canvas.sld_canvas_projection import SLDCanvasAnnotation

    realization, factory, _ = _composition()
    scene = QGraphicsScene()
    renderer = SLDCanvasRenderSystem(scene, factory, realization)
    annotations = (
        SLDCanvasAnnotation(
            block_id="identity", node_id="node-1", x=100.0, y=100.0,
            text="ID: CB-1", visible=True, priority=0,
        ),
        SLDCanvasAnnotation(
            block_id="parameter", node_id="node-1", x=100.0, y=100.0,
            text="Parameter: 11 kV", visible=True, priority=40,
        ),
        SLDCanvasAnnotation(
            block_id="other-identity", node_id="node-2", x=500.0, y=100.0,
            text="ID: BUS-1", visible=True, priority=0,
        ),
    )

    renderer.synchronize(SLDCanvasSnapshot(nodes=(), connections=(), annotations=annotations))

    identity = renderer._items["annotation:identity"][0]
    parameter = renderer._items["annotation:parameter"][0]
    other_identity = renderer._items["annotation:other-identity"][0]
    assert identity.isVisible()
    assert other_identity.isVisible()
    assert not parameter.isVisible()
    assert parameter.scale() == pytest.approx(1.0)

    # Decluttering is viewport-only and reversible when zoom crosses the
    # existing annotation visibility threshold.
    renderer.set_zoom_level(0.5)
    assert not identity.isVisible()
    renderer.set_zoom_level(1.0)
    assert identity.isVisible()
    assert other_identity.isVisible()
    assert not parameter.isVisible()
    renderer.dispose()


def test_annotation_layout_shrinks_labels_before_hiding_them(qapp):
    from ui.canvas.sld_canvas_projection import SLDCanvasAnnotation

    realization, factory, _ = _composition()
    scene = QGraphicsScene()
    renderer = SLDCanvasRenderSystem(scene, factory, realization)
    annotations = (
        SLDCanvasAnnotation(
            block_id="primary", node_id="node-1", x=100.0, y=100.0,
            text="Primary equipment identity", visible=True, priority=0,
        ),
        SLDCanvasAnnotation(
            block_id="secondary", node_id="node-2", x=100.0, y=70.0,
            text="Secondary\nlabel", visible=True, priority=20,
        ),
    )

    renderer.synchronize(SLDCanvasSnapshot(nodes=(), connections=(), annotations=annotations))

    primary = renderer._items["annotation:primary"][0]
    secondary = renderer._items["annotation:secondary"][0]
    assert primary.isVisible()
    assert secondary.isVisible()
    assert secondary.scale() < 1.0
    assert secondary.scale() >= 0.6
    assert not primary.sceneBoundingRect().intersects(secondary.sceneBoundingRect())

    renderer.dispose()


def test_annotation_projection_priority_prefers_identity_then_type_then_secondary_fields():
    from ui.canvas.sld_canvas_projection import SLDCanvasProjection

    assert SLDCanvasProjection._annotation_priority(("parameter:voltage", "identity")) == 0
    assert SLDCanvasProjection._annotation_priority(("attribute:rating", "type")) == 10
    assert SLDCanvasProjection._annotation_priority(("parameter:voltage",)) == 20
    assert SLDCanvasProjection._annotation_priority(("label:name",)) == 30
    assert SLDCanvasProjection._annotation_priority(("attribute:rating",)) == 40



def test_sld_physical_route_provenance_label_navigates_to_exact_peer_and_tracks_visibility(qapp):
    realization, factory, _ = _composition()
    scene = QGraphicsScene()
    renderer = SLDCanvasRenderSystem(scene, factory, realization)
    route = QGraphicsLineItem(0.0, 0.0, 120.0, 0.0)
    route.setOpacity(0.4)
    route.setVisible(False)
    scene.addItem(route)
    renderer._items["physical-route"] = (route,)
    renderer._connection_signal_ids["physical-route"] = ("signal-1",)
    renderer._connection_label_signal_ids["physical-route"] = ("signal-1",)
    navigations = []
    renderer.set_provenance_navigation_callback(
        lambda editor, object_id: navigations.append((editor, object_id))
    )
    renderer.set_signal_provenance_targets({
        "signal-1": ({
            "label": "IA_A | PROTECTION IA",
            "detail": "Cable IC-001/1; sink IED-101/IA",
            "target_editor": "protection",
            "target_object_id": "element-1",
        },),
    })

    labels = renderer._provenance_items["physical-route"]
    assert len(labels) == 1
    label = labels[0]
    assert isinstance(label, SignalProvenanceItem)
    assert not label.isVisible()
    assert label.opacity() == pytest.approx(0.4)
    accepted = []
    label.mouseDoubleClickEvent(SimpleNamespace(accept=lambda: accepted.append(True)))
    assert navigations == [("protection", "element-1")]
    assert accepted == [True]

    route.setVisible(True)
    renderer.set_signal_provenance_targets({
        "signal-1": ({
            "label": "IA_A | CONTROL PV",
            "detail": "Cable IC-001/1; sink PLC-101/AI1",
            "target_editor": "control",
            "target_object_id": "component-1",
        },),
    })
    current_label = renderer._provenance_items["physical-route"][0]
    assert current_label.isVisible()
    assert current_label.opacity() == pytest.approx(0.4)
    renderer.dispose()
    assert scene.items() == []



def test_sld_signal_selection_highlights_all_carrier_segments(qapp):
    realization, factory, _ = _composition()
    scene = QGraphicsScene()
    renderer = SLDCanvasRenderSystem(scene, factory, realization)
    first = QGraphicsLineItem(0.0, 0.0, 50.0, 0.0)
    second = QGraphicsLineItem(50.0, 0.0, 100.0, 0.0)
    first.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)
    second.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)
    scene.addItem(first)
    scene.addItem(second)
    renderer._items["carrier-hop-1"] = (first,)
    renderer._items["carrier-hop-2"] = (second,)
    renderer._connection_signal_ids = {
        "carrier-hop-1": ("signal-1",),
        "carrier-hop-2": ("signal-1",),
    }

    bounds = renderer.select_signal_routes("signal-1")

    assert first.isSelected()
    assert second.isSelected()
    assert bounds.left() <= first.sceneBoundingRect().left()
    assert bounds.right() >= second.sceneBoundingRect().right()
    renderer.dispose()
