# ============================================================
# File: ui/events/sld_update_coordinator.py
# GridForge V2 — SLD Update Coordinator
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
    TopologyChanged,
)

from ui.sld.sld_document import SLDDocument
from ui.sld.sld_read_synchronizer import SLDReadSynchronizer

CanvasRefresh = Callable[[], None]


class SLDUpdateCoordinator:
    """Apply authoritative Application semantic facts to the active SLD projection.

    Semantic element/topology events are the authoritative invalidation signal.
    NetworkChanged is an aggregate network-state invalidation signal and may
    coalesce several semantic changes, but it is never used to represent an
    arbitrary successful Application command.
    """

    _PRESENTATION_EVENTS = (
        ElementCreated,
        ElementUpdated,
        ElementRemoved,
        TopologyChanged,
        NetworkChanged,
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
        self._document = document
        self._synchronizer = synchronizer
        self._canvas_refresh = canvas_refresh

    @property
    def document(self) -> SLDDocument:
        """Return the active persistent presentation document."""
        presentation = self._application.presentation
        if isinstance(presentation, SLDDocument):
            self._document = presentation
        return self._document

    def refresh(self, event: ApplicationEvent) -> None:
        """Refresh the active presentation after an authoritative Application fact."""
        if not isinstance(event, ApplicationEvent):
            raise TypeError("event must be an ApplicationEvent")
        if isinstance(event, self._PRESENTATION_EVENTS):
            self._synchronizer.synchronize_network(
                self.document,
                self._application.read_network(),
            )
            self._canvas_refresh()

    def dispose(self) -> None:
        self._canvas_refresh = lambda: None


__all__ = ["SLDUpdateCoordinator", "CanvasRefresh"]
