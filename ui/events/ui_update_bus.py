# ============================================================
# File: ui/events/ui_update_bus.py
# GridForge V2 — Presentation Update Boundary
# Author: Subhendu Mishra
# ============================================================
"""Small presentation-facing update boundary.

This module routes application/domain results to presentation consumers. It is
not a domain event bus, contains no engineering logic, and has no Qt
 dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class UIUpdate:
    """Immutable notification describing presentation-relevant change."""

    kind: str
    payload: Any = None


UIUpdateHandler = Callable[[UIUpdate], None]


class UIUpdateBus:
    """Deterministic synchronous dispatcher for presentation updates."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[UIUpdateHandler]] = {}

    def subscribe(self, kind: str, handler: UIUpdateHandler) -> None:
        if not kind:
            raise ValueError("kind must not be empty")
        handlers = self._handlers.setdefault(kind, [])
        if handler not in handlers:
            handlers.append(handler)

    def unsubscribe(self, kind: str, handler: UIUpdateHandler) -> None:
        handlers = self._handlers.get(kind)
        if not handlers:
            return
        if handler in handlers:
            handlers.remove(handler)
        if not handlers:
            self._handlers.pop(kind, None)

    def publish(self, update: UIUpdate) -> None:
        """Deliver one update to a stable snapshot of current subscribers."""
        for handler in tuple(self._handlers.get(update.kind, ())):
            handler(update)

    def clear(self) -> None:
        """Remove all presentation subscriptions."""
        self._handlers.clear()


__all__ = ["UIUpdate", "UIUpdateBus", "UIUpdateHandler"]
