# ============================================================
# File: core/application/services/sld_service.py
# GridForge V2 — Application SLD presentation service
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..command import Command
from ..results import ApplicationResult


@dataclass(frozen=True, slots=True)
class SLDState:
    """Immutable snapshot of presentation-only SLD state."""
    nodes: tuple[dict[str, Any], ...] = ()
    connections: tuple[dict[str, Any], ...] = ()


class SLDService:
    """Application boundary for persistent SLD presentation state."""

    COMMAND_TYPES = frozenset({
        "sld.set_node_position",
        "sld.add_node",
        "sld.remove_node",
        "sld.add_connection",
        "sld.remove_connection",
    })

    def __init__(self, document: Any) -> None:
        if document is None:
            raise TypeError("SLDService requires an SLD document.")
        self._document = document

    @property
    def document(self) -> Any:
        return self._document

    def supports(self, command: Command) -> bool:
        return command.command_type in self.COMMAND_TYPES

    def execute(self, command: Command) -> ApplicationResult:
        """Apply one validated SLD command to the presentation document."""
        if not self.supports(command):
            return ApplicationResult.failure(f"Unsupported SLD command: {command.command_type}")
        handler = {
            "sld.set_node_position": self._set_node_position,
            "sld.add_node": self._add_node,
            "sld.remove_node": self._remove_node,
            "sld.add_connection": self._add_connection,
            "sld.remove_connection": self._remove_connection,
        }[command.command_type]
        return handler(command)

    def _set_node_position(self, command: Command) -> ApplicationResult:
        p = command.payload
        self._document.set_node_position(p["node_id"], float(p["x"]), float(p["y"]))
        return ApplicationResult.success("SLD node position updated.")

    def _add_node(self, command: Command) -> ApplicationResult:
        p = command.payload
        self._document.model.create_node(
            node_id=p["node_id"],
            equipment_id=p.get("equipment_id"),
            x=float(p["x"]),
            y=float(p["y"]),
        )
        self._document.mark_modified()
        return ApplicationResult.success("SLD node added.")

    def _remove_node(self, command: Command) -> ApplicationResult:
        self._document.model.remove_node(command.payload["node_id"])
        self._document.mark_modified()
        return ApplicationResult.success("SLD node removed.")

    def _add_connection(self, command: Command) -> ApplicationResult:
        p = command.payload
        self._document.model.create_connection(
            connection_id=p["connection_id"],
            source_node_id=p["source_node_id"],
            target_node_id=p["target_node_id"],
        )
        self._document.mark_modified()
        return ApplicationResult.success("SLD connection added.")

    def _remove_connection(self, command: Command) -> ApplicationResult:
        self._document.model.remove_connection(command.payload["connection_id"])
        self._document.mark_modified()
        return ApplicationResult.success("SLD connection removed.")


__all__ = ["SLDService", "SLDState"]
