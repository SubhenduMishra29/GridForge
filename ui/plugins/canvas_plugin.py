"""
GridForge V2
============

File:
    ui/plugins/canvas_plugin.py

Purpose
-------
Canvas plugin lifecycle boundary for an application-composed SLD canvas.

Architectural role
------------------
CanvasPlugin consumes an application-owned CanvasComposition and injected SLD
presentation services. It does not construct Canvas services, own the Canvas
scene, or dispose shared Canvas services. SLD projection and graphics
realization remain presentation-only.
"""

from __future__ import annotations

from typing import Optional

from ui.core.qt import QGraphicsScene, QWidget

from ui.canvas.canvas_composition import CanvasComposition
from ui.canvas.graphics_view import GraphicsView
from ui.canvas.sld_canvas_projection import SLDCanvasProjection, SLDCanvasSnapshot
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.plugins.plugin_context import PluginContext
from ui.sld.sld_document import SLDDocument


class CanvasPlugin:
    """GridForge canvas plugin consuming an application-owned composition."""

    plugin_id = "canvas"

    def __init__(self) -> None:
        """Construct the plugin without runtime dependencies.

        Dependencies are supplied only through ``initialize(context)`` as
        required by the PluginLoader contract.
        """
        self._context: Optional[PluginContext] = None
        self._composition: Optional[CanvasComposition] = None
        self._initialized = False
        self._sld_canvas_snapshot: Optional[SLDCanvasSnapshot] = None
        self._sld_canvas_render_system: Optional[SLDCanvasRenderSystem] = None

    @property
    def context(self) -> Optional[PluginContext]:
        return self._context

    def set_context(self, context: PluginContext) -> None:
        if not isinstance(context, PluginContext):
            raise TypeError("context must be PluginContext.")
        if self._initialized:
            raise RuntimeError("CanvasPlugin context cannot be changed after initialization.")
        self._context = context

    @property
    def composition(self) -> Optional[CanvasComposition]:
        return self._composition

    def set_composition(self, composition: CanvasComposition) -> None:
        if not isinstance(composition, CanvasComposition):
            raise TypeError("composition must be CanvasComposition.")
        if self._initialized:
            raise RuntimeError("CanvasPlugin composition cannot be changed after initialization.")
        if self._composition is not None and self._composition is not composition:
            raise RuntimeError("CanvasPlugin already has a CanvasComposition.")
        self._composition = composition

    def initialize(self, context: Optional[PluginContext] = None) -> bool:
        if self._initialized:
            return True
        if context is not None:
            self.set_context(context)
        self._validate_context()
        if self._composition is None:
            raise RuntimeError("CanvasPlugin requires an application-composed CanvasComposition.")

        self._sld_canvas_render_system = self._context.sld_canvas_render_system
        if not isinstance(self._sld_canvas_render_system, SLDCanvasRenderSystem):
            raise TypeError("sld_canvas_render_system must be an SLDCanvasRenderSystem.")
        if self._sld_canvas_render_system.scene is not self.require_scene():
            raise RuntimeError("SLD canvas render system must target the CanvasComposition scene.")

        self.synchronize_sld()
        self._initialized = True
        return True

    def _validate_context(self) -> None:
        if self._context is None:
            raise RuntimeError("CanvasPlugin context is unavailable.")
        self._context.validate(required=(
            "controller",
            "application",
            "tool_manager",
            "sld_document",
            "sld_canvas_projection",
            "sld_canvas_render_system",
        ))

    def _active_sld_document(self) -> SLDDocument:
        application = self._context.application
        document = getattr(application, "presentation", None)
        if isinstance(document, SLDDocument):
            return document
        document = self._context.sld_document
        if isinstance(document, SLDDocument):
            return document
        raise RuntimeError("CanvasPlugin has no active SLD document.")

    def synchronize_sld(self) -> SLDCanvasSnapshot:
        if self._context is None:
            raise RuntimeError("CanvasPlugin context is unavailable.")
        projection = self._context.sld_canvas_projection
        render_system = self._context.sld_canvas_render_system
        if projection is None or render_system is None:
            raise RuntimeError("SLD canvas projection dependencies are unavailable.")
        if getattr(self._context.application, "presentation", None) is None:
            render_system.clear()
            snapshot = SLDCanvasSnapshot(nodes=(), connections=())
            self._sld_canvas_snapshot = snapshot
            return snapshot
        document = self._active_sld_document()
        if not isinstance(projection, SLDCanvasProjection):
            raise TypeError("sld_canvas_projection must be an SLDCanvasProjection.")
        if not isinstance(render_system, SLDCanvasRenderSystem):
            raise TypeError("sld_canvas_render_system must be an SLDCanvasRenderSystem.")
        if render_system is not self._sld_canvas_render_system:
            raise RuntimeError("SLD canvas render system changed after plugin initialization.")

        snapshot = projection.project(document.model)
        self._sld_canvas_snapshot = snapshot
        render_system.synchronize(snapshot)
        return snapshot

    @property
    def sld_canvas_snapshot(self) -> Optional[SLDCanvasSnapshot]:
        return self._sld_canvas_snapshot

    @property
    def sld_canvas_render_system(self) -> Optional[SLDCanvasRenderSystem]:
        return self._sld_canvas_render_system

    @property
    def widget(self) -> Optional[QWidget]:
        return self._composition.widget if self._composition is not None else None

    def require_view(self) -> GraphicsView:
        if self._composition is None:
            raise RuntimeError("CanvasPlugin has no CanvasComposition.")
        if not isinstance(self._composition.view, GraphicsView):
            raise TypeError("CanvasComposition view must be a GraphicsView.")
        return self._composition.view

    def require_scene(self) -> QGraphicsScene:
        scene = self._composition.scene if self._composition is not None else None
        if scene is None:
            raise RuntimeError("CanvasPlugin has no CanvasComposition scene.")
        return scene

    @property
    def initialized(self) -> bool:
        return self._initialized

    def shutdown(self) -> None:
        self._sld_canvas_render_system = None
        self._sld_canvas_snapshot = None
        self._initialized = False


def create_canvas_plugin() -> CanvasPlugin:
    """Construct a context-free CanvasPlugin."""
    return CanvasPlugin()


__all__ = ["CanvasPlugin", "create_canvas_plugin"]
