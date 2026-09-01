# ============================================================
# File: ui/sld/sld_surface.py
# GridForge V2 — SLD Presentation Surface
# Author: Subhendu Mishra
# ============================================================
"""Concrete Qt host for the SLD presentation surface.

This module is the realization boundary between the logical SLD document and
its graphics scene. It owns Qt scene/view objects and delegates document
projection to SLDSceneRenderer. It does not own electrical truth or workspace
policy.
"""

from __future__ import annotations

from ui.core.qt import QGraphicsScene, QGraphicsView, QWidget

from .sld_document import SLDDocument
from .sld_layout import SLDLayout
from .sld_scene_renderer import SLDSceneRenderer


class SLDSurface(QGraphicsView):
    """Present one SLD document through a Qt graphics view."""

    def __init__(
        self,
        *,
        layout: SLDLayout | None = None,
        parent: QWidget | None = None,
    ) -> None:
        scene = QGraphicsScene()
        super().__init__(scene, parent)
        self._renderer = SLDSceneRenderer(scene, layout=layout)
        self._document_id: str | None = None

        self.setObjectName("GridForgeSLDSurface")
        self.setAcceptDrops(True)

    @property
    def renderer(self) -> SLDSceneRenderer:
        """Return the presentation renderer owned by this surface."""
        return self._renderer

    @property
    def document_id(self) -> str | None:
        """Return the currently presented SLD document identity."""
        return self._document_id

    def present(self, document: SLDDocument) -> None:
        """Render an SLD document without mutating the document itself."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")

        self._document_id = document.document_id
        self._renderer.render(document.model)

    def clear_document(self) -> None:
        """Remove all presentation items and detach the logical document."""
        self._renderer.clear()
        self._document_id = None


__all__ = ["SLDSurface"]
