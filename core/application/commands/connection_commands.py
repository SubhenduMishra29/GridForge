# ============================================================
# File: core/application/commands/connection_commands.py
# GridForge V2 — Canonical electrical connection commands
# Author: Subhendu Mishra
# ============================================================

"""Immutable Application commands for electrical terminal connectivity."""

from __future__ import annotations

from uuid import UUID, uuid4

from ..command import Command
from core.model import EndpointReference


CONNECT_TERMINAL = "model.connect_terminal"
DISCONNECT_TERMINAL = "model.disconnect_terminal"
RECONNECT_TERMINAL = "model.reconnect_terminal"


class ConnectTerminalCommand(Command):
    """Attach one canonical Core terminal to an electrical endpoint."""

    def __init__(self, *, terminal: EndpointReference, target: EndpointReference, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if not isinstance(terminal, EndpointReference) or not terminal.is_terminal:
            raise TypeError("terminal must be a terminal EndpointReference.")
        if not isinstance(target, EndpointReference):
            raise TypeError("target must be an EndpointReference.")
        super().__init__(command_type=CONNECT_TERMINAL, payload={"terminal": terminal, "target": target}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class ReconnectTerminalCommand(Command):
    """Replace one terminal's existing endpoint with a new endpoint."""

    def __init__(self, *, terminal: EndpointReference, target: EndpointReference, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if not isinstance(terminal, EndpointReference) or not terminal.is_terminal:
            raise TypeError("terminal must be a terminal EndpointReference.")
        if not isinstance(target, EndpointReference):
            raise TypeError("target must be an EndpointReference.")
        super().__init__(command_type=RECONNECT_TERMINAL, payload={"terminal": terminal, "target": target}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class DisconnectTerminalCommand(Command):
    """Detach one canonical Core terminal."""

    def __init__(self, *, terminal: EndpointReference, expected_target: EndpointReference | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if not isinstance(terminal, EndpointReference) or not terminal.is_terminal:
            raise TypeError("terminal must be a terminal EndpointReference.")
        if expected_target is not None and not isinstance(expected_target, EndpointReference):
            raise TypeError("expected_target must be an EndpointReference or None.")
        super().__init__(command_type=DISCONNECT_TERMINAL, payload={"terminal": terminal, "expected_target": expected_target}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


__all__ = ["CONNECT_TERMINAL", "DISCONNECT_TERMINAL", "RECONNECT_TERMINAL", "ConnectTerminalCommand", "DisconnectTerminalCommand", "ReconnectTerminalCommand"]
