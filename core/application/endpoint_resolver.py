# ============================================================
# File: core/application/endpoint_resolver.py
# GridForge V2 — Application Endpoint Resolver
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Endpoint Resolver
=============================================

Resolves immutable EndpointReference values into canonical
Core Bus / Terminal objects.

The resolver is read-only.

It does not:

    * create Core objects;
    * mutate Core objects;
    * modify topology;
    * access NetworkRegistry internals;
    * access SLD/UI state;
    * invoke ModelService.

Identity contract
-----------------

Bus:

    bus_id

Terminal:

    equipment_type
    equipment_id
    terminal_role

A Terminal has no globally unique ID.

Its identity is the owning equipment plus terminal role.
"""

from __future__ import annotations

from typing import Any

from .endpoint_reference import (
    EndpointReference,
    EndpointReferenceKind,
)
from .errors import ResourceError, ValidationError


# ============================================================
# NETWORK ACCESS
# ============================================================

def _get_network(context: Any) -> Any:
    """
    Return the canonical Core Network from the Application
    context.
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
# EQUIPMENT RESOLUTION
# ============================================================

def _resolve_equipment_by_id(
    context: Any,
    *,
    equipment_type: Any,
    object_id: str,
) -> Any:
    """
    Resolve canonical equipment exclusively through the
    Network public lookup boundary.
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

    if not isinstance(value, str) or not value:
        raise ValidationError(
            code="INVALID_EQUIPMENT_TYPE",
            message=(
                "Terminal reference contains an "
                "invalid EquipmentType."
            ),
            details={
                "equipment_type": str(equipment_type),
                "equipment_id": object_id,
            },
        )

    network = _get_network(context)

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
    Resolve a Bus EndpointReference to the canonical Bus.
    """

    network = _get_network(context)

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
    Resolve a Terminal EndpointReference to the canonical
    Terminal owned by the referenced equipment.

    Exactly one terminal must satisfy both:

        terminal.role == reference.terminal_role
        terminal.owner is equipment
    """

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
                f"Equipment '{reference.object_id}' "
                "does not expose its terminals."
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

    matches = [
        terminal
        for terminal in terminals
        if (
            terminal.role == requested_role
            and terminal.owner is equipment
        )
    ]

    if not matches:
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

    if len(matches) > 1:
        equipment_type = (
            reference.equipment_type.value
            if reference.equipment_type is not None
            else "equipment"
        )

        raise ResourceError(
            code="AMBIGUOUS_TERMINAL",
            message=(
                f"Terminal role '{requested_role}' is "
                f"ambiguous on {equipment_type} "
                f"'{reference.object_id}'."
            ),
            details={
                "equipment_type": equipment_type,
                "equipment_id": reference.object_id,
                "terminal_role": requested_role,
                "match_count": len(matches),
            },
        )

    return matches[0]


# ============================================================
# PUBLIC RESOLUTION FUNCTION
# ============================================================

def resolve_endpoint(
    context: Any,
    reference: EndpointReference,
) -> Any:
    """
    Resolve an EndpointReference into the canonical Core
    Bus or Terminal.

    No Core mutation occurs.
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
                "received_type": type(reference).__name__,
            },
        )

    if reference.kind is EndpointReferenceKind.BUS:
        return _resolve_bus(
            context,
            reference,
        )

    if reference.kind is EndpointReferenceKind.TERMINAL:
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
# STATELESS RESOLVER FACADE
# ============================================================

class EndpointResolver:
    """
    Stateless Application endpoint resolver.

    The resolver intentionally does not retain Network,
    Core objects, topology, or command state.
    """

    @staticmethod
    def resolve(
        context: Any,
        reference: EndpointReference,
    ) -> Any:
        """
        Resolve an immutable endpoint reference.
        """

        return resolve_endpoint(
            context,
            reference,
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "EndpointResolver",
    "resolve_endpoint",
]
