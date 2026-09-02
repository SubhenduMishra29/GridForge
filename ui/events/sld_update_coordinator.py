# ============================================================
# File: ui/events/sld_update_coordinator.py
# GridForge V2 — SLD Update Coordinator
# Author: Subhendu Mishra
# ============================================================
"""Coordinate Application read refreshes into the open SLD and Canvas.

This presentation adapter consumes Application events and asks the public
Application facade for immutable read snapshots. It then synchronizes the
SLD document and invokes an injected Canvas refresh callback.

No Core model object crosses this boundary.
"""

from __future__ import annotations

from collections.abc import Callable

from core.application.application import Application
from core.application.events import ApplicationEvent, NetworkChanged

from ui.sld.sld_document import SLDDocument
from ui.sld.sld_read_synchronizer import SLDReadSynchronizer


CanvasRefresh = Callable[[], None]


class SLDUpdateCoordinator:
    """Apply authoritative Application changes to the open SLD projection."""

    def __init__(
        self,
        *,
        application: Application,
        document: SLDDocument,
        synchronizer: SLDReadSynchronizer,
        canvas_refresh: CanvasRefresh,
    ) -> None:
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

    def refresh(self, event: ApplicationEvent) -> None:
        """Refresh the presentation after a relevant Application fact."""
        if not isinstance(event, ApplicationEvent):
            raise TypeError("event must be an ApplicationEvent")

        if isinstance(event, NetworkChanged):
            self._synchronizer.synchronize_network(
                self._document,
                self._application.read_network(),
            )
            self._canvas_refresh()

    def dispose(self) -> None:
        """Release coordinator-owned references."""
        self._canvas_refresh = lambda: None


__all__ = ["SLDUpdateCoordinator", "CanvasRefresh"]
