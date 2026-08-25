# ============================================================
# File: core/application/command_handlers.py
# GridForge V2 — Application Command Handlers
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Application command handlers.

Handlers are the translation boundary between immutable
Application Commands and Application Services.

Responsibilities
----------------
Handlers:

    * read immutable Command payloads;
    * validate required payload fields;
    * resolve Core references from immutable IDs;
    * invoke Application Services;
    * return ApplicationResult.

Handlers do NOT:

    * mutate Core directly;
    * perform topology logic;
    * perform engineering calculations;
    * manipulate SLD/UI objects;
    * access Qt;
    * maintain application state.

The Application Service remains responsible for Core mutation.

Command flow
------------

    Command
       |
       v
    Handler
       |
       +---- resolve IDs
       |
       v
    ModelService
       |
       v
    Core Network / Model

The command payload contains identifiers.

The handler resolves those identifiers into canonical Core
objects before invoking ModelService.

Author: Subhendu Mishra
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .command import Command
from .errors import ResourceError, ValidationError
from .results import ApplicationResult
from .transaction import Transaction

from .commands.model_commands import (
    CREATE_BUS,
    DELETE_BUS,
    CREATE_LINE,
    DELETE_LINE,
    CREATE_TRANSFORMER,
    DELETE_TRANSFORMER,
)


# ============================================================
# TYPE DEFINITIONS
# ============================================================

Handler = Callable[
    [
        Command,
        Any,
        Transaction,
    ],
    ApplicationResult[Any],
]


# ============================================================
# PAYLOAD HELPERS
# ============================================================

def _require_payload(
    command: Command,
    key: str,
) -> Any:
    """
    Return a required command payload value.
    """

    if key not in command.payload:
        raise ValidationError(
            code="MISSING_COMMAND_PAYLOAD",
            message=(
                f"Command '{command.command_type}' "
                f"is missing required payload field "
                f"'{key}'."
            ),
            details={
                "command_type": command.command_type,
                "command_id": str(
                    command.command_id
                ),
                "field": key,
            },
        )

    value = command.payload[key]

    if value is None:
        raise ValidationError(
            code="NULL_COMMAND_PAYLOAD",
            message=(
                f"Command '{command.command_type}' "
                f"contains null value for required "
                f"payload field '{key}'."
            ),
            details={
                "command_type": command.command_type,
                "command_id": str(
                    command.command_id
                ),
                "field": key,
            },
        )

    return value


# ============================================================
# CORE OBJECT RESOLUTION
# ============================================================

def _find_by_id(
    collection: Any,
    object_id: str,
) -> Any | None:
    """
    Resolve a canonical Core object by its public id.
    """

    for item in collection:
        if getattr(item, "id", None) == object_id:
            return item

    return None


def _resolve_endpoint(
    context: Any,
    endpoint_id: str,
) -> Any:
    """
    Resolve an endpoint identifier against canonical Core state.

    Endpoint resolution belongs to the Application boundary.

    The command carries only the identifier.
    The Core object is resolved immediately before service
    invocation and is never stored in the command.

    Current GridForge Core endpoint ownership is Network-centric:
    endpoints are resolved through the canonical Network model.
    """

    if not isinstance(
        endpoint_id,
        str,
    ) or not endpoint_id.strip():
        raise ValidationError(
            code="INVALID_ENDPOINT_ID",
            message=(
                "Endpoint id must be a non-empty string."
            ),
            details={
                "field": "endpoint_id",
            },
        )

    endpoint_id = endpoint_id.strip()
    network = context.network

    # --------------------------------------------------------
    # Bus endpoints
    # --------------------------------------------------------

    bus = _find_by_id(
        network.buses,
        endpoint_id,
    )

    if bus is not None:
        return bus

    # --------------------------------------------------------
    # Existing network elements
    #
    # These checks intentionally use public collections.
    # No Network private indexes are accessed.
    # --------------------------------------------------------

    for collection_name in (
        "lines",
        "transformers",
    ):
        collection = getattr(
            network,
            collection_name,
            (),
        )

        element = _find_by_id(
            collection,
            endpoint_id,
        )

        if element is not None:
            return element

    raise ResourceError(
        code="ENDPOINT_NOT_FOUND",
        message=(
            f"Endpoint '{endpoint_id}' could not be "
            "resolved in the canonical Core Network."
        ),
        details={
            "endpoint_id": endpoint_id,
            "operation": "resolve_endpoint",
        },
    )


