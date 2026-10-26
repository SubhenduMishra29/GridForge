"""Typed immutable motor commands and CommandManager-compatible handlers.

Author: Subhendu Mishra

The Application CommandManager owns commit/rollback. Handlers must register
inverse operations on the supplied Transaction before mutating state.
"""
from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID, uuid4

from core.application.command import Command
from core.application.results import ApplicationResult
from core.application.transaction import Transaction


ADD_DRAFT_MOTOR_PLACEMENT = "motor.add_draft_placement"
COMMIT_MOTOR_TO_NETWORK = "motor.commit_to_network"


class AddDraftMotorPlacementCommand(Command):
    """Request placement of an uncommitted motor draft."""

    def __init__(
        self,
        motor_id: str,
        x: float,
        y: float,
        parameters: Mapping[str, Any] | None = None,
        *,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(motor_id, str) or not motor_id.strip():
            raise ValueError("motor_id must be a non-empty string")
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError("x must be numeric")
        if isinstance(y, bool) or not isinstance(y, (int, float)):
            raise TypeError("y must be numeric")
        payload = {
            "motor_id": motor_id,
            "x": float(x),
            "y": float(y),
            "parameters": dict(parameters or {}),
        }
        super().__init__(
            command_type=ADD_DRAFT_MOTOR_PLACEMENT,
            payload=payload,
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class CommitMotorToNetworkCommand(Command):
    """Request an atomic motor-to-wire topology operation."""

    def __init__(
        self,
        motor_id: str,
        wire_id: str,
        split_fraction: float = 0.5,
        *,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(motor_id, str) or not motor_id.strip():
            raise ValueError("motor_id must be a non-empty string")
        if not isinstance(wire_id, str) or not wire_id.strip():
            raise ValueError("wire_id must be a non-empty string")
        if isinstance(split_fraction, bool) or not isinstance(split_fraction, (int, float)):
            raise TypeError("split_fraction must be numeric")
        fraction = float(split_fraction)
        if not 0.0 < fraction < 1.0:
            raise ValueError("split_fraction must be inside (0, 1)")
        super().__init__(
            command_type=COMMIT_MOTOR_TO_NETWORK,
            payload={
                "motor_id": motor_id,
                "wire_id": wire_id,
                "split_fraction": fraction,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class MotorPlacementCommandHandler:
    """CommandManager handler adapter; never owns transaction lifecycle."""

    def __init__(self, motor_service: Any) -> None:
        if motor_service is None:
            raise ValueError("motor_service is required")
        self._motor_service = motor_service

    def __call__(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        if not isinstance(command, Command):
            raise TypeError("GridForge CommandManager handlers require Command")
        if not isinstance(transaction, Transaction):
            raise TypeError("GridForge CommandManager supplies a Transaction")

        if command.command_type == ADD_DRAFT_MOTOR_PLACEMENT:
            method = getattr(self._motor_service, "add_draft_motor", None)
        elif command.command_type == COMMIT_MOTOR_TO_NETWORK:
            method = getattr(self._motor_service, "commit_motor_to_network", None)
        else:
            raise ValueError(f"Unsupported motor command type: {command.command_type!r}")

        if not callable(method):
            raise RuntimeError(
                f"Motor service does not implement the handler for {command.command_type!r}"
            )

        # The service receives the CommandManager-owned transaction and MUST
        # register undo operations before every mutation. The manager commits
        # or rolls back; this handler must never do so itself.
        result = method(command=command, context=context, transaction=transaction)
        if not isinstance(result, ApplicationResult):
            raise TypeError("Motor service handlers must return ApplicationResult")
        return result


__all__ = [
    "ADD_DRAFT_MOTOR_PLACEMENT",
    "COMMIT_MOTOR_TO_NETWORK",
    "AddDraftMotorPlacementCommand",
    "CommitMotorToNetworkCommand",
    "MotorPlacementCommandHandler",
]
