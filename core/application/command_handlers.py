# ============================================================
# File: core/application/command_handlers.py
# GridForge V2 — Headless Application Command Handlers
# Author: Subhendu Mishra
# ============================================================
"""
GridForge V2
============

Module:
    core.application.command_handlers

Purpose
-------
Provides the Application command handlers that connect immutable
Command objects to Application services.

Architectural flow
------------------

    Command
       |
       v
    CommandManager
       |
       v
    Command Handler
       |
       v
    Application Service
       |
       v
    Core Network / Core Model

Handlers perform Application-level orchestration only.

They do NOT:

    * mutate Core objects directly;
    * manipulate Network collections directly;
    * manipulate topology;
    * invalidate Y-bus;
    * manipulate Qt;
    * create graphics objects;
    * render SLD objects.

ModelService remains the Application boundary responsible for
calling the public Core Network API.

Current handlers
----------------

    handle_create_bus
    handle_delete_bus

    handle_create_line
    handle_delete_line

Line endpoint resolution
------------------------
The current Terminal model does not expose a stable independent
Terminal ID. Therefore CreateLineCommand endpoint identifiers are
resolved against canonical Network Bus IDs.

The handler passes those canonical Bus objects to ModelService.

This is intentionally conservative.

A future terminal-addressing command can be introduced when the
Application architecture defines a stable Terminal identity
contract.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from typing import Any

from core.model import Bus

from .command import Command
from .commands.model_commands import (
    CREATE_BUS,
    CREATE_LINE,
    DELETE_BUS,
    DELETE_LINE,
)
from .context import ApplicationContext
from .errors import ExecutionError, ResourceError
from .results import ApplicationResult
from .services.model_service import ModelService


# =====================================================================
# INTERNAL HELPERS
# =====================================================================

def _service(context: ApplicationContext) -> ModelService:
    """
    Construct the Application model service for the supplied context.

    ModelService is intentionally stateless with respect to the
    canonical Network, so it is safe to construct at the command
    boundary.

    Parameters
    ----------
    context:
        Canonical Application dependency context.

    Returns
    -------
    ModelService
        Application model orchestration service.
    """

    if not isinstance(
        context,
        ApplicationContext,
    ):
        raise TypeError(
            "Command handler requires an ApplicationContext."
        )

    return ModelService(context)


def _payload_value(
    command: Command,
    key: str,
) -> Any:
    """
    Read a required value from a command payload.

    Command.__post_init__ guarantees that payload is a Mapping.
    This helper provides a consistent missing-field failure for
    malformed commands.
    """

    try:
        return command.payload[key]

    except KeyError as exc:
        raise ExecutionError(
            code="COMMAND_PAYLOAD_FIELD_MISSING",
            message=(
                f"Command '{command.command_type}' is missing "
                f"required payload field '{key}'."
            ),
            details={
                "command_type": command.command_type,
                "command_id": str(command.command_id),
                "field": key,
            },
            cause=exc,
        ) from exc


def _require_command_type(
    command: Command,
    expected: str,
) -> None:
    """
    Ensure that a handler received its expected command type.

    CommandManager normally guarantees this through registration,
    but explicit validation keeps the handler independently safe.
    """

    if command.command_type != expected:
        raise ExecutionError(
            code="COMMAND_TYPE_MISMATCH",
            message=(
                f"Handler expected command type '{expected}' "
                f"but received '{command.command_type}'."
            ),
            details={
                "expected": expected,
                "received": command.command_type,
                "command_id": str(command.command_id),
            },
        )


def _find_bus(
    context: ApplicationContext,
    bus_id: str,
) -> Bus:
    """
    Resolve a canonical Bus by its stable Network identifier.

    Network owns the canonical Bus collection.

    The handler performs lookup only; it does not mutate the
    collection.
    """

    if not isinstance(bus_id, str) or not bus_id.strip():
        raise ExecutionError(
            code="INVALID_ENDPOINT_ID",
            message=(
                "Line endpoint identifier must be a non-empty string."
            ),
            details={
                "field": "endpoint_id",
                "value": bus_id,
            },
        )

    normalized_id = bus_id.strip()

    for bus in context.network.buses:
        if getattr(bus, "id", None) == normalized_id:
            return bus

    raise ResourceError(
        code="LINE_ENDPOINT_BUS_NOT_FOUND",
        message=(
            f"Line endpoint Bus '{normalized_id}' "
            "is not registered on the Core Network."
        ),
        details={
            "bus_id": normalized_id,
            "operation": "resolve_line_endpoint",
        },
    )


# =====================================================================
# CREATE BUS
# =====================================================================

def handle_create_bus(
    command: Command,
    context: ApplicationContext,
) -> ApplicationResult:
    """
    Execute CreateBusCommand.

    Flow
    ----
        CreateBusCommand
              |
              v
        extract payload
              |
              v
        ModelService.create_bus()
              |
              v
        Network.add_bus()

    The handler itself never mutates Network.
    """

    _require_command_type(
        command,
        CREATE_BUS,
    )

    service = _service(context)

    return service.create_bus(
        bus_id=_payload_value(
            command,
            "bus_id",
        ),
        name=_payload_value(
            command,
            "name",
        ),
        bus_type=_payload_value(
            command,
            "bus_type",
        ),
        voltage=_payload_value(
            command,
            "voltage",
        ),
        angle=_payload_value(
            command,
            "angle",
        ),
        p_spec=_payload_value(
            command,
            "p_spec",
        ),
        q_spec=_payload_value(
            command,
            "q_spec",
        ),
        v_setpoint=_payload_value(
            command,
            "v_setpoint",
        ),
        q_min=_payload_value(
            command,
            "q_min",
        ),
        q_max=_payload_value(
            command,
            "q_max",
        ),
    )


# =====================================================================
# DELETE BUS
# =====================================================================

def handle_delete_bus(
    command: Command,
    context: ApplicationContext,
) -> ApplicationResult:
    """
    Execute DeleteBusCommand.

    Flow
    ----
        DeleteBusCommand
              |
              v
        ModelService.delete_bus()
              |
              v
        Network.remove_bus()

    The handler does not perform deletion itself.
    """

    _require_command_type(
        command,
        DELETE_BUS,
    )

    service = _service(context)

    return service.delete_bus(
        bus_id=_payload_value(
            command,
            "bus_id",
        ),
    )


# =====================================================================
# CREATE LINE
# =====================================================================

def handle_create_line(
    command: Command,
    context: ApplicationContext,
) -> ApplicationResult:
    """
    Execute CreateLineCommand.

    Endpoint resolution
    -------------------
    The command carries:

        endpoint_from_id
        endpoint_to_id

    These are resolved as canonical Bus IDs.

    The resulting Bus objects are passed to ModelService.

    Flow
    ----
        CreateLineCommand
              |
              +---- endpoint_from_id
              |          |
              |          v
              |       Bus lookup
              |
              +---- endpoint_to_id
                         |
                         v
                      Bus lookup
              |
              v
        ModelService.create_line()
              |
              v
        Network.add_line()

    No Network collection is directly modified here.
    """

    _require_command_type(
        command,
        CREATE_LINE,
    )

    endpoint_from_id = _payload_value(
        command,
        "endpoint_from_id",
    )

    endpoint_to_id = _payload_value(
        command,
        "endpoint_to_id",
    )

    endpoint_from = _find_bus(
        context,
        endpoint_from_id,
    )

    endpoint_to = _find_bus(
        context,
        endpoint_to_id,
    )

    service = _service(context)

    return service.create_line(
        line_id=_payload_value(
            command,
            "line_id",
        ),
        endpoint_from=endpoint_from,
        endpoint_to=endpoint_to,
        r=_payload_value(
            command,
            "r",
        ),
        x=_payload_value(
            command,
            "x",
        ),
        b=_payload_value(
            command,
            "b",
        ),
        name=_payload_value(
            command,
            "name",
        ),
        rate_mva=_payload_value(
            command,
            "rate_mva",
        ),
    )


# =====================================================================
# DELETE LINE
# =====================================================================

def handle_delete_line(
    command: Command,
    context: ApplicationContext,
) -> ApplicationResult:
    """
    Execute DeleteLineCommand.

    Flow
    ----
        DeleteLineCommand
              |
              v
        ModelService.delete_line()
              |
              v
        Network.remove_line()

    Terminal disconnection is deliberately NOT performed here.

    Network membership removal and derived-state invalidation are
    owned by Network.remove_line().
    """

    _require_command_type(
        command,
        DELETE_LINE,
    )

    service = _service(context)

    return service.delete_line(
        line_id=_payload_value(
            command,
            "line_id",
        ),
    )


# =====================================================================
# DEFAULT HANDLER REGISTRATION
# =====================================================================

def register_model_handlers(
    command_manager,
) -> None:
    """
    Register all canonical model command handlers.

    Parameters
    ----------
    command_manager:
        CommandManager instance.

    Registered command types
    ------------------------
        model.create_bus
        model.delete_bus
        model.create_line
        model.delete_line

    Notes
    -----
    CommandManager owns duplicate-registration protection.

    This function performs composition only.

    It does not execute any command.
    """

    if command_manager is None:
        raise ValueError(
            "command_manager must not be None."
        )

    command_manager.register(
        CREATE_BUS,
        handle_create_bus,
    )

    command_manager.register(
        DELETE_BUS,
        handle_delete_bus,
    )

    command_manager.register(
        CREATE_LINE,
        handle_create_line,
    )

    command_manager.register(
        DELETE_LINE,
        handle_delete_line,
    )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "handle_create_bus",
    "handle_delete_bus",
    "handle_create_line",
    "handle_delete_line",
    "register_model_handlers",
]
