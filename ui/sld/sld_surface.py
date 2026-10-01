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

from .sld_document import SLDDocument


class SLDSurface:
    """Compatibility adapter for the canonical :class:`SLDCanvasSurface`.

    This class does not own a scene, projection, renderer, or document.
    All presentation is delegated to the already-composed canonical SLD
    surface, preventing a second SLD presentation mechanism.
    """

    def __init__(self, canvas_surface: Any) -> None:
        if canvas_surface is None:
            raise ValueError("canvas_surface must not be None")
        if not callable(getattr(canvas_surface, "present_document", None)):
            raise TypeError("canvas_surface must expose present_document().")
        if not callable(getattr(canvas_surface, "clear_document", None)):
            raise TypeError("canvas_surface must expose clear_document().")
        self._canvas_surface = canvas_surface

    @property
    def canvas_surface(self) -> Any:
        return self._canvas_surface

    @property
    def document_id(self) -> str | None:
        return getattr(self._canvas_surface, "document_id", None)

    def present(self, document: SLDDocument) -> None:
        self._canvas_surface.present_document(document)

    def clear_document(self) -> None:
        self._canvas_surface.clear_document()

    def close(self) -> None:
        self.clear_document()


__all__ = ["SLDSurface"]