# ============================================================
# MODEL COMMAND HANDLERS
# ============================================================

class ModelCommandHandlers:
    """
    Application handlers for canonical model commands.

    The handler set exactly mirrors model_commands.py.

    Supported commands
    ------------------

        model.create_bus
        model.delete_bus

        model.create_line
        model.delete_line

        model.create_transformer
        model.delete_transformer
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
    # REGISTRATION
    # ========================================================

    def handlers(
        self,
    ) -> Mapping[str, Handler]:
        """
        Return the canonical command-handler registry.
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
        Handle model.create_bus.
        """

        return self._model_service.create_bus(
            bus_id=_require_payload(
                command,
                "bus_id",
            ),
            name=_require_payload(
                command,
                "name",
            ),
            bus_type=_require_payload(
                command,
                "bus_type",
            ),
            voltage=_require_payload(
                command,
                "voltage",
            ),
            angle=_require_payload(
                command,
                "angle",
            ),
            p_spec=_require_payload(
                command,
                "p_spec",
            ),
            q_spec=_require_payload(
                command,
                "q_spec",
            ),
            v_setpoint=command.payload.get(
                "v_setpoint"
            ),
            q_min=_require_payload(
                command,
                "q_min",
            ),
            q_max=_require_payload(
                command,
                "q_max",
            ),
            transaction=transaction,
        )

    def delete_bus(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Handle model.delete_bus.
        """

        return self._model_service.delete_bus(
            bus_id=_require_payload(
                command,
                "bus_id",
            ),
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
        Handle model.create_line.

        Converts:

            endpoint_from_id
            endpoint_to_id

        into canonical Core endpoint objects before invoking
        ModelService.
        """

        endpoint_from_id = _require_payload(
            command,
            "endpoint_from_id",
        )

        endpoint_to_id = _require_payload(
            command,
            "endpoint_to_id",
        )

        endpoint_from = _resolve_endpoint(
            context,
            endpoint_from_id,
        )

        endpoint_to = _resolve_endpoint(
            context,
            endpoint_to_id,
        )

        return self._model_service.create_line(
            line_id=_require_payload(
                command,
                "line_id",
            ),
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=_require_payload(
                command,
                "r",
            ),
            x=_require_payload(
                command,
                "x",
            ),
            b=_require_payload(
                command,
                "b",
            ),
            name=_require_payload(
                command,
                "name",
            ),
            rate_mva=_require_payload(
                command,
                "rate_mva",
            ),
            transaction=transaction,
        )

    def delete_line(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Handle model.delete_line.
        """

        return self._model_service.delete_line(
            line_id=_require_payload(
                command,
                "line_id",
            ),
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
        Handle model.create_transformer.

        Endpoint IDs are resolved against canonical Core state.
        """

        endpoint_from_id = _require_payload(
            command,
            "endpoint_from_id",
        )

        endpoint_to_id = _require_payload(
            command,
            "endpoint_to_id",
        )

        endpoint_from = _resolve_endpoint(
            context,
            endpoint_from_id,
        )

        endpoint_to = _resolve_endpoint(
            context,
            endpoint_to_id,
        )

        return self._model_service.create_transformer(
            transformer_id=_require_payload(
                command,
                "transformer_id",
            ),
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=_require_payload(
                command,
                "r",
            ),
            x=_require_payload(
                command,
                "x",
            ),
            tap=_require_payload(
                command,
                "tap",
            ),
            shift=_require_payload(
                command,
                "shift",
            ),
            name=_require_payload(
                command,
                "name",
            ),
            rate_mva=_require_payload(
                command,
                "rate_mva",
            ),
            transaction=transaction,
        )

    def delete_transformer(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Handle model.delete_transformer.
        """

        return self._model_service.delete_transformer(
            transformer_id=_require_payload(
                command,
                "transformer_id",
            ),
            transaction=transaction,
        )


# ============================================================
# FUNCTIONAL REGISTRATION API
# ============================================================

def build_model_command_handlers(
    model_service: Any,
) -> Mapping[str, Handler]:
    """
    Build the canonical model command-handler registry.
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
