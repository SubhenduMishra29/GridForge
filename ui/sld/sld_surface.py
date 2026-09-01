# ============================================================
# File: ui/sld/sld_surface.py
# GridForge V2 — SLD Presentation Surface
# Author: Subhendu Mishra
# ============================================================
"""SLD presentation coordinator attached to the canonical Canvas scene.

Canvas owns the Qt viewport and QGraphicsScene. This class owns only the
SLD presentation/rendering coordination and never creates a second viewport
or scene.
"""

from __future__ import annotations

from typing import Any

from .sld_document import SLDDocument
from .sld_layout import SLDLayout
from .sld_scene_renderer import SLDSceneRenderer


class SLDSurface:
    """Coordinate SLD presentation on an existing Canvas graphics view."""

    def __init__(self, graphics_view: Any, *, layout: SLDLayout | None = None) -> None:
        if graphics_view is None:
            raise ValueError("graphics_view must not be None")

        scene = getattr(graphics_view, "graphics_scene", None)
        if scene is None:
            raise TypeError("graphics_view must expose graphics_scene")

        self._graphics_view = graphics_view
        self._renderer = SLDSceneRenderer(scene, layout=layout)
        self._document_id: str | None = None

    @property
    def graphics_view(self) -> Any:
        """Return the injected canonical Canvas viewport."""
        return self._graphics_view

    @property
    def renderer(self) -> SLDSceneRenderer:
        """Return the SLD presentation renderer."""
        return self._renderer

    @property
    def document_id(self) -> str | None:
        """Return the currently presented SLD document identity."""
        return self._document_id

    def present(self, document: SLDDocument) -> None:
        """Render an SLD document onto the existing Canvas scene."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")

        self._document_id = document.document_id
        self._renderer.render(document.model)

    def clear_document(self) -> None:
        """Remove SLD presentation items and detach the logical document."""
        self._renderer.clear()
        self._document_id = None


__all__ = ["SLDSurface"]
