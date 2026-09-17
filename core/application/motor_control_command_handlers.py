"""Application handlers for semantic Motor operational commands.

Author: Subhendu Mishra
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .command import Command
from .commands.motor_commands import (
    PUT_MOTOR_IN_SERVICE,
    START_MOTOR,
    STOP_MOTOR,
    TAKE_MOTOR_OUT_OF_SERVICE,
)
from .results import ApplicationResult
from .transaction import Transaction

Handler = Callable[[Command, Any, Transaction], ApplicationResult]


class MotorControlCommandHandlers:
    """Translate semantic motor intents into the existing MotorModelService."""

    def __init__(self, motor_service: Any) -> None:
        if motor_service is None:
            raise ValueError("motor_service is required.")
        self._motor_service = motor_service

    def handlers(self) -> Mapping[str, Handler]:
        return {
            START_MOTOR: self.start,
            STOP_MOTOR: self.stop,
            PUT_MOTOR_IN_SERVICE: self.put_in_service,
            TAKE_MOTOR_OUT_OF_SERVICE: self.take_out_of_service,
        }

    def start(self, command, context, transaction):
        return self._motor_service.update_motor(
            transaction=transaction,
            motor_id=command.payload["motor_id"],
            running=True,
        )

    def stop(self, command, context, transaction):
        return self._motor_service.update_motor(
            transaction=transaction,
            motor_id=command.payload["motor_id"],
            running=False,
        )

    def put_in_service(self, command, context, transaction):
        return self._motor_service.update_motor(
            transaction=transaction,
            motor_id=command.payload["motor_id"],
            in_service=True,
        )

    def take_out_of_service(self, command, context, transaction):
        return self._motor_service.update_motor(
            transaction=transaction,
            motor_id=command.payload["motor_id"],
            in_service=False,
        )


__all__ = ["MotorControlCommandHandlers", "Handler"]
