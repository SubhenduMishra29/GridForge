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
from ..transaction import Transaction


@dataclass(frozen=True, slots=True)
class SLDState:
    """Immutable snapshot of presentation-only SLD state."""
    nodes: tuple[dict[str, Any], ...] = ()
    connections: tuple[dict[str, Any], ...] = ()


class SLDService:
    """Application boundary for persistent SLD presentation state.

    The service performs presentation mutation only inside the Application
    transaction supplied by CommandManager. It never owns history or undo/redo.
    """

    COMMAND_TYPES = frozenset({
        "sld.set_node_position",
        "sld.add_node",
        "sld.remove_node",
        "sld.add_connection",
        "sld.remove_connection",
    })

    def __init__(self, document: Any) -> None:
        self._document = None
        self.bind_document(document)

    @property
    def document(self) -> Any:
        if self._document is None:
            raise RuntimeError("SLD service has no active document.")
        return self._document

    @property
    def is_bound(self) -> bool:
        return self._document is not None

    def bind_document(self, document: Any) -> None:
        """Bind the service to the currently active presentation document."""
        if document is None:
            raise TypeError("SLDService requires an SLD document.")
        self._document = document

    def detach_document(self) -> Any:
        """Detach the active document so closed projects cannot be mutated."""
        document = self._document
        self._document = None
        return document

    def supports(self, command: Command) -> bool:
        return command.command_type in self.COMMAND_TYPES

    def execute(self, command: Command, transaction: Transaction) -> ApplicationResult:
        """Apply one SLD command inside the canonical Application transaction."""
        if not isinstance(command, Command):
            raise TypeError("command must be a Command")
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction")
        if not self.supports(command):
            raise ValueError(f"Unsupported SLD command: {command.command_type}")
        handler = {
            "sld.set_node_position": self._set_node_position,
            "sld.add_node": self._add_node,
            "sld.remove_node": self._remove_node,
            "sld.add_connection": self._add_connection,
            "sld.remove_connection": self._remove_connection,
        }[command.command_type]
        return handler(command, transaction)

    def _set_node_position(self, command: Command, transaction: Transaction) -> ApplicationResult:
        p = command.payload
        node = self.document.model.get_node(p["node_id"])
        previous = node.position
        self.document.set_node_position(p["node_id"], float(p["x"]), float(p["y"]))
        transaction.record_undo(
            lambda node_id=p["node_id"], position=previous: self.document.set_node_position(node_id, *position)
        )
        return ApplicationResult.success_result(
            message="SLD node position updated.",
            metadata={"presentation_operation": "set_node_position", "node_id": p["node_id"]},
        )

    def _add_node(self, command: Command, transaction: Transaction) -> ApplicationResult:
        p = command.payload
        self.document.model.create_node(
            node_id=p["node_id"],
            equipment_id=p.get("equipment_id"),
            x=float(p["x"]),
            y=float(p["y"]),
        )
        self.document.mark_modified()
        transaction.record_undo(lambda node_id=p["node_id"]: self.document.model.remove_node(node_id))
        return ApplicationResult.success_result(
            message="SLD node added.",
            metadata={"presentation_operation": "add_node", "node_id": p["node_id"]},
        )

    def _remove_node(self, command: Command, transaction: Transaction) -> ApplicationResult:
        node_id = command.payload["node_id"]
        node = self.document.model.get_node(node_id)
        node_snapshot = node.to_dict()
        connection_snapshots = tuple(
            connection.to_dict()
            for connection in self.document.model.connections
            if connection.source_node_id == node_id or connection.target_node_id == node_id
        )
        self.document.model.remove_node(node_id)
        self.document.mark_modified()

        def restore() -> None:
            self.document.model.create_node(
                node_id=node_snapshot["node_id"],
                equipment_id=node_snapshot.get("equipment_id"),
                x=node_snapshot.get("x", 0.0),
                y=node_snapshot.get("y", 0.0),
                properties=node_snapshot.get("properties", {}),
            )
            for snapshot in connection_snapshots:
                self.document.model.create_connection(
                    connection_id=snapshot["connection_id"],
                    source_node_id=snapshot["source_node_id"],
                    target_node_id=snapshot["target_node_id"],
                    properties=snapshot.get("properties", {}),
                )

        transaction.record_undo(restore)
        return ApplicationResult.success_result(
            message="SLD node removed.",
            metadata={"presentation_operation": "remove_node", "node_id": node_id},
        )

    def _add_connection(self, command: Command, transaction: Transaction) -> ApplicationResult:
        p = command.payload
        self.document.model.create_connection(
            connection_id=p["connection_id"],
            source_node_id=p["source_node_id"],
            target_node_id=p["target_node_id"],
        )
        self.document.mark_modified()
        transaction.record_undo(
            lambda connection_id=p["connection_id"]: self.document.model.remove_connection(connection_id)
        )
        return ApplicationResult.success_result(
            message="SLD connection added.",
            metadata={"presentation_operation": "add_connection", "connection_id": p["connection_id"]},
        )

    def _remove_connection(self, command: Command, transaction: Transaction) -> ApplicationResult:
        connection_id = command.payload["connection_id"]
        connection = self.document.model.get_connection(connection_id)
        snapshot = connection.to_dict()
        self.document.model.remove_connection(connection_id)
        self.document.mark_modified()

        def restore() -> None:
            self.document.model.create_connection(
                connection_id=snapshot["connection_id"],
                source_node_id=snapshot["source_node_id"],
                target_node_id=snapshot["target_node_id"],
                properties=snapshot.get("properties", {}),
            )

        transaction.record_undo(restore)
        return ApplicationResult.success_result(
            message="SLD connection removed.",
            metadata={"presentation_operation": "remove_connection", "connection_id": connection_id},
        )


__all__ = ["SLDService", "SLDState"]
