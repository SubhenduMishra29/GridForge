# ============================================================
# File: ui/events/application_update_bridge.py
# GridForge V2 — Application to Presentation Bridge
# Author: Subhendu Mishra
# ============================================================
"""Translate successful application notifications into UI updates.

The bridge deliberately accepts an application-facing callback rather than
coupling the presentation layer to a particular application implementation.
It contains routing policy only; it never mutates Core state.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .ui_update_bus import UIUpdate, UIUpdateBus


class ApplicationUpdateBridge:
    """Translate application result notifications into presentation updates."""

    DEFAULT_KINDS = frozenset(
        {
            "document_changed",
            "projection_invalidated",
            "workspace_changed",
        }
    )

    def __init__(
        self,
        bus: UIUpdateBus,
        *,
        kind_map: Mapping[str, str] | None = None,
    ) -> None:
        if bus is None:
            raise ValueError("bus must not be None")
        self._bus = bus
        self._kind_map = dict(kind_map or {})

    @property
    def bus(self) -> UIUpdateBus:
        return self._bus

    def publish_result(self, kind: str, payload: Any = None) -> None:
        """Publish a presentation update for a successful application result."""
        if not kind:
            raise ValueError("kind must not be empty")
        ui_kind = self._kind_map.get(kind, kind)
        if ui_kind in self.DEFAULT_KINDS or ui_kind in self._kind_map.values():
            self._bus.publish(UIUpdate(kind=ui_kind, payload=payload))

    def callback(self) -> Callable[[str, Any], None]:
        """Return a small callback suitable for application composition."""
        return self.publish_result


__all__ = ["ApplicationUpdateBridge"]
