# ============================================================
# GridForge V2 — Central UI Projection Coordinator
# ============================================================
# Author: Subhendu Mishra
# ============================================================
"""Framework-neutral fan-out from the Application event ingress.

The coordinator deliberately contains routing only. Specialized projections
own read-model refresh and presentation adaptation; this class does not know
about panels, Qt, Core objects, or projection-specific transformation logic.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from core.application.events import ApplicationEvent


class UIProjectionCoordinator:
    """Route each Application event to registered interested projections."""

    def __init__(self, projections: Iterable[Any] = ()) -> None:
        self._routes: dict[type[ApplicationEvent], list[Any]] = defaultdict(list)
        self._projections: list[Any] = []
        self._disposed = False
        for projection in projections:
            self.register(projection)

    @property
    def projections(self) -> tuple[Any, ...]:
        """Return registered projections in composition order."""
        return tuple(self._projections)

    def register(self, projection: Any) -> None:
        """Register one projection by its declared Application event interests."""
        self._ensure_active()
        if projection is None or not callable(getattr(projection, "refresh", None)):
            raise TypeError("projection must provide refresh(event).")
        if projection in self._projections:
            return
        event_types = getattr(projection, "event_types", None)
        if event_types is None:
            raise TypeError("projection must expose event_types.")
        for event_type in tuple(event_types):
            if not isinstance(event_type, type) or not issubclass(event_type, ApplicationEvent):
                raise TypeError("projection event_types must derive from ApplicationEvent.")
            self._routes[event_type].append(projection)
        self._projections.append(projection)

    def unregister(self, projection: Any) -> None:
        """Remove one projection from all routing paths."""
        if projection not in self._projections:
            return
        self._projections.remove(projection)
        for event_type in tuple(self._routes):
            routes = self._routes[event_type]
            if projection in routes:
                routes.remove(projection)
            if not routes:
                self._routes.pop(event_type, None)

    def handle(self, event: ApplicationEvent) -> None:
        """Fan one immutable Application fact to each interested projection once."""
        self._ensure_active()
        if not isinstance(event, ApplicationEvent):
            raise TypeError("event must be an ApplicationEvent.")
        delivered: set[int] = set()
        for event_type, projections in tuple(self._routes.items()):
            if isinstance(event, event_type):
                for projection in tuple(projections):
                    marker = id(projection)
                    if marker in delivered:
                        continue
                    delivered.add(marker)
                    projection.refresh(event)

    def dispose(self) -> None:
        """Dispose registered projections and release all routing state."""
        if self._disposed:
            return
        for projection in tuple(self._projections):
            dispose = getattr(projection, "dispose", None)
            if callable(dispose):
                dispose()
        self._routes.clear()
        self._projections.clear()
        self._disposed = True

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("UIProjectionCoordinator has been disposed.")


__all__ = ["UIProjectionCoordinator"]
