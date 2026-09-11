"""Application handlers for canonical Logic Control/Ladder commands.

Author: Subhendu Mishra
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .command import Command
from .commands.control_commands import (
    ADD_CONTROL_COMPONENT, REMOVE_CONTROL_COMPONENT,
    CONNECT_CONTROL_SIGNALS, DISCONNECT_CONTROL_SIGNALS,
    ADD_LOGIC_DEPENDENCY, REMOVE_LOGIC_DEPENDENCY,
    ADD_LADDER_RUNG, REMOVE_LADDER_RUNG, MOVE_LADDER_ELEMENT,
)
from .results import ApplicationResult
from .transaction import Transaction

Handler = Callable[[Command, Any, Transaction], ApplicationResult[Any]]


class ControlCommandHandlers:
    """Handlers that keep Control mutation inside the Application boundary."""

    def __init__(self, service: Any) -> None:
        if service is None:
            raise ValueError("control service is required.")
        self._service = service

    def handlers(self) -> Mapping[str, Handler]:
        return {
            ADD_CONTROL_COMPONENT: self.add_component,
            REMOVE_CONTROL_COMPONENT: self.remove_component,
            CONNECT_CONTROL_SIGNALS: self.connect_signals,
            DISCONNECT_CONTROL_SIGNALS: self.disconnect_signals,
            ADD_LOGIC_DEPENDENCY: self.add_dependency,
            REMOVE_LOGIC_DEPENDENCY: self.remove_dependency,
            ADD_LADDER_RUNG: self.add_rung,
            REMOVE_LADDER_RUNG: self.remove_rung,
            MOVE_LADDER_ELEMENT: self.move_element,
        }

    def add_component(self, command, context, transaction):
        return self._service.add_component(transaction, **dict(command.payload))

    def remove_component(self, command, context, transaction):
        return self._service.remove_component(transaction, **dict(command.payload))

    def connect_signals(self, command, context, transaction):
        return self._service.connect_signals(transaction, **dict(command.payload))

    def disconnect_signals(self, command, context, transaction):
        return self._service.disconnect_signals(transaction, **dict(command.payload))

    def add_dependency(self, command, context, transaction):
        return self._service.add_dependency(transaction, **dict(command.payload))

    def remove_dependency(self, command, context, transaction):
        return self._service.remove_dependency(transaction, **dict(command.payload))

    def add_rung(self, command, context, transaction):
        return self._service.add_rung(transaction, **dict(command.payload))

    def remove_rung(self, command, context, transaction):
        return self._service.remove_rung(transaction, **dict(command.payload))

    def move_element(self, command, context, transaction):
        return self._service.move_element(transaction, **dict(command.payload))


__all__ = ["ControlCommandHandlers", "Handler"]
