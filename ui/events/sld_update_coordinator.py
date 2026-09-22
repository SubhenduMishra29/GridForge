# ============================================================
# File: core/ui/events/sld_update_coordinator.py
# GridForge V2 — SLD Update Coordinator
# ============================================================
# Author: Subhendu Mishra
# ============================================================

"""Coordinate Application semantic events into the active SLD projection."""

from __future__ import annotations

from collections.abc import Callable

from core.application.application import Application
from core.application.events import (
    ApplicationEvent,
    ElementCreated,
    ElementRemoved,
    ElementUpdated,
    NetworkChanged,
    ProjectLoaded,
    ProjectClosed,
    SLDPresentationChanged,
    TopologyChanged,
)

from ui.sld.sld_document import SLDDocument
from ui.sld.sld_read_synchronizer import SLDReadSynchronizer

CanvasRefresh = Callable[[], None]


class SLDUpdateCoordinator:
    """Apply authoritative Application semantic facts to the active SLD projection."""

    event_types = (
        ElementCreated,
        ElementUpdated,
        ElementRemoved,
        TopologyChanged,
        NetworkChanged,
        SLDPresentationChanged,
        ProjectLoaded,
        ProjectClosed,
    )

    def __init__(self, *, application: Application, document: SLDDocument,
                 synchronizer: SLDReadSynchronizer, canvas_refresh: CanvasRefresh) -> None:
        if not isinstance(application, Application):
            raise TypeError("application must be an Application")
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        if not isinstance(synchronizer, SLDReadSynchronizer):
            raise TypeError("synchronizer must be an SLDReadSynchronizer")
        if not callable(canvas_refresh):
            raise TypeError("canvas_refresh must be callable")
        self._application = application
        self._document: SLDDocument | None = document
        self._synchronizer = synchronizer
        self._canvas_refresh = canvas_refresh
        self._disposed = False

    @property
    def document(self) -> SLDDocument | None:
        """Return the currently bound presentation document."""
        if self._disposed:
            return None
        presentation = self._application.presentation
        if isinstance(presentation, SLDDocument):
            self._document = presentation
        return self._document

    def bind_document(self, document: SLDDocument) -> None:
        """Explicitly bind a newly active SLD document."""
        if self._disposed:
            raise RuntimeError("SLDUpdateCoordinator has been disposed")
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        self._document = document

    def detach_document(self) -> None:
        """Drop the cached presentation reference during project close."""
        self._document = None

    def refresh(self, event: ApplicationEvent) -> None:
        """Refresh the active presentation after an authoritative Application fact."""
        if self._disposed:
            return
        if not isinstance(event, ApplicationEvent):
            raise TypeError("event must be an ApplicationEvent")
        if isinstance(event, ProjectClosed):
            self.detach_document()
            self._canvas_refresh()
            return
        if isinstance(event, ProjectLoaded):
            presentation = self._application.presentation
            if isinstance(presentation, SLDDocument):
                self.bind_document(presentation)
        if isinstance(event, self.event_types):
            document = self.document
            if document is None:
                return
            initial_positions = {}
            if isinstance(event, ElementCreated):
                x = event.metadata.get("presentation_x")
                y = event.metadata.get("presentation_y")
                if x is not None and y is not None:
                    initial_positions[event.element_id] = (float(x), float(y))
            self._synchronizer.synchronize_network(
                document,
                self._application.read_network(),
                initial_positions=initial_positions,
            )
            self._canvas_refresh()

    def dispose(self) -> None:
        if self._disposed:
            return
        self.detach_document()
        self._canvas_refresh = lambda: None
        self._disposed = True


__all__ = ["SLDUpdateCoordinator", "CanvasRefresh"]
