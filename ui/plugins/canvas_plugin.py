"""
GridForge V2
============

File:
    ui/plugins/canvas_plugin.py

Purpose
-------
Canvas composition plugin for the GridForge SLD UI.

Architectural role
------------------
CanvasPlugin owns the lifecycle of the authoritative GraphicsView.
It receives the SLD-to-Canvas projection boundary from composition but does
not own electrical truth or construct a second model.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QGraphicsScene, QWidget

from ui.canvas.graphics_view import GraphicsView
from ui.canvas.sld_canvas_projection import SLDCanvasProjection, SLDCanvasSnapshot
from ui.plugins.plugin_context import PluginContext


class CanvasPlugin:
    """GridForge canvas composition plugin."""

    plugin_id = "canvas"

    def __init__(self, context: Optional[PluginContext] = None) -> None:
        self._context = context
        self._view: Optional[GraphicsView] = None
        self._initialized = False
        self._sld_canvas_snapshot: Optional[SLDCanvasSnapshot] = None

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

    def initialize(self, context: Optional[PluginContext] = None) -> bool:
        """Initialize the canvas plugin."""
        if self._initialized:
            return True
        if context is not None:
            self.set_context(context)
        if self._context is None:
            raise RuntimeError("CanvasPlugin requires a PluginContext.")
        self._validate_context()
        self._create_canvas()
        self.synchronize_sld()
        self._initialized = True
        return True

    def _validate_context(self) -> None:
        """Validate dependencies required by the canvas."""
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

    def _create_canvas(self) -> None:
        """Create the authoritative GridForge GraphicsView."""
        if self._context is None:
            raise RuntimeError("CanvasPlugin context is unavailable.")
        if self._view is not None:
            raise RuntimeError("CanvasPlugin already contains a GraphicsView.")

        self._view = GraphicsView(
            controller=self._context.controller,
            tool_manager=self._context.tool_manager,
            parent=self._context.parent,
        )

        if not isinstance(self._view, GraphicsView):
            raise TypeError("GraphicsView construction returned an invalid object.")

    def synchronize_sld(self) -> SLDCanvasSnapshot:
        """Refresh renderer-neutral Canvas input from the active SLD document."""
        if self._context is None:
            raise RuntimeError("CanvasPlugin context is unavailable.")
        document = self._context.sld_document
        projection = self._context.sld_canvas_projection
        if document is None or projection is None:
            raise RuntimeError("SLD canvas projection dependencies are unavailable.")
        if not isinstance(projection, SLDCanvasProjection):
            raise TypeError("sld_canvas_projection must be an SLDCanvasProjection.")
        self._sld_canvas_snapshot = projection.project(document.model)
        return self._sld_canvas_snapshot

    @property
    def sld_canvas_snapshot(self) -> Optional[SLDCanvasSnapshot]:
        """Return the latest renderer-neutral SLD Canvas projection."""
        return self._sld_canvas_snapshot

    @property
    def widget(self) -> Optional[QWidget]:
        """Return the canvas QWidget."""
        return self._view

    def require_view(self) -> GraphicsView:
        """Return the initialized GraphicsView."""
        if self._view is None:
            raise RuntimeError("CanvasPlugin has not been initialized.")
        return self._view

    def require_scene(self) -> QGraphicsScene:
        """Return the scene owned by GraphicsView."""
        scene = self.require_view().scene()
        if scene is None:
            raise RuntimeError("GraphicsView does not currently have a scene.")
        return scene

    @property
    def initialized(self) -> bool:
        """Return whether the canvas plugin is initialized."""
        return self._initialized

    def shutdown(self) -> None:
        """Shut down the canvas plugin."""
        if self._view is not None:
            self._view.setParent(None)
            self._view.deleteLater()
        self._view = None
        self._sld_canvas_snapshot = None
        self._initialized = False


def create_canvas_plugin(context: Optional[PluginContext] = None) -> CanvasPlugin:
    """Create a CanvasPlugin without constructing Qt until initialization."""
    return CanvasPlugin(context=context)


__all__ = ["CanvasPlugin", "create_canvas_plugin"]
