from types import SimpleNamespace

from ui.plugins.canvas_plugin import CanvasPlugin
from ui.plugins.plugin_context import PluginContext
from ui.sld.sld_document import SLDDocument


class _Projection:
    def __init__(self):
        self.models = []

    def project(self, model):
        self.models.append(model)
        return SimpleNamespace(nodes=(), connections=())


class _RenderSystem:
    def synchronize(self, snapshot):
        self.snapshot = snapshot


def test_canvas_plugin_synchronizes_current_application_document_after_replacement():
    startup_document = SLDDocument("startup", project_id="project-1")
    restored_document = SLDDocument("restored", project_id="project-1")
    projection = _Projection()
    render_system = _RenderSystem()
    application = SimpleNamespace(presentation=startup_document)
    context = PluginContext(
        application=application,
        sld_document=startup_document,
        sld_canvas_projection=projection,
        sld_canvas_render_system=render_system,
    )
    plugin = CanvasPlugin()
    plugin.initialize(context)

    application.presentation = restored_document
    plugin.synchronize_sld()

    assert projection.models[-1] is restored_document.model
