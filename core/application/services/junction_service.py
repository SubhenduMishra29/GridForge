"""Application orchestration for authoritative Network Junction membership."""
from __future__ import annotations
from typing import Any
from core.network import ConnectivityError, Junction
from ..command import Command
from ..commands.junction_commands import CREATE_JUNCTION, REMOVE_JUNCTION
from ..errors import DomainError, ResourceError, ValidationError
from ..results import ApplicationResult
from ..transaction import Transaction

class JunctionService:
    """Own Junction command orchestration without owning presentation state."""
    COMMAND_TYPES = frozenset({CREATE_JUNCTION, REMOVE_JUNCTION})
    def supports(self, command: Command) -> bool:
        return command.command_type in self.COMMAND_TYPES
    def execute(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        if not isinstance(command, Command):
            raise TypeError("command must be a Command.")
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction.")
        if not transaction.active:
            raise ValidationError(code="JUNCTION_TRANSACTION_INACTIVE",
                message="Junction mutations require an active Application transaction.", details={})
        if not self.supports(command):
            raise ValidationError(code="UNSUPPORTED_JUNCTION_COMMAND",
                message=f"Unsupported Junction command: {command.command_type!r}.",
                details={"command_type": command.command_type})
        network = getattr(context, "network", None)
        if network is None or not all(callable(getattr(network, name, None)) for name in
            ("add_junction", "remove_junction", "get_junction", "contains_junction")):
            raise ResourceError(code="NETWORK_CONTEXT_MISSING",
                message="Application context does not expose a canonical Junction-capable Network.", details={})
        junction_id = command.payload.get("junction_id")
        if not isinstance(junction_id, str) or not junction_id.strip() or junction_id != junction_id.strip():
            raise ValidationError(code="INVALID_JUNCTION_ID",
                message="Junction ID must be a non-empty canonical string.", details={"junction_id": junction_id})
        if command.command_type == CREATE_JUNCTION:
            if network.contains_junction(junction_id):
                raise ValidationError(code="DUPLICATE_JUNCTION_ID",
                    message=f"Junction '{junction_id}' already exists on this Network.",
                    details={"junction_id": junction_id})
            junction = Junction(junction_id)
            try:
                network.add_junction(junction)
            except ConnectivityError as exc:
                raise DomainError(code="JUNCTION_CREATE_REJECTED", message=str(exc),
                                  details={"junction_id": junction_id}) from exc
            transaction.record_undo(lambda junction=junction, network=network: network.remove_junction(junction))
            return ApplicationResult.success_result(value=junction, message=f"Junction {junction_id} created.",
                metadata={"junction_id": junction_id, "junction_kind": "topology"})
        try:
            junction = network.get_junction(junction_id)
        except (KeyError, TypeError, ValueError) as exc:
            raise ResourceError(code="JUNCTION_NOT_FOUND",
                message=f"Junction '{junction_id}' is not registered on this Network.",
                details={"junction_id": junction_id}) from exc
        try:
            network.remove_junction(junction)
        except ConnectivityError as exc:
            raise DomainError(code="JUNCTION_REMOVE_REJECTED", message=str(exc),
                              details={"junction_id": junction_id, "connected": True}) from exc
        transaction.record_undo(lambda junction=junction, network=network: network.add_junction(junction))
        return ApplicationResult.success_result(value=None, message=f"Junction {junction_id} removed.",
            metadata={"junction_id": junction_id, "junction_kind": "topology"})

class JunctionCommandHandlers:
    """Bind Junction command types to the canonical Application service."""
    def __init__(self, service: JunctionService | None = None) -> None:
        self._service = service or JunctionService()
    def handlers(self) -> dict[str, Any]:
        return {CREATE_JUNCTION: self.execute, REMOVE_JUNCTION: self.execute}
    def execute(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._service.execute(command, context, transaction)

__all__ = ["JunctionCommandHandlers", "JunctionService"]
