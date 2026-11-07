# ============================================================
# File: ui/events/update_boundary.py
# GridForge V2 — UI Update Boundary
# ============================================================
"""Single Application-event ingress for UI projections."""

from __future__ import annotations

from core.application.event_bus import ApplicationEventBus
from core.application.events import ApplicationEvent
from ui.core.qt import QObject, Qt, Signal, Slot
from ui.projection.ui_projection_coordinator import UIProjectionCoordinator


class _QueuedApplicationEventBridge(QObject):
    """Marshal worker-published Application events onto the owning Qt thread."""

    event_received = Signal(object)

    def __init__(self, receiver: object) -> None:
        super().__init__()
        self._receiver = receiver
        self.event_received.connect(self._deliver, Qt.ConnectionType.QueuedConnection)

    @Slot(object)
    def _deliver(self, event: object) -> None:
        self._receiver(event)


class UIUpdateBoundary:
    """Own the only ApplicationEventBus subscription used by UI projections."""

    def __init__(self, *, event_bus: ApplicationEventBus, projection_coordinator: UIProjectionCoordinator, queued: bool = False) -> None:
        if not isinstance(event_bus, ApplicationEventBus):
            raise TypeError("event_bus must be an ApplicationEventBus.")
        if not isinstance(projection_coordinator, UIProjectionCoordinator):
            raise TypeError("projection_coordinator must be a UIProjectionCoordinator.")
        self._event_bus = event_bus
        self._projection_coordinator = projection_coordinator
        self._subscribed = False
        self._disposed = False
        self._queued_bridge = _QueuedApplicationEventBridge(self.handle) if queued else None

    @property
    def subscribed(self) -> bool:
        return self._subscribed

    @property
    def projection_coordinator(self) -> UIProjectionCoordinator:
        return self._projection_coordinator

    def subscribe(self) -> None:
        if self._disposed:
            raise RuntimeError("UIUpdateBoundary has been disposed.")
        if self._subscribed:
            return
        self._event_bus.subscribe(ApplicationEvent, self._on_event)
        self._subscribed = True

    def unsubscribe(self) -> None:
        if not self._subscribed:
            return
        self._event_bus.unsubscribe(ApplicationEvent, self._on_event)
        self._subscribed = False

    def handle(self, event: ApplicationEvent) -> None:
        if self._disposed:
            return
        if not isinstance(event, ApplicationEvent):
            raise TypeError("event must be an ApplicationEvent.")
        self._projection_coordinator.handle(event)

    def _on_event(self, event: ApplicationEvent) -> None:
        bridge = self._queued_bridge
        if bridge is None:
            self.handle(event)
        else:
            bridge.event_received.emit(event)

    def dispose(self) -> None:
        if self._disposed:
            return
        self.unsubscribe()
        self._projection_coordinator.dispose()
        self._disposed = True


__all__ = ["UIUpdateBoundary"]
