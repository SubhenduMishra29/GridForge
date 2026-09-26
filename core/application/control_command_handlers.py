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
    ADD_CONTROL_ACTION_BINDING, REMOVE_CONTROL_ACTION_BINDING, ADD_CONTROL_INTERLOCK, REMOVE_CONTROL_INTERLOCK,
    ADD_DYNAMIC_CONTROL_ASSOCIATION, REMOVE_DYNAMIC_CONTROL_ASSOCIATION,
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
            ADD_CONTROL_ACTION_BINDING: self.add_action_binding, REMOVE_CONTROL_ACTION_BINDING: self.remove_action_binding,
            ADD_CONTROL_INTERLOCK: self.add_interlock, REMOVE_CONTROL_INTERLOCK: self.remove_interlock,
            ADD_DYNAMIC_CONTROL_ASSOCIATION: self.add_dynamic_association, REMOVE_DYNAMIC_CONTROL_ASSOCIATION: self.remove_dynamic_association,
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

    def add_action_binding(self, command, context, transaction): return self._service.add_action_binding(transaction, **dict(command.payload))
    def remove_action_binding(self, command, context, transaction): return self._service.remove_action_binding(transaction, **dict(command.payload))
    def add_interlock(self, command, context, transaction): return self._service.add_interlock(transaction, **dict(command.payload))
    def remove_interlock(self, command, context, transaction): return self._service.remove_interlock(transaction, **dict(command.payload))
    def add_dynamic_association(self, command, context, transaction): return self._service.add_dynamic_association(transaction, **dict(command.payload))
    def remove_dynamic_association(self, command, context, transaction): return self._service.remove_dynamic_association(transaction, **dict(command.payload))


__all__ = ["ControlCommandHandlers", "Handler"]
