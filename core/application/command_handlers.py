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
    * resolve EndpointReference values;
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

Bus:

    EndpointReference.bus("BUS-001")
            |
            v
    context.network.buses
            |
            v
    Bus

Terminal:

    EndpointReference.terminal(
        equipment_type=...,
        equipment_id=...,
        terminal_role=...
    )
            |
            v
    canonical Network collection
            |
            v
    Branch / equipment
            |
            v
    equipment.terminals
            |
            v
    Terminal.role

The handler resolves references but delegates all mutation
to ModelService.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .command import Command
from .endpoint_reference import (
    EndpointReference,
    EndpointReferenceKind,
    EquipmentType,
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
    [Command, Any, Transaction],
    ApplicationResult[Any],
]


# ============================================================
# NETWORK COLLECTION RESOLUTION
# ============================================================

_EQUIPMENT_COLLECTIONS: Mapping[
    EquipmentType,
    str,
] = {
    EquipmentType.LINE: "lines",
    EquipmentType.TRANSFORMER: "transformers",
    EquipmentType.GENERATOR: "generators",
    EquipmentType.LOAD: "loads",
    EquipmentType.SHUNT: "shunts",
}


def _get_collection(
    context: Any,
    equipment_type: EquipmentType,
) -> Any:
    """
    Return the canonical Network collection for an
    EquipmentType.

    The mapping is kept in the Application boundary so the
    command handler can translate an Application reference
    into a canonical Core collection without importing
    concrete Core equipment classes.
    """

    if not isinstance(
        equipment_type,
        EquipmentType,
    ):
        raise ValidationError(
            code="INVALID_EQUIPMENT_TYPE",
            message=(
                "A valid EquipmentType is required."
            ),
            details={
                "equipment_type": str(
                    equipment_type
                ),
            },
        )

    collection_name = _EQUIPMENT_COLLECTIONS.get(
        equipment_type
    )

    if collection_name is None:
        raise ValidationError(
            code="UNSUPPORTED_EQUIPMENT_TYPE",
            message=(
                f"Equipment type "
                f"'{equipment_type.value}' is not "
                "supported by the Application resolver."
            ),
            details={
                "equipment_type": (
                    equipment_type.value
                ),
            },
        )

    network = getattr(
        context,
        "network",
        None,
    )

    if network is None:
        raise ResourceError(
            code="NETWORK_CONTEXT_MISSING",
            message=(
                "Application context does not expose "
                "the canonical Core Network."
            ),
            details={},
        )

    collection = getattr(
        network,
        collection_name,
        None,
    )

    if collection is None:
        raise ResourceError(
            code="NETWORK_COLLECTION_MISSING",
            message=(
                f"Canonical Network collection "
                f"'{collection_name}' is unavailable."
            ),
            details={
                "equipment_type": (
                    equipment_type.value
                ),
                "collection": collection_name,
            },
        )

    return collection


# ============================================================
# OBJECT LOOKUP
# ============================================================

def _find_by_id(
    collection: Any,
    object_id: str,
) -> Any | None:
    """
    Resolve an object from a canonical Core collection.

    No Application-side cache is maintained.
    """

    for item in collection:
        if getattr(item, "id", None) == object_id:
            return item

    return None


# ============================================================
# BUS RESOLUTION
# ============================================================

