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
    DELETE_SLD_SELECTION,
    SET_SLD_NODE_POSITION,
    SET_SLD_NODE_POSITIONS,
    SET_SLD_NODE_TRANSFORMS,
    SET_SLD_NODE_PRESENTATION,
    SET_SLD_CONNECTION_ROUTE,
    SET_SLD_NODE_PROPERTIES,
    CREATE_SLD_LAYER,
    UPDATE_SLD_LAYER,
    DELETE_SLD_LAYER,
    REORDER_SLD_LAYERS,
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
            SET_SLD_NODE_POSITIONS: self.set_node_positions,
            SET_SLD_NODE_TRANSFORMS: self.set_node_transforms,
            SET_SLD_CONNECTION_ROUTE: self.set_connection_route,
            SET_SLD_NODE_PROPERTIES: self.set_node_properties,
            SET_SLD_NODE_PRESENTATION: self.set_node_presentation,
            ADD_SLD_NODE: self.add_node,
            REMOVE_SLD_NODE: self.remove_node,
            DELETE_SLD_SELECTION: self.delete_selection,
            ADD_SLD_CONNECTION: self.add_connection,
            REMOVE_SLD_CONNECTION: self.remove_connection,
            CREATE_SLD_LAYER: self.mutate_layer_state,
            UPDATE_SLD_LAYER: self.mutate_layer_state,
            DELETE_SLD_LAYER: self.mutate_layer_state,
            REORDER_SLD_LAYERS: self.mutate_layer_state,
        }

    def _execute(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._service.execute(command, transaction, context=context)

    def set_node_position(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def set_node_positions(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def set_node_transforms(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def set_node_properties(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def set_connection_route(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def set_node_presentation(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def add_node(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def remove_node(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def delete_selection(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def add_connection(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def remove_connection(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)

    def mutate_layer_state(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._execute(command, context, transaction)


__all__ = ["SLDCommandHandlers"]
