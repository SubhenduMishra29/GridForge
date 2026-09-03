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

from ui.events import UIUpdate, UIUpdateBus

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
        update_bus: UIUpdateBus | None = None,
    ) -> None:
        if graphics_view is None:
            raise ValueError("graphics_view must not be None")

        scene = getattr(graphics_view, "graphics_scene", None)
        if scene is None:
            raise TypeError("graphics_view must expose graphics_scene")

        self._graphics_view = graphics_view
        self._projection = projection or SLDCanvasProjection()
        self._render_system = render_system or SLDCanvasRenderSystem(scene)
        if self._render_system.scene is not scene:
            raise ValueError("render_system must target the graphics_view scene")
        self._document_id: str | None = None
        self._update_bus: UIUpdateBus | None = None

        if update_bus is not None:
            self.attach_update_bus(update_bus)

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

    def attach_update_bus(self, update_bus: UIUpdateBus) -> None:
        """Subscribe to the presentation update boundary."""
        if not isinstance(update_bus, UIUpdateBus):
            raise TypeError("update_bus must be a UIUpdateBus")

        if self._update_bus is update_bus:
            return

        self.detach_update_bus()
        self._update_bus = update_bus
        update_bus.subscribe("sld_document_changed", self._on_ui_update)
        update_bus.subscribe("sld_projection_invalidated", self._on_ui_update)

    def detach_update_bus(self) -> None:
        """Detach from the presentation update boundary."""
        if self._update_bus is None:
            return

        self._update_bus.unsubscribe("sld_document_changed", self._on_ui_update)
        self._update_bus.unsubscribe("sld_projection_invalidated", self._on_ui_update)
        self._update_bus = None

    def _on_ui_update(self, update: UIUpdate) -> None:
        """Consume an SLD presentation update without mutating Core."""
        payload = update.payload
        if isinstance(payload, SLDDocument):
            self.present(payload)
        elif payload is None:
            self.clear_document()

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
        """Release presentation subscriptions."""
        self.detach_update_bus()


__all__ = ["SLDSurface"]
