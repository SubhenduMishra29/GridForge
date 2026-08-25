# ============================================================
# File: core/application/command_handlers.py
# GridForge V2 — Application Command Handlers
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Command Handlers
============================================

Application handlers translate immutable Application Commands
into calls to Application Services.

Handlers:

    * validate command-level references;
    * delegate EndpointReference resolution;
    * invoke Application Services;
    * return ApplicationResult.

Handlers do NOT:

    * mutate Core directly;
    * manipulate SLD state;
    * access Qt/UI;
    * perform engineering calculations;
    * maintain electrical state;
    * implement topology mutation.

Endpoint resolution
-------------------

EndpointReference resolution is delegated to the dedicated
Application EndpointResolver.

    EndpointReference
            |
            v
    EndpointResolver
            |
            +----------------------+
            |                      |
            v                      v
    canonical Bus          canonical Terminal
            |                      |
            +----------+-----------+
                       |
                       v
                  ModelService

Canonical lookup boundary
-------------------------

EndpointResolver performs canonical Core lookup through:

    Network.get_by_id()

Neither this handler nor the resolver accesses NetworkRegistry
internals or individual Network collections directly.

The handler remains an orchestration boundary and delegates all
Core mutation to ModelService.

Load commands
-------------

Load creation is intentionally independent of topology.

CreateLoadCommand carries:

    load_id
    p
    q
    name
    in_service

The handler therefore does not resolve a Bus or Terminal for
Load creation.

Load connectivity is handled by the appropriate separate
Application topology workflow.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .command import Command
from .endpoint_resolver import EndpointResolver
from .results import ApplicationResult
from .transaction import Transaction

from .commands.model_commands import (
    CREATE_BUS,
    DELETE_BUS,
    CREATE_LINE,
    DELETE_LINE,
    CREATE_TRANSFORMER,
    DELETE_TRANSFORMER,
    CREATE_LOAD,
    DELETE_LOAD,
)


# ============================================================
# TYPES
# ============================================================

Handler = Callable[
    [Command, Any, Transaction],
    ApplicationResult[Any],
]


# ============================================================
# MODEL COMMAND HANDLERS
# ============================================================

class ModelCommandHandlers:
    """
    Canonical Application handlers for model commands.

    Handlers translate Commands into ModelService operations.

    Core mutation is never performed directly here.

    EndpointReference values are resolved exclusively through
    EndpointResolver.
    """

    def __init__(
        self,
        model_service: Any,
    ) -> None:

        if model_service is None:
            raise ValueError(
                "model_service is required."
            )

        self._model_service = model_service

    # ========================================================
    # REGISTRY
    # ========================================================

    def handlers(
        self,
    ) -> Mapping[str, Handler]:
        """
        Return the canonical model command handler registry.
        """

        return {
            CREATE_BUS: self.create_bus,
            DELETE_BUS: self.delete_bus,

            CREATE_LINE: self.create_line,
            DELETE_LINE: self.delete_line,

            CREATE_TRANSFORMER: (
                self.create_transformer
            ),
            DELETE_TRANSFORMER: (
                self.delete_transformer
            ),

            CREATE_LOAD: self.create_load,
            DELETE_LOAD: self.delete_load,
        }

    # ========================================================
    # BUS
    # ========================================================

    def create_bus(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Create a Bus through ModelService.

        No Core mutation is performed directly by the handler.
        """

        payload = command.payload

        return self._model_service.create_bus(
            bus_id=payload["bus_id"],
            name=payload["name"],
            bus_type=payload["bus_type"],
            voltage=payload["voltage"],
            angle=payload["angle"],
            p_spec=payload["p_spec"],
            q_spec=payload["q_spec"],
            v_setpoint=payload["v_setpoint"],
            q_min=payload["q_min"],
            q_max=payload["q_max"],
            transaction=transaction,
        )

    def delete_bus(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Delete a Bus through ModelService.
        """

        return self._model_service.delete_bus(
            bus_id=command.payload["bus_id"],
            transaction=transaction,
        )

    # ========================================================
    # LINE
    # ========================================================

    def create_line(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Create a Line.

        EndpointReference values are resolved to canonical
        Bus / Terminal objects before ModelService is invoked.
        """

        payload = command.payload

        endpoint_from = EndpointResolver.resolve(
            context,
            payload["endpoint_from"],
        )

        endpoint_to = EndpointResolver.resolve(
            context,
            payload["endpoint_to"],
        )

        return self._model_service.create_line(
            line_id=payload["line_id"],
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=payload["r"],
            x=payload["x"],
            b=payload["b"],
            name=payload["name"],
            rate_mva=payload["rate_mva"],
            transaction=transaction,
        )

    def delete_line(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Delete a Line through ModelService.
        """

        return self._model_service.delete_line(
            line_id=command.payload["line_id"],
            transaction=transaction,
        )

    # ========================================================
    # TRANSFORMER
    # ========================================================

    def create_transformer(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Create a Transformer.

        EndpointReference values are resolved to canonical
        Bus / Terminal objects before ModelService is invoked.
        """

        payload = command.payload

        endpoint_from = EndpointResolver.resolve(
            context,
            payload["endpoint_from"],
        )

        endpoint_to = EndpointResolver.resolve(
            context,
            payload["endpoint_to"],
        )

        return self._model_service.create_transformer(
            transformer_id=payload["transformer_id"],
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=payload["r"],
            x=payload["x"],
            tap=payload["tap"],
            shift=payload["shift"],
            name=payload["name"],
            rate_mva=payload["rate_mva"],
            transaction=transaction,
        )

    def delete_transformer(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Delete a Transformer through ModelService.
        """

        return self._model_service.delete_transformer(
            transformer_id=command.payload[
                "transformer_id"
            ],
            transaction=transaction,
        )

    # ========================================================
    # LOAD
    # ========================================================

    def create_load(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Create a Load through ModelService.

        Load creation does not resolve an endpoint.

        The resulting Load is initially disconnected and its
        terminal/topology is handled separately by the
        Application topology workflow.
        """

        payload = command.payload

        return self._model_service.create_load(
            load_id=payload["load_id"],
            p=payload["p"],
            q=payload["q"],
            name=payload["name"],
            in_service=payload["in_service"],
            transaction=transaction,
        )

    def delete_load(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Delete a Load through ModelService.
        """

        return self._model_service.delete_load(
            load_id=command.payload["load_id"],
            transaction=transaction,
        )


# ============================================================
# FACTORY
# ============================================================

def build_model_command_handlers(
    model_service: Any,
) -> Mapping[str, Handler]:
    """
    Build the canonical model command handler registry.
    """

    return ModelCommandHandlers(
        model_service
    ).handlers()


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ModelCommandHandlers",
    "build_model_command_handlers",
]
