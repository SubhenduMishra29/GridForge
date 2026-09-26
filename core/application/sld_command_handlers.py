# ============================================================
# File: core/application/sld_command_handlers.py
# GridForge V2 — Application SLD command handlers
# ============================================================

"""Command handlers that bind SLD presentation commands to SLDService."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .command import Command
from .commands.sld_commands import (
    ADD_SLD_CONNECTION,
    ADD_SLD_NODE,
    REMOVE_SLD_CONNECTION,
    REMOVE_SLD_NODE,
    SET_SLD_NODE_POSITION,
    SET_SLD_NODE_PRESENTATION,
)
from .results import ApplicationResult
from .services.sld_service import SLDService
from .transaction import Transaction


class SLDCommandHandlers:
    """Application handlers for the canonical SLD command family."""

    def __init__(self, service: SLDService) -> None:
        if not isinstance(service, SLDService):
            raise TypeError("service must be an SLDService")
        self._service = service

    def handlers(self) -> Mapping[str, Any]:
        return {
            SET_SLD_NODE_POSITION: self.set_node_position,
            SET_SLD_NODE_PRESENTATION: self.set_node_presentation,
            ADD_SLD_NODE: self.add_node,
            REMOVE_SLD_NODE: self.remove_node,
            ADD_SLD_CONNECTION: self.add_connection,
            REMOVE_SLD_CONNECTION: self.remove_connection,
        }

    def _execute(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._service.execute(command, transaction, context=context)

    def set_node_position(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def set_node_presentation(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def add_node(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def remove_node(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def add_connection(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def remove_connection(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)


__all__ = ["SLDCommandHandlers"]
