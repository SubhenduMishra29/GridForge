from types import SimpleNamespace

from ui.canvas.sld_canvas_projection import SLDCanvasProjection, SLDCanvasSnapshot
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.plugins.canvas_plugin import CanvasPlugin
from ui.plugins.plugin_context import PluginContext
from ui.sld.sld_document import SLDDocument


def test_canvas_plugin_synchronizes_current_application_document_after_replacement(
    monkeypatch,
):
    startup_document = SLDDocument("startup", project_id="project-1")
    restored_document = SLDDocument("restored", project_id="project-1")

    projection = object.__new__(SLDCanvasProjection)
    projected_models = []

    def project(model):
        projected_models.append(model)
        return SLDCanvasSnapshot(nodes=(), connections=())

    projection.project = project

    render_system = object.__new__(SLDCanvasRenderSystem)
    render_system.synchronize = lambda snapshot: None

    application = SimpleNamespace(presentation=startup_document)
    context = PluginContext(
        application=application,
        controller=object(),
        tool_manager=object(),
        sld_document=startup_document,
        sld_canvas_projection=projection,
        sld_canvas_render_system=render_system,
    )

    plugin = CanvasPlugin()
    plugin._composition = object()
    monkeypatch.setattr(CanvasPlugin, "require_scene", lambda self: object())
    plugin.initialize(context)

    application.presentation = restored_document
    plugin.synchronize_sld()

    assert projected_models[-1] is restored_document.model


def test_canvas_plugin_clears_canvas_when_application_project_is_closed(
    monkeypatch,
):
    startup_document = SLDDocument("startup", project_id="project-1")

    projection = object.__new__(SLDCanvasProjection)
    projection.project = lambda model: SLDCanvasSnapshot(nodes=(), connections=())

    clear_calls = []
    render_system = object.__new__(SLDCanvasRenderSystem)
    render_system.synchronize = lambda snapshot: None
    render_system.clear = lambda: clear_calls.append(True)

    application = SimpleNamespace(presentation=startup_document)
    context = PluginContext(
        application=application,
        controller=object(),
        tool_manager=object(),
        sld_document=startup_document,
        sld_canvas_projection=projection,
        sld_canvas_render_system=render_system,
    )

    plugin = CanvasPlugin()
    plugin._composition = object()
    monkeypatch.setattr(CanvasPlugin, "require_scene", lambda self: object())
    plugin.initialize(context)

    application.presentation = None
    snapshot = plugin.synchronize_sld()

    assert clear_calls
    assert snapshot.nodes == ()
    assert snapshot.connections == ()
