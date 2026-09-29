from types import SimpleNamespace

import pytest

from ui.core.qt import QGraphicsScene
from ui.canvas.sld_canvas_projection import SLDCanvasProjection
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.canvas.semantic_presentation_realization import SemanticPresentationRealization
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.built_in_symbol_catalogue import register_builtin_symbols
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.plugins.canvas_plugin import CanvasPlugin
from ui.plugins.plugin_context import PluginContext
from ui.sld.sld_document import SLDDocument


class FakeApplication:
    def __init__(self, document):
        self.presentation = document


def _composition(application):
    equipment = EquipmentRegistry.create_default()
    symbols = SymbolRegistry()
    register_builtin_symbols(symbols)
    factory = SLDGraphicsItemFactory(equipment, symbols, application)
    realization = SemanticPresentationRealization(equipment, symbols)
    scene = QGraphicsScene()
    projection = SLDCanvasProjection()
    render_system = SLDCanvasRenderSystem(scene, factory, realization)
    return SimpleNamespace(
        scene=scene,
        sld_canvas_projection=projection,
        sld_canvas_render_system=render_system,
    )


def _plugin(application, composition):
    context = PluginContext(
        application=application,
        controller=object(),
        tool_manager=object(),
        sld_document=application.presentation,
        sld_canvas_projection=composition.sld_canvas_projection,
        sld_canvas_render_system=composition.sld_canvas_render_system,
    )
    plugin = CanvasPlugin()
    plugin._composition = composition
    plugin.initialize(context)
    return plugin


def test_canvas_plugin_synchronizes_current_application_document_after_replacement(qapp):
    startup_document = SLDDocument("startup", project_id="project-1")
    restored_document = SLDDocument("restored", project_id="project-1")
    application = FakeApplication(startup_document)
    composition = _composition(application)
    plugin = _plugin(application, composition)

    application.presentation = restored_document
    snapshot = plugin.synchronize_sld()

    assert snapshot.nodes == ()
    assert plugin.sld_canvas_snapshot is snapshot


def test_canvas_plugin_clears_canvas_when_application_project_is_closed(qapp):
    startup_document = SLDDocument("startup", project_id="project-1")
    application = FakeApplication(startup_document)
    composition = _composition(application)
    plugin = _plugin(application, composition)

    application.presentation = None
    snapshot = plugin.synchronize_sld()

    assert snapshot.nodes == ()
    assert snapshot.connections == ()
