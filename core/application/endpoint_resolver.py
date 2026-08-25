# ============================================================
# File: core/application/endpoint_resolver.py
# GridForge V2 — Application Endpoint Resolver
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Endpoint Resolver
=============================================

Resolves immutable Application EndpointReference values into
canonical Core Bus / Terminal objects.

Architecture
------------

    EndpointReference
            |
            v
    EndpointResolver
            |
            +----------------------+
            |                      |
            v                      v
    Network.get_by_id()     Network.get_by_id()
            |                      |
            v                      v
           Bus                  Equipment
                                   |
                                   v
                           equipment.terminals
                                   |
                                   v
                              Terminal

The resolver:

    * resolves Application references;
    * returns canonical Core objects;
    * uses Network.get_by_id() as the canonical lookup boundary;
    * validates terminal ownership;
    * rejects ambiguous terminal roles.

The resolver does NOT:

    * create Core objects;
    * mutate Core objects;
    * modify topology;
    * connect terminals;
    * access NetworkRegistry internals;
    * access SLD/UI state;
    * invoke ModelService;
    * perform engineering calculations.

Identity Contract
-----------------

Bus identity:

    bus_id

Terminal identity:

    owning equipment type
    owning equipment id
    terminal role

A Terminal does not have a globally unique ID.

Terminal ownership remains with the owning Core equipment object.
"""

from __future__ import annotations

from typing import Any

from .endpoint_reference import (
    EndpointReference,
    EndpointReferenceKind,
)
from .errors import (
    ResourceError,
    ValidationError,
)


# ============================================================
# NETWORK ACCESS
# ============================================================

def _get_network(
    context: Any,
) -> Any:
    """
    Return the canonical Core Network from the Application
    context.

    The resolver does not construct or cache a Network.
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
    Resolve canonical equipment through Network.get_by_id().

    The Application layer intentionally does not know how the
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

    Exactly one terminal must satisfy:

        terminal.role == requested_role
        terminal.owner is equipment
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

    # --------------------------------------------------------
    # Collect all valid matches.
    #
    # Do not return the first match. Terminal roles are only
    # unique within the owning equipment and malformed model
    # state must not be silently accepted.
    # --------------------------------------------------------

    matches = []

    for terminal in terminals:

        if getattr(
            terminal,
            "role",
            None,
        ) != requested_role:
            continue

        # ----------------------------------------------------
        # Frozen ownership invariant:
        #
        # The terminal returned for an equipment reference
        # must actually belong to that equipment.
        # ----------------------------------------------------

        if getattr(
            terminal,
            "owner",
            None,
        ) is not equipment:
            continue

        matches.append(
            terminal
        )

    equipment_type = (
        reference.equipment_type.value
        if reference.equipment_type is not None
        else "equipment"
    )

    # --------------------------------------------------------
    # No match
    # --------------------------------------------------------

    if not matches:
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

    # --------------------------------------------------------
    # Multiple matches
    # --------------------------------------------------------

    if len(matches) > 1:
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

    # --------------------------------------------------------
    # Exactly one canonical terminal
    # --------------------------------------------------------

    return matches[0]


# ============================================================
# ENDPOINT RESOLUTION
# ============================================================

def resolve_endpoint(
    context: Any,
    reference: EndpointReference,
) -> Any:
    """
    Resolve an immutable Application EndpointReference into
    the corresponding canonical Core endpoint.

    Returns
    -------
    Bus | Terminal
        The canonical Core endpoint represented by the
        reference.

    Raises
    ------
    ValidationError
        If the reference is malformed or unsupported.

    ResourceError
        If the referenced canonical Core object cannot be
        resolved.
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
# RESOLVER FACADE
# ============================================================

class EndpointResolver:
    """
    Application-layer endpoint resolver.

    This is a thin façade over the canonical resolution
    functions.

    The resolver is intentionally stateless.

    It does not retain:

        * Network
        * Core objects
        * terminals
        * topology state
        * command state
    """

    @staticmethod
    def resolve(
        context: Any,
        reference: EndpointReference,
    ) -> Any:
        """
        Resolve an EndpointReference to its canonical Core
        Bus or Terminal.
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
