# ============================================================
# File: core/application/services/electrical_connection_service.py
# GridForge V2 — Canonical electrical connection service
# Author: Subhendu Mishra
# ============================================================
"""Application use cases for connecting, disconnecting, and reconnecting Core terminals."""

from __future__ import annotations

from typing import Any

from ..command import Command
from ..commands.connection_commands import CONNECT_TERMINAL, DISCONNECT_TERMINAL, RECONNECT_TERMINAL
from ..endpoint_reference import EndpointReference
from ..endpoint_resolver import EndpointResolver, resolve_terminal_reference
from ..errors import ResourceError, ValidationError
from ..results import ApplicationResult
from ..transaction import Transaction


class ElectricalConnectionService:
    """Own terminal connectivity orchestration without owning topology."""

    COMMAND_TYPES = frozenset({CONNECT_TERMINAL, DISCONNECT_TERMINAL, RECONNECT_TERMINAL})

    def supports(self, command: Command) -> bool:
        return command.command_type in self.COMMAND_TYPES

    def execute(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        if not isinstance(command, Command):
            raise TypeError("command must be a Command.")
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction.")
        if not self.supports(command):
            raise ValueError(f"Unsupported electrical connection command: {command.command_type}")
        if command.command_type == CONNECT_TERMINAL:
            return self._connect(command, context, transaction, operation="connect")
        if command.command_type == RECONNECT_TERMINAL:
            return self._connect(command, context, transaction, operation="reconnect")
        return self._disconnect(command, context, transaction)

    def _connect(self, command: Command, context: Any, transaction: Transaction, *, operation: str) -> ApplicationResult:
        terminal_ref = command.payload["terminal"]
        target_ref = command.payload["target"]
        terminal = self._resolve_terminal(context, terminal_ref)
        target = EndpointResolver.resolve(context, target_ref)
        previous = terminal.endpoint

        if previous is target:
            return ApplicationResult.success_result(
                message=f"Terminal {terminal_ref} already targets the requested endpoint.",
                metadata=self._metadata(terminal_ref, target_ref, terminal, target, operation, changed=False),
            )

        self._set_endpoint(context, terminal, target)
        transaction.record_undo(
            lambda terminal=terminal, previous=previous, context=context: self._restore_endpoint(
                context, terminal, previous
            )
        )
        return ApplicationResult.success_result(
            message=f"Terminal {terminal_ref} {operation}ed.",
            metadata=self._metadata(terminal_ref, target_ref, terminal, target, operation, changed=True),
        )

    def _disconnect(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        terminal_ref = command.payload["terminal"]
        expected_target = command.payload.get("expected_target")
        terminal = self._resolve_terminal(context, terminal_ref)
        current = terminal.endpoint

        if current is None:
            return ApplicationResult.success_result(
                message=f"Terminal {terminal_ref} is already disconnected.",
                metadata=self._metadata(terminal_ref, expected_target, terminal, None, "disconnect", changed=False),
            )

        if expected_target is not None:
            expected = EndpointResolver.resolve(context, expected_target)
            if current is not expected:
                raise ValidationError(
                    code="ENDPOINT_MISMATCH",
                    message="Terminal is not attached to the expected endpoint.",
                    details={"equipment_id": terminal_ref.object_id, "terminal_role": terminal_ref.terminal_role},
                )

        self._set_endpoint(context, terminal, None)
        transaction.record_undo(
            lambda terminal=terminal, current=current, context=context: self._restore_endpoint(
                context, terminal, current
            )
        )
        return ApplicationResult.success_result(
            message=f"Terminal {terminal_ref} disconnected.",
            metadata=self._metadata(terminal_ref, expected_target, terminal, current, "disconnect", changed=True),
        )

    @staticmethod
    def _resolve_terminal(context: Any, reference: EndpointReference) -> Any:
        if not isinstance(reference, EndpointReference) or not reference.is_terminal:
            raise ValidationError(
                code="INVALID_TERMINAL_REFERENCE",
                message="Electrical connection source must be a terminal EndpointReference.",
                details={},
            )
        return resolve_terminal_reference(context, reference)

    @staticmethod
    def _set_endpoint(context: Any, terminal: Any, endpoint: Any | None) -> None:
        if endpoint is None:
            terminal.detach()
        else:
            terminal.attach(endpoint)
        network = getattr(context, "network", None)
        if network is None:
            raise ResourceError(
                code="NETWORK_CONTEXT_MISSING",
                message="Application context does not expose the canonical Core Network.",
                details={},
            )
        network.invalidate_topology()

    @classmethod
    def _restore_endpoint(cls, context: Any, terminal: Any, endpoint: Any | None) -> None:
        cls._set_endpoint(context, terminal, endpoint)

    @staticmethod
    def _metadata(
        terminal_ref: EndpointReference,
        target_ref: EndpointReference | None,
        terminal: Any,
        target: Any | None,
        operation: str,
        *,
        changed: bool,
    ) -> dict[str, Any]:
        return {
            "connection_operation": operation,
            "connection_changed": changed,
            "terminal": dict(terminal_ref.to_mapping()),
            "target": dict(target_ref.to_mapping()) if target_ref is not None else None,
            "equipment_id": str(getattr(getattr(terminal, "owner", None), "id", terminal_ref.object_id)),
            "terminal_role": str(getattr(terminal, "role", terminal_ref.terminal_role)),
            "target_object_id": getattr(target, "id", None),
        }


class ElectricalConnectionCommandHandlers:
    """Bind electrical connection commands to the canonical Application service."""

    def __init__(self, service: ElectricalConnectionService | None = None) -> None:
        self._service = service or ElectricalConnectionService()

    def handlers(self) -> dict[str, Any]:
        return {
            CONNECT_TERMINAL: self.connect,
            DISCONNECT_TERMINAL: self.disconnect,
            RECONNECT_TERMINAL: self.reconnect,
        }

    def connect(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._service.execute(command, context, transaction)

    def disconnect(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._service.execute(command, context, transaction)

    def reconnect(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._service.execute(command, context, transaction)


__all__ = ["ElectricalConnectionService", "ElectricalConnectionCommandHandlers"]
