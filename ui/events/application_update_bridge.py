# ============================================================
# File: ui/events/application_update_bridge.py
# GridForge V2 — Application to Presentation Bridge
# Author: Subhendu Mishra
# ============================================================
"""Translate successful application command completion into UI updates.

The bridge contains presentation routing policy only. It never mutates Core
state and does not depend on Qt.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from application.commands.command import Command
from application.commands.command_result import CommandResult

from .ui_update_bus import UIUpdate, UIUpdateBus


class ApplicationUpdateBridge:
    """Translate successful application command results into UI updates."""

    DEFAULT_KINDS = frozenset(
        {"document_changed", "projection_invalidated", "workspace_changed"}
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
        """Publish one explicitly approved presentation update kind."""
        if not kind:
            raise ValueError("kind must not be empty")
        ui_kind = self._kind_map.get(kind, kind)
        if ui_kind in self.DEFAULT_KINDS or ui_kind in self._kind_map.values():
            self._bus.publish(UIUpdate(kind=ui_kind, payload=payload))

    def publish_command_result(
        self,
        command: Command,
        result: CommandResult,
    ) -> None:
        """Translate a successful command completion into a UI update.

        Commands opt into presentation invalidation by exposing a
        ``presentation_update_kind`` attribute. The bridge deliberately ignores
        failed results so unsuccessful mutations cannot refresh the UI as if
        Core state had changed.
        """
        if not result.success:
            return

        kind = getattr(command, "presentation_update_kind", None)
        if kind is None:
            return

        self.publish_result(kind, result.value)

    def callback(self):
        """Return a dispatcher-compatible completion callback."""
        return self.publish_command_result


__all__ = ["ApplicationUpdateBridge"]
