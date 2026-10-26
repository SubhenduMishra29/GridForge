"""Typed immutable motor commands aligned with GridForge's electrical model.

Author: Subhendu Mishra

A GridForge Motor is a one-terminal injection/load model. It connects to a
Bus attachment; it is not a series element to be inserted by splitting a wire.
The canonical Application DraftNetwork/commit path remains the only route from
draft authoring to authoritative Core topology.
"""
from __future__ import annotations

from math import isfinite
import re
from typing import Any, Mapping
from uuid import UUID, uuid4

from core.application.command import Command
from core.application.results import ApplicationResult
from core.application.transaction import Transaction


ADD_DRAFT_MOTOR_PLACEMENT = "motor.add_draft_placement"
CONNECT_MOTOR_TO_BUS = "motor.connect_to_bus"


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
        if not isfinite(float(x)) or not isfinite(float(y)):
            raise ValueError("placement coordinates must be finite numbers")
        if parameters is not None and not isinstance(parameters, Mapping):
            raise TypeError("parameters must be a mapping when provided")
        payload = {
            "motor_id": motor_id.strip(),
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


class ConnectMotorToBusCommand(Command):
    """Request a draft graph connection from a motor terminal to a Bus attachment.

    This command does not mutate Core topology directly and does not split a
    SimpleWire. The composition service must translate it to the canonical
    DraftNetwork connection workflow and let the normal draft commit create
    Core equipment and connectivity.
    """

    def __init__(
        self,
        motor_id: str,
        bus_id: str,
        attachment_id: str,
        *,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        for name, value in (("motor_id", motor_id), ("bus_id", bus_id), ("attachment_id", attachment_id)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not re.fullmatch(r"attachment-(?:[0-8])", attachment_id.strip()):
            raise ValueError(
                "attachment_id must use canonical 'attachment-N' form "
                "with an index in the supported range 0..8"
            )
        super().__init__(
            command_type=CONNECT_MOTOR_TO_BUS,
            payload={
                "motor_id": motor_id.strip(),
                "bus_id": bus_id.strip(),
                "attachment_id": attachment_id.strip(),
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

        methods = {
            ADD_DRAFT_MOTOR_PLACEMENT: "add_draft_motor",
            CONNECT_MOTOR_TO_BUS: "connect_motor_to_bus",
        }
        method_name = methods.get(command.command_type)
        if method_name is None:
            raise ValueError(f"Unsupported motor command type: {command.command_type!r}")
        method = getattr(self._motor_service, method_name, None)
        if not callable(method):
            raise RuntimeError(
                f"Motor service does not implement the handler for {command.command_type!r}"
            )

        # Service must register inverses on the supplied Application transaction
        # before mutation. CommandManager owns commit and rollback.
        result = method(command=command, context=context, transaction=transaction)
        if not isinstance(result, ApplicationResult):
            raise TypeError("Motor service handlers must return ApplicationResult")
        return result


__all__ = [
    "ADD_DRAFT_MOTOR_PLACEMENT",
    "CONNECT_MOTOR_TO_BUS",
    "AddDraftMotorPlacementCommand",
    "ConnectMotorToBusCommand",
    "MotorPlacementCommandHandler",
]