def _resolve_bus(
    context: Any,
    reference: EndpointReference,
) -> Any:
    """
    Resolve a Bus EndpointReference.
    """

    if (
        reference.kind
        is not EndpointReferenceKind.BUS
    ):
        raise ValidationError(
            code="INVALID_BUS_REFERENCE",
            message=(
                "A Bus EndpointReference is required."
            ),
            details={
                "kind": reference.kind.value,
            },
        )

    network = getattr(
        context,
        "network",
        None,
    )

    if network is None:
        raise ResourceError(
            code="NETWORK_CONTEXT_MISSING",
            message=(
                "Application context does not expose "
                "the canonical Core Network."
            ),
            details={},
        )

    buses = getattr(
        network,
        "buses",
        None,
    )

    if buses is None:
        raise ResourceError(
            code="BUS_COLLECTION_MISSING",
            message=(
                "Canonical Network does not expose "
                "its Bus collection."
            ),
            details={},
        )

    bus = _find_by_id(
        buses,
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


# ============================================================
# EQUIPMENT RESOLUTION
# ============================================================

def _resolve_equipment(
    context: Any,
    reference: EndpointReference,
) -> Any:
    """
    Resolve the owning equipment of a Terminal reference.
    """

    if (
        reference.kind
        is not EndpointReferenceKind.TERMINAL
    ):
        raise ValidationError(
            code="INVALID_TERMINAL_REFERENCE",
            message=(
                "A Terminal EndpointReference is required."
            ),
            details={
                "kind": reference.kind.value,
            },
        )

    if reference.equipment_type is None:
        raise ValidationError(
            code="MISSING_EQUIPMENT_TYPE",
            message=(
                "Terminal references require an "
                "EquipmentType."
            ),
            details={
                "equipment_id": reference.object_id,
            },
        )

    collection = _get_collection(
        context,
        reference.equipment_type,
    )

    equipment = _find_by_id(
        collection,
        reference.object_id,
    )

    if equipment is None:
        raise ResourceError(
            code="EQUIPMENT_NOT_FOUND",
            message=(
                f"{reference.equipment_type.value} "
                f"'{reference.object_id}' could not "
                "be resolved."
            ),
            details={
                "equipment_type": (
                    reference.equipment_type.value
                ),
                "equipment_id": reference.object_id,
            },
        )

    return equipment


# ============================================================
# TERMINAL RESOLUTION
# ============================================================

def _resolve_terminal(
    context: Any,
    reference: EndpointReference,
) -> Any:
    """
    Resolve a Terminal EndpointReference.

    The audited Core Branch contract exposes:

        equipment.terminals

    and each Terminal exposes:

        terminal.role

    Exact role matching is used.
    """

    equipment = _resolve_equipment(
        context,
        reference,
    )

    terminals = getattr(
        equipment,
        "terminals",
        None,
    )

    if terminals is None:
        raise ResourceError(
            code="EQUIPMENT_TERMINALS_UNAVAILABLE",
            message=(
                f"Equipment "
                f"'{reference.object_id}' does not "
                "expose the canonical terminals "
                "collection."
            ),
            details={
                "equipment_type": (
                    reference.equipment_type.value
                    if reference.equipment_type
                    else None
                ),
                "equipment_id": reference.object_id,
            },
        )

    requested_role = reference.terminal_role

    if not isinstance(
        requested_role,
        str,
    ) or not requested_role:
        raise ValidationError(
            code="INVALID_TERMINAL_ROLE",
            message=(
                "Terminal reference requires a "
                "non-empty terminal role."
            ),
            details={
                "equipment_id": reference.object_id,
            },
        )

    for terminal in terminals:
        if getattr(
            terminal,
            "role",
            None,
        ) == requested_role:
            return terminal

    raise ResourceError(
        code="TERMINAL_NOT_FOUND",
        message=(
            f"Terminal '{requested_role}' was not "
            f"found on "
            f"{reference.equipment_type.value} "
            f"'{reference.object_id}'."
        ),
        details={
            "equipment_type": (
                reference.equipment_type.value
            ),
            "equipment_id": reference.object_id,
            "terminal_role": requested_role,
        },
    )


# ============================================================
# ENDPOINT RESOLUTION
# ============================================================

def _resolve_endpoint(
    context: Any,
    reference: EndpointReference,
) -> Any:
    """
    Resolve an immutable Application EndpointReference into
    the corresponding canonical Core endpoint.
    """

    if not isinstance(
        reference,
        EndpointReference,
    ):
        raise ValidationError(
            code="INVALID_ENDPOINT_REFERENCE",
            message=(
                "Command endpoint must be an "
                "EndpointReference."
            ),
            details={
                "received_type": type(
                    reference
                ).__name__,
            },
        )

    if reference.kind is EndpointReferenceKind.BUS:
        return _resolve_bus(
            context,
            reference,
        )

    if (
        reference.kind
        is EndpointReferenceKind.TERMINAL
    ):
        return _resolve_terminal(
            context,
            reference,
        )

    raise ValidationError(
        code="UNSUPPORTED_ENDPOINT_KIND",
        message=(
            f"Unsupported endpoint kind "
            f"'{reference.kind.value}'."
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
    Canonical Application handlers for model commands.
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
        Return the canonical model command registry.
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
