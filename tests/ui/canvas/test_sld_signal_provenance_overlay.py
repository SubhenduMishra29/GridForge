from __future__ import annotations

import os

from ui.canvas.semantic_presentation_realization import SemanticPresentationRealization
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory
from ui.core.qt import QApplication, QGraphicsLineItem, QGraphicsScene
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.built_in_symbol_catalogue import register_builtin_symbols
from ui.equipment.symbol.symbol_registry import SymbolRegistry


def _renderer(scene):
    registry = EquipmentRegistry.create_default()
    symbols = SymbolRegistry()
    register_builtin_symbols(symbols)
    application = object()
    realization = SemanticPresentationRealization(registry, symbols)
    factory = SLDGraphicsItemFactory(registry, symbols, application)
    return SLDCanvasRenderSystem(scene, factory, realization)


def test_provenance_overlays_do_not_mutate_authoritative_render_item_registry():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    scene = QGraphicsScene()
    renderer = _renderer(scene)
    route = QGraphicsLineItem(0.0, 0.0, 100.0, 0.0)
    scene.addItem(route)
    renderer._items["physical-segment-1"] = (route,)
    renderer._connection_signal_ids["physical-segment-1"] = ("signal-1",)

    renderer.set_signal_provenance_targets({
        "signal-1": ({
            "label": "PT-101-V | CONTROL PV",
            "detail": "Signal PT-101-V\nCable C-101 / core 2",
            "target_editor": None,
            "target_object_id": None,
        },),
    })
    assert renderer._items["physical-segment-1"] == (route,)
    assert len(renderer._provenance_items["physical-segment-1"]) == 1
    assert len(scene.items()) == 2

    renderer.set_signal_provenance_targets({})
    assert renderer._items["physical-segment-1"] == (route,)
    assert renderer._provenance_items == {}
    assert scene.items() == [route]

    renderer.set_signal_provenance_targets({
        "signal-1": ({
            "label": "PT-101-V | PROTECTION IA",
            "detail": "Signal PT-101-V",
            "target_editor": None,
            "target_object_id": None,
        },),
    })
    renderer._remove_realized("physical-segment-1")
    assert renderer._provenance_items == {}
    assert scene.items() == []
    renderer.dispose()
    del app
