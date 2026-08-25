# ============================================================
# File: core/application/command_handlers.py
# GridForge V2 — Application Command Handlers
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Application Command Handlers.

Handlers are the Application translation boundary between
immutable Commands and Application Services.

Responsibilities
----------------
Handlers:

    * inspect immutable command payloads;
    * resolve Application references against canonical Core state;
    * invoke Application Services;
    * return ApplicationResult objects.

Handlers do NOT:

    * mutate Core directly;
    * perform topology mutation;
    * perform engineering calculations;
    * manipulate SLD/UI objects;
    * access Qt;
    * maintain independent application state.

Endpoint resolution
-------------------
EndpointReference supports:

    BUS
        object_id = Bus.id

    TERMINAL
        object_id = owning equipment.id
        terminal_role = terminal role

The handler resolves these references against canonical Core
objects before invoking ModelService.

Author:
    Subhendu Mishra
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .command import Command
from .endpoint_reference import (
    EndpointReference,
    EndpointReferenceKind,
)
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
# TYPES
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
# GENERIC COLLECTION RESOLUTION
# ============================================================

def _find_by_id(
    collection: Any,
    object_id: str,
) -> Any | None:
    """
    Find an object by its canonical public id.

    The handler deliberately uses public collection contents
    rather than private Core indexes.
    """

    for item in collection:
        if getattr(item, "id", None) == object_id:
            return item

    return None


# ============================================================
# EQUIPMENT RESOLUTION
# ============================================================

def _resolve_equipment(
    context: Any,
    equipment_id: str,
) -> Any:
    """
    Resolve a canonical Core equipment object.

    Equipment collections are discovered from the canonical
    Network object exposed by ApplicationContext.

    No UI or Application-side object registry is consulted.
    """

    network = context.network

    if not isinstance(
        equipment_id,
        str,
    ) or not equipment_id.strip():
        raise ValidationError(
            code="INVALID_EQUIPMENT_ID",
            message=(
                "Equipment id must be a non-empty string."
            ),
            details={
                "equipment_id": equipment_id,
            },
        )

    equipment_id = equipment_id.strip()

    # --------------------------------------------------------
    # Known canonical network collections
    # --------------------------------------------------------

    collection_names = (
        "lines",
        "transformers",
        "generators",
        "loads",
        "motors",
        "breakers",
        "switches",
        "shunts",
        "capacitors",
        "reactors",
    )

    for collection_name in collection_names:
        collection = getattr(
            network,
            collection_name,
            None,
        )

        if collection is None:
            continue

        equipment = _find_by_id(
            collection,
            equipment_id,
        )

        if equipment is not None:
            return equipment

    raise ResourceError(
        code="EQUIPMENT_NOT_FOUND",
        message=(
            f"Equipment '{equipment_id}' could not be "
            "resolved in the canonical Core Network."
        ),
        details={
            "equipment_id": equipment_id,
        },
    )


# ============================================================
# TERMINAL RESOLUTION
# ============================================================

