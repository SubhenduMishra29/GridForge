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
    context.network.get_by_id("bus", "BUS-001")
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
    context.network.get_by_id(...)
            |
            v
    canonical equipment
            |
            v
    equipment.terminals
            |
            v
    Terminal.role

The handler resolves references but delegates all mutation
to ModelService.

Canonical lookup boundary
-------------------------

The handler MUST NOT inspect:

    network.buses
    network.lines
    network.transformers
    network.generators
    network.loads
    network.shunts

for ID resolution.

All canonical equipment lookup goes through:

    Network.get_by_id()

Network delegates the lookup to NetworkRegistry.

This prevents Application-layer duplication of Core registry
knowledge.
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
    [Command, Any, Transaction],
    ApplicationResult[Any],
]


# ============================================================
# NETWORK ACCESS
# ============================================================

def _get_network(
    context: Any,
) -> Any:
    """
    Return the canonical Core Network from the Application
    context.

    The handler does not construct or cache a Network.
    """

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

    return network


# ============================================================
# CANONICAL EQUIPMENT LOOKUP
# ============================================================

def _resolve_equipment_by_id(
    context: Any,
    *,
    equipment_type: Any,
    object_id: str,
) -> Any:
    """
    Resolve canonical equipment through the Network façade.

    The Application layer intentionally does not know how
    NetworkRegistry stores equipment.
    """

    if equipment_type is None:
        raise ValidationError(
            code="MISSING_EQUIPMENT_TYPE",
            message=(
                "Terminal references require an "
                "EquipmentType."
            ),
            details={
                "equipment_id": object_id,
            },
        )

    value = getattr(
        equipment_type,
        "value",
        None,
    )

    if not isinstance(
        value,
        str,
    ) or not value:
        raise ValidationError(
            code="INVALID_EQUIPMENT_TYPE",
            message=(
                "Terminal reference contains an "
                "invalid EquipmentType."
            ),
            details={
                "equipment_type": str(
                    equipment_type
                ),
                "equipment_id": object_id,
            },
        )

    network = _get_network(
        context
    )

    try:
        return network.get_by_id(
            value,
            object_id,
        )

    except KeyError as exc:
        raise ResourceError(
            code="EQUIPMENT_NOT_FOUND",
            message=(
                f"{value} '{object_id}' could not "
                "be resolved."
            ),
            details={
                "equipment_type": value,
                "equipment_id": object_id,
            },
        ) from exc


# ============================================================
# BUS RESOLUTION
# ============================================================

def _resolve_bus(
    context: Any,
    reference: EndpointReference,
) -> Any:
    """
    Resolve a Bus EndpointReference through the canonical
    Network lookup boundary.
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

    network = _get_network(
        context
    )

    try:
        return network.get_by_id(
            "bus",
            reference.object_id,
        )

    except KeyError as exc:
        raise ResourceError(
            code="BUS_NOT_FOUND",
            message=(
                f"Bus '{reference.object_id}' "
                "could not be resolved."
            ),
            details={
                "bus_id": reference.object_id,
            },
        ) from exc


# ============================================================
# TERMINAL RESOLUTION
# ============================================================

def _resolve_terminal(
    context: Any,
    reference: EndpointReference,
) -> Any:
    """
    Resolve a Terminal EndpointReference.

    Equipment lookup is delegated to Network.get_by_id().
    Terminal ownership remains with the equipment object.
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

    equipment = _resolve_equipment_by_id(
        context,
        equipment_type=reference.equipment_type,
        object_id=reference.object_id,
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
                    if reference.equipment_type is not None
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

    equipment_type = (
        reference.equipment_type.value
        if reference.equipment_type is not None
        else "equipment"
    )

    raise ResourceError(
        code="TERMINAL_NOT_FOUND",
        message=(
            f"Terminal '{requested_role}' was not "
            f"found on {equipment_type} "
            f"'{reference.object_id}'."
        ),
        details={
            "equipment_type": equipment_type,
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

    if (
        reference.kind
        is EndpointReferenceKind.BUS
    ):
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

    Handlers translate Commands into ModelService operations.

    Core mutation is never performed directly here.
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
