# ============================================================
# File: ui/sld/sld_surface.py
# GridForge V2 — SLD Presentation Surface
# Author: Subhendu Mishra
# ============================================================
"""SLD presentation coordinator attached to the canonical Canvas scene.

Canvas owns the Qt viewport and QGraphicsScene. This class owns only the
SLD presentation/update coordination and never creates a second viewport
or scene. SLD model data is projected into renderer-neutral Canvas input
before the canonical Canvas render system realizes graphics items.
"""

from __future__ import annotations

from typing import Any

from ui.canvas.sld_canvas_projection import SLDCanvasProjection
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from .sld_document import SLDDocument


class SLDSurface:
    """Coordinate SLD presentation on an existing Canvas graphics view."""

    def __init__(
        self,
        graphics_view: Any,
        *,
        projection: SLDCanvasProjection | None = None,
        render_system: SLDCanvasRenderSystem | None = None,
    ) -> None:
        if graphics_view is None:
            raise ValueError("graphics_view must not be None")

        scene = getattr(graphics_view, "graphics_scene", None)
        if scene is None:
            raise TypeError("graphics_view must expose graphics_scene")

        self._graphics_view = graphics_view
        self._projection = projection or SLDCanvasProjection()
        if not isinstance(render_system, SLDCanvasRenderSystem):
            raise TypeError(
                "render_system must be the application-composed SLDCanvasRenderSystem"
            )
        if render_system.scene is not scene:
            raise ValueError("render_system must target the graphics_view scene")
        self._render_system = render_system
        self._document_id: str | None = None

    @property
    def graphics_view(self) -> Any:
        """Return the injected canonical Canvas viewport."""
        return self._graphics_view

    @property
    def projection(self) -> SLDCanvasProjection:
        """Return the SLD-to-Canvas projection boundary."""
        return self._projection

    @property
    def render_system(self) -> SLDCanvasRenderSystem:
        """Return the canonical Canvas SLD render system."""
        return self._render_system

    @property
    def document_id(self) -> str | None:
        """Return the currently presented SLD document identity."""
        return self._document_id

    def present(self, document: SLDDocument) -> None:
        """Project and realize an SLD document on the existing Canvas scene."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")

        self._document_id = document.document_id
        snapshot = self._projection.project(document.model)
        self._render_system.synchronize(snapshot)

    def clear_document(self) -> None:
        """Remove SLD presentation items and detach the logical document."""
        self._render_system.clear()
        self._document_id = None

    def close(self) -> None:
        """Release only transient SLD graphics owned by the canonical renderer."""
        self.clear_document()


__all__ = ["SLDSurface"]
