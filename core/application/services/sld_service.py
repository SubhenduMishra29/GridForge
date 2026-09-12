# ============================================================
# File: core/application/services/sld_service.py
# GridForge V2 — Application SLD presentation service
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..application import ApplicationResult
from ..command import Command
from ._model_service_support import ModelServiceSupport


@dataclass(frozen=True, slots=True)
class SLDState:
    """Immutable snapshot of presentation-only SLD state."""
    nodes: tuple[dict[str, Any], ...] = ()
    connections: tuple[dict[str, Any], ...] = ()


class SLDService:
    """Application boundary for persistent SLD presentation state."""

    def __init__(self, document: Any) -> None:
        if document is None:
            raise TypeError("SLDService requires an SLD document.")
        self._document = document

    @property
    def document(self) -> Any:
        return self._document

    def execute(self, command: Command) -> ApplicationResult:
        """Apply one validated SLD command to the presentation document."""
        handler = {
            "sld.set_node_position": self._set_node_position,
            "sld.add_node": self._add_node,
            "sld.remove_node": self._remove_node,
            "sld.add_connection": self._add_connection,
            "sld.remove_connection": self._remove_connection,
        }.get(command.command_type)
        if handler is None:
            return ApplicationResult.failure(
                f"Unsupported SLD command: {command.command_type}"
            )
        return handler(command)

    def _set_node_position(self, command: Command) -> ApplicationResult:
        p = command.payload
        self._document.set_node_position(p["node_id"], float(p["x"]), float(p["y"]))
        return ApplicationResult.success("SLD node position updated.")

    def _add_node(self, command: Command) -> ApplicationResult:
        p = command.payload
        self._document.add_node(p["node_id"], p["equipment_id"], float(p["x"]), float(p["y"]))
        return ApplicationResult.success("SLD node added.")

    def _remove_node(self, command: Command) -> ApplicationResult:
        self._document.remove_node(command.payload["node_id"])
        return ApplicationResult.success("SLD node removed.")

    def _add_connection(self, command: Command) -> ApplicationResult:
        p = command.payload
        self._document.add_connection(p["connection_id"], p["source_node_id"], p["target_node_id"])
        return ApplicationResult.success("SLD connection added.")

    def _remove_connection(self, command: Command) -> ApplicationResult:
        self._document.remove_connection(command.payload["connection_id"])
        return ApplicationResult.success("SLD connection removed.")


__all__ = ["SLDService", "SLDState"]
