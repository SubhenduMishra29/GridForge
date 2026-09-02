# ============================================================
# File: ui/events/update_boundary.py
# GridForge V2 — UI Update Boundary
# Author: Subhendu Mishra
# ============================================================
"""Translate Application events into presentation projection updates.

The boundary is intentionally small and toolkit-independent. It consumes
headless Application events and delegates projection refresh to an injected
callback. It never mutates Core state and never creates Qt objects.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.application.event_bus import ApplicationEventBus
from core.application.events import ApplicationEvent


ProjectionRefresh = Callable[[ApplicationEvent], None]


class UIUpdateBoundary:
    """Own the Application-event-to-projection refresh boundary."""

    def __init__(
        self,
        *,
        event_bus: ApplicationEventBus,
        refresh: ProjectionRefresh,
    ) -> None:
        if not isinstance(event_bus, ApplicationEventBus):
            raise TypeError("event_bus must be an ApplicationEventBus.")
        if not callable(refresh):
            raise TypeError("refresh must be callable.")

        self._event_bus = event_bus
        self._refresh = refresh
        self._subscribed = False

    @property
    def subscribed(self) -> bool:
        """Return whether the boundary is subscribed to Application events."""
        return self._subscribed

    def subscribe(self) -> None:
        """Subscribe to the base ApplicationEvent stream."""
        if self._subscribed:
            return
        self._event_bus.subscribe(ApplicationEvent, self._on_event)
        self._subscribed = True

    def unsubscribe(self) -> None:
        """Detach from the Application event stream."""
        if not self._subscribed:
            return
        self._event_bus.unsubscribe(ApplicationEvent, self._on_event)
        self._subscribed = False

    def handle(self, event: ApplicationEvent) -> None:
        """Translate one Application fact into a projection refresh."""
        if not isinstance(event, ApplicationEvent):
            raise TypeError("event must be an ApplicationEvent.")
        self._refresh(event)

    def _on_event(self, event: ApplicationEvent) -> None:
        self.handle(event)

    def dispose(self) -> None:
        """Release the event subscription."""
        self.unsubscribe()


__all__ = ["UIUpdateBoundary", "ProjectionRefresh"]
