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
CanvasPlugin consumes an application-owned CanvasComposition. It does not
construct Canvas services, own the Canvas scene, or dispose shared Canvas
services. SLD projection and graphics realization remain presentation-only.

Author
------
Subhendu Mishra
"""

from __future__ import annotations

from typing import Optional

from ui.core.qt import QGraphicsScene, QWidget

from ui.canvas.canvas_composition import CanvasComposition
from ui.canvas.graphics_view import GraphicsView
from ui.canvas.sld_canvas_projection import SLDCanvasProjection, SLDCanvasSnapshot
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.plugins.plugin_context import PluginContext


class CanvasPlugin:
    """GridForge canvas plugin consuming an application-owned composition."""

    plugin_id = "canvas"

    def __init__(self, context: Optional[PluginContext] = None) -> None:
        self._context = context
        self._composition: Optional[CanvasComposition] = None
        self._initialized = False
        self._sld_canvas_snapshot: Optional[SLDCanvasSnapshot] = None
        self._sld_canvas_render_system: Optional[SLDCanvasRenderSystem] = None

    @property
    def context(self) -> Optional[PluginContext]:
        """Return the current plugin context."""
        return self._context

    def set_context(self, context: PluginContext) -> None:
        """Supply plugin dependencies before initialization."""
        if not isinstance(context, PluginContext):
            raise TypeError("context must be PluginContext.")
        if self._initialized:
            raise RuntimeError("CanvasPlugin context cannot be changed after initialization.")
        self._context = context

    @property
    def composition(self) -> Optional[CanvasComposition]:
        """Return the application-owned Canvas composition."""
        return self._composition

    def set_composition(self, composition: CanvasComposition) -> None:
        """Attach an application-owned Canvas composition before initialization."""
        if not isinstance(composition, CanvasComposition):
            raise TypeError("composition must be CanvasComposition.")
        if self._initialized:
            raise RuntimeError("CanvasPlugin composition cannot be changed after initialization.")
        if self._composition is not None and self._composition is not composition:
            raise RuntimeError("CanvasPlugin already has a CanvasComposition.")
        self._composition = composition

    def initialize(self, context: Optional[PluginContext] = None) -> bool:
        """Initialize the plugin against a pre-composed Canvas."""
        if self._initialized:
            return True
        if context is not None:
            self.set_context(context)
        self._validate_context()
        if self._composition is None:
            raise RuntimeError("CanvasPlugin requires an application-composed CanvasComposition.")

        self._sld_canvas_render_system = SLDCanvasRenderSystem(self.require_scene())
        self.synchronize_sld()
        self._initialized = True
        return True

    def _validate_context(self) -> None:
        """Validate dependencies required by SLD projection."""
        if self._context is None:
            raise RuntimeError("CanvasPlugin context is unavailable.")
        if self._context.controller is None:
            raise RuntimeError("CanvasPlugin requires a controller.")
        if self._context.tool_manager is None:
            raise RuntimeError("CanvasPlugin requires a ToolManager.")
        if self._context.sld_document is None:
            raise RuntimeError("CanvasPlugin requires an active SLD document.")
        if self._context.sld_canvas_projection is None:
            raise RuntimeError("CanvasPlugin requires an SLD canvas projection.")

    def synchronize_sld(self) -> SLDCanvasSnapshot:
        """Project and realize the active SLD document in the composed Canvas."""
        if self._context is None:
            raise RuntimeError("CanvasPlugin context is unavailable.")
        document = self._context.sld_document
        projection = self._context.sld_canvas_projection
        if document is None or projection is None:
            raise RuntimeError("SLD canvas projection dependencies are unavailable.")
        if not isinstance(projection, SLDCanvasProjection):
            raise TypeError("sld_canvas_projection must be an SLDCanvasProjection.")
        if self._sld_canvas_render_system is None:
            raise RuntimeError("SLD canvas render system is not initialized.")

        snapshot = projection.project(document.model)
        self._sld_canvas_snapshot = snapshot
        self._sld_canvas_render_system.synchronize(snapshot)
        return snapshot

    @property
    def sld_canvas_snapshot(self) -> Optional[SLDCanvasSnapshot]:
        """Return the latest renderer-neutral SLD Canvas projection."""
        return self._sld_canvas_snapshot

    @property
    def sld_canvas_render_system(self) -> Optional[SLDCanvasRenderSystem]:
        """Return the presentation-only SLD graphics realization."""
        return self._sld_canvas_render_system

    @property
    def widget(self) -> Optional[QWidget]:
        """Return the composed canvas QWidget."""
        return self._composition.widget if self._composition is not None else None

    def require_view(self) -> GraphicsView:
        """Return the GraphicsView supplied by the Canvas composition."""
        if self._composition is None:
            raise RuntimeError("CanvasPlugin has no CanvasComposition.")
        if not isinstance(self._composition.view, GraphicsView):
            raise TypeError("CanvasComposition view must be a GraphicsView.")
        return self._composition.view

    def require_scene(self) -> QGraphicsScene:
        """Return the scene supplied by the Canvas composition."""
        scene = self._composition.scene if self._composition is not None else None
        if scene is None:
            raise RuntimeError("CanvasPlugin has no CanvasComposition scene.")
        return scene

    @property
    def initialized(self) -> bool:
        """Return whether the canvas plugin is initialized."""
        return self._initialized

    def shutdown(self) -> None:
        """Release plugin-owned transient SLD realization only."""
        if self._sld_canvas_render_system is not None:
            self._sld_canvas_render_system.dispose()
        self._sld_canvas_render_system = None
        self._sld_canvas_snapshot = None
        self._initialized = False
        # CanvasComposition and its services remain application-owned.


def create_canvas_plugin(context: Optional[PluginContext] = None) -> CanvasPlugin:
    """Create a CanvasPlugin without constructing Canvas services."""
    return CanvasPlugin(context=context)


__all__ = ["CanvasPlugin", "create_canvas_plugin"]