def _resolve_terminal(
    context: Any,
    reference: EndpointReference,
) -> Any:
    """
    Resolve an EndpointReference of kind TERMINAL.

    Terminal identity is:

        owning equipment id
        +
        terminal role

    The returned object is the actual Core Terminal instance.

    This function does not create terminals.
    """

    if not reference.is_terminal:
        raise ValidationError(
            code="INVALID_TERMINAL_REFERENCE",
            message=(
                "A terminal endpoint reference is required."
            ),
            details={
                "kind": reference.kind.value,
            },
        )

    equipment = _resolve_equipment(
        context,
        reference.object_id,
    )

    terminal_role = reference.terminal_role

    if terminal_role is None:
        raise ValidationError(
            code="MISSING_TERMINAL_ROLE",
            message=(
                "Terminal endpoint reference requires "
                "a terminal role."
            ),
            details={
                "equipment_id": reference.object_id,
            },
        )

    # --------------------------------------------------------
    # Preferred public terminal access
    # --------------------------------------------------------

    terminals = getattr(
        equipment,
        "terminals",
        None,
    )

    if terminals is not None:
        terminal = _find_terminal_by_role(
            terminals,
            terminal_role,
        )

        if terminal is not None:
            return terminal

    # --------------------------------------------------------
    # Branch-style equipment
    #
    # Core Branch explicitly exposes:
    #
    #     from_terminal
    #     to_terminal
    #
    # Handle those canonical attributes directly.
    # --------------------------------------------------------

    for attribute_name in (
        "from_terminal",
        "to_terminal",
    ):
        terminal = getattr(
            equipment,
            attribute_name,
            None,
        )

        if terminal is None:
            continue

        role = getattr(
            terminal,
            "role",
            None,
        )

        if role == terminal_role:
            return terminal

    # --------------------------------------------------------
    # Generic terminal attributes
    #
    # This supports equipment such as transformers that expose
    # named terminals without requiring the handler to know
    # every equipment-specific topology implementation.
    # --------------------------------------------------------

    for attribute_name in (
        "hv_terminal",
        "lv_terminal",
        "primary_terminal",
        "secondary_terminal",
    ):
        terminal = getattr(
            equipment,
            attribute_name,
            None,
        )

        if terminal is None:
            continue

        role = getattr(
            terminal,
            "role",
            None,
        )

        if role == terminal_role:
            return terminal

    raise ResourceError(
        code="TERMINAL_NOT_FOUND",
        message=(
            f"Terminal '{terminal_role}' was not found "
            f"on equipment '{reference.object_id}'."
        ),
        details={
            "equipment_id": reference.object_id,
            "terminal_role": terminal_role,
        },
    )


def _find_terminal_by_role(
    terminals: Any,
    terminal_role: str,
) -> Any | None:
    """
    Find a terminal by its role from a public terminal
    collection or mapping.
    """

    if isinstance(terminals, Mapping):
        terminal = terminals.get(
            terminal_role
        )

        if terminal is not None:
            return terminal

    for terminal in terminals:
        if getattr(
            terminal,
            "role",
            None,
        ) == terminal_role:
            return terminal

    return None


# ============================================================
# ENDPOINT RESOLUTION
# ============================================================

def _resolve_endpoint(
    context: Any,
    reference: EndpointReference,
) -> Any:
    """
    Resolve an Application EndpointReference to a canonical
    Core endpoint object.
    """

    if not isinstance(
        reference,
        EndpointReference,
    ):
        raise ValidationError(
            code="INVALID_ENDPOINT_REFERENCE",
            message=(
                "Endpoint must be represented by "
                "EndpointReference."
            ),
            details={
                "received_type": type(reference).__name__,
            },
        )

    if (
        reference.kind
        is EndpointReferenceKind.BUS
    ):
        bus = _find_by_id(
            context.network.buses,
            reference.object_id,
        )

        if bus is None:
            raise ResourceError(
                code="BUS_NOT_FOUND",
                message=(
                    f"Bus '{reference.object_id}' "
                    "could not be resolved."
                ),
                details={
                    "bus_id": reference.object_id,
                },
            )

        return bus

    if (
        reference.kind
        is EndpointReferenceKind.TERMINAL
    ):
        return _resolve_terminal(
            context,
            reference,
        )

    raise ValidationError(
        code="UNSUPPORTED_ENDPOINT_REFERENCE",
        message=(
            f"Unsupported endpoint reference kind "
            f"'{reference.kind}'."
        ),
        details={
            "kind": reference.kind.value,
        },
    )


# ============================================================
# MODEL COMMAND HANDLERS
# ============================================================

class ModelCommandHandlers:
    """
    Handler registry for canonical model commands.
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
        Return the complete canonical model-handler registry.
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

        payload = command.payload

        endpoint_from = _resolve_endpoint(
            context,
            payload["endpoint_from"],
        )

        endpoint_to = _resolve_endpoint(
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

        payload = command.payload

        endpoint_from = _resolve_endpoint(
            context,
            payload["endpoint_from"],
        )

        endpoint_to = _resolve_endpoint(
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

        return self._model_service.delete_transformer(
            transformer_id=command.payload[
                "transformer_id"
            ],
            transaction=transaction,
        )


# ============================================================
# REGISTRATION FACTORY
# ============================================================

def build_model_command_handlers(
    model_service: Any,
) -> Mapping[str, Handler]:
    """
    Construct the canonical model command registry.
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
