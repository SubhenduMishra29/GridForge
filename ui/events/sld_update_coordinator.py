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
    ProjectLoaded,
    ProjectClosed,
    ProtectionChanged,
    SLDPresentationChanged,
    TopologyChanged,
)

from ui.sld.sld_read_synchronizer import SLDReadSynchronizer

CanvasRefresh = Callable[[], None]


class SLDUpdateCoordinator:
    """Project Application read state into domain-scoped SLD projections."""

    event_types = (
        ElementCreated,
        ElementUpdated,
        ElementRemoved,
        TopologyChanged,
        NetworkChanged,
        ProtectionChanged,
        SLDPresentationChanged,
        ProjectLoaded,
        ProjectClosed,
    )

    def __init__(
        self,
        *,
        application: Application,
        synchronizer: SLDReadSynchronizer,
        canvas_refresh: CanvasRefresh,
    ) -> None:
        if not isinstance(application, Application):
            raise TypeError("application must be an Application")
        if not isinstance(synchronizer, SLDReadSynchronizer):
            raise TypeError("synchronizer must be an SLDReadSynchronizer")
        if not callable(canvas_refresh):
            raise TypeError("canvas_refresh must be callable")
        if synchronizer.application is not None and synchronizer.application is not application:
            raise RuntimeError("SLDReadSynchronizer is already attached to another Application")
        if synchronizer.application is None:
            synchronizer.attach_application(application)
        self._application = application
        self._synchronizer = synchronizer
        self._canvas_refresh = canvas_refresh
        self._disposed = False

    def refresh(self, event: ApplicationEvent) -> None:
        """Refresh read-only projections after an authoritative Application fact."""
        if self._disposed:
            return
        if not isinstance(event, ApplicationEvent):
            raise TypeError("event must be an ApplicationEvent")

        if isinstance(event, ProjectClosed):
            self._canvas_refresh()
            return

        if isinstance(event, ProjectLoaded):
            self._synchronizer.synchronize_network_from_application()
            self._synchronizer.synchronize_protection_from_application()
            self._canvas_refresh()
            return

        if isinstance(event, ProtectionChanged):
            self._synchronizer.synchronize_protection_from_application()
            self._canvas_refresh()
            return

        if isinstance(event, (ElementCreated, ElementUpdated, ElementRemoved)):
            element_type = str(event.payload.get("element_type", "")).lower()
            if element_type == "relay":
                self._synchronizer.synchronize_protection_from_application()
            else:
                self._synchronizer.synchronize_network_from_application()
            self._canvas_refresh()
            return

        if isinstance(event, (TopologyChanged, NetworkChanged)):
            self._synchronizer.synchronize_network_from_application()
            self._canvas_refresh()
            return

        if isinstance(event, SLDPresentationChanged):
            self._canvas_refresh()

    def dispose(self) -> None:
        if self._disposed:
            return
        self._canvas_refresh = lambda: None
        self._disposed = True


__all__ = ["SLDUpdateCoordinator", "CanvasRefresh"]
