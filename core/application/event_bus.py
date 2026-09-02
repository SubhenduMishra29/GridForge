# ============================================================
# File: core/application/event_bus.py
# GridForge V2 — Application Event Bus
# Author: Subhendu Mishra
# ============================================================
"""Headless publication boundary for Application events.

The Core/Application event contract is deliberately UI-agnostic. This bus
routes those events to registered consumers while keeping dispatch ownership
inside the Application layer.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from threading import RLock
from typing import TypeVar

from .events import ApplicationEvent

EventHandler = Callable[[ApplicationEvent], None]
E = TypeVar("E", bound=ApplicationEvent)


class ApplicationEventBus:
    """Synchronous, deterministic publisher for Application events."""

    def __init__(self) -> None:
        self._handlers: dict[type[ApplicationEvent], list[EventHandler]] = defaultdict(list)
        self._lock = RLock()

    def subscribe(
        self,
        event_type: type[E],
        handler: Callable[[E], None],
    ) -> None:
        if not isinstance(event_type, type) or not issubclass(event_type, ApplicationEvent):
            raise TypeError("event_type must derive from ApplicationEvent")
        if not callable(handler):
            raise TypeError("handler must be callable")
        with self._lock:
            handlers = self._handlers[event_type]
            if handler not in handlers:
                handlers.append(handler)  # type: ignore[arg-type]

    def unsubscribe(
        self,
        event_type: type[E],
        handler: Callable[[E], None],
    ) -> None:
        with self._lock:
            handlers = self._handlers.get(event_type)
            if not handlers:
                return
            try:
                handlers.remove(handler)  # type: ignore[arg-type]
            except ValueError:
                return
            if not handlers:
                self._handlers.pop(event_type, None)

    def publish(self, event: ApplicationEvent) -> None:
        if not isinstance(event, ApplicationEvent):
            raise TypeError("event must be an ApplicationEvent")

        for handler in self._snapshot_handlers(type(event)):
            handler(event)

    def clear(self) -> None:
        with self._lock:
            self._handlers.clear()

    def _snapshot_handlers(
        self,
        event_type: type[ApplicationEvent],
    ) -> Iterable[EventHandler]:
        with self._lock:
            return tuple(self._handlers.get(event_type, ()))


__all__ = ["ApplicationEventBus", "EventHandler"]
