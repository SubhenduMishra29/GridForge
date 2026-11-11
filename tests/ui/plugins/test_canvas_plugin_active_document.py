from types import SimpleNamespace

import pytest

from ui.core.qt import QGraphicsScene
from ui.canvas.sld_canvas_projection import SLDCanvasProjection, CompositeSLDCanvasSnapshot
from ui.canvas.draft_sld_projection import DraftSLDCanvasSnapshot
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.canvas.semantic_presentation_realization import SemanticPresentationRealization
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.built_in_symbol_catalogue import register_builtin_symbols
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.plugins.canvas_plugin import CanvasPlugin
from ui.plugins.plugin_context import PluginContext
from ui.sld.sld_document import SLDDocument
from ui.sld.instrumentation_wiring_projection import SLDInstrumentationWiringProjection


class FakeApplication:
    def __init__(self, document):
        self.presentation = document

    def read_network(self):
        return SimpleNamespace(elements=())

    def read_protection(self):
        return SimpleNamespace(relays=())


def _composition(application):
    equipment = EquipmentRegistry.create_default()
    symbols = SymbolRegistry()
    register_builtin_symbols(symbols)
    factory = SLDGraphicsItemFactory(equipment, symbols, application)
    realization = SemanticPresentationRealization(equipment, symbols)
    scene = QGraphicsScene()
    projection = SLDCanvasProjection()
    render_system = SLDCanvasRenderSystem(scene, factory, realization)
    class _Surface:
        last_wiring_projection = None

        def present_composite_document(self, document, draft_snapshot, *, instrumentation_wiring=None):
            self.last_wiring_projection = instrumentation_wiring
            committed = projection.project(
                document.model, document.annotation_blocks,
                instrumentation_wiring=instrumentation_wiring,
            )
            snapshot = CompositeSLDCanvasSnapshot(committed=committed, draft=draft_snapshot)
            render_system.synchronize(snapshot)
            return snapshot

        def clear_document(self):
            render_system.clear()

    return SimpleNamespace(
        scene=scene,
        surface=_Surface(),
        draft_sld_projection=SimpleNamespace(project=lambda: DraftSLDCanvasSnapshot(nodes=(), connections=())),
        sld_canvas_projection=projection,
        sld_canvas_render_system=render_system,
        sld_controller=SimpleNamespace(
            read_instrumentation_wiring_projection=lambda: SLDInstrumentationWiringProjection(
                project_id="project-1", activation_generation=4, records=(),
            ),
        ),
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

    assert snapshot.committed.nodes == ()
    assert plugin.sld_canvas_snapshot is snapshot


def test_canvas_plugin_clears_canvas_when_application_project_is_closed(qapp):
    startup_document = SLDDocument("startup", project_id="project-1")
    application = FakeApplication(startup_document)
    composition = _composition(application)
    plugin = _plugin(application, composition)

    application.presentation = None
    snapshot = plugin.synchronize_sld()

    assert snapshot.committed.nodes == ()
    assert snapshot.committed.connections == ()

def test_canvas_plugin_forwards_active_document_wiring_projection_to_surface(qapp):
    document = SLDDocument("active", project_id="project-1")
    application = FakeApplication(document)
    composition = _composition(application)
    plugin = _plugin(application, composition)

    snapshot = plugin.synchronize_sld()

    forwarded = composition.surface.last_wiring_projection
    assert isinstance(forwarded, SLDInstrumentationWiringProjection)
    assert forwarded.project_id == "project-1"
    assert snapshot.committed.physical_wiring_diagnostics == ()
