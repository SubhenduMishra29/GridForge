# ============================================================
# Author: Subhendu Mishra
# GridForge V2 — SLD Simple Wire Selection/Deletion Boundary
# ============================================================
"""Translate an SLD Simple Wire presentation selection to the Core command boundary.

This module is retained only as a compatibility adapter. Core connection
identity and SLD presentation identity are resolved explicitly; neither is
derived from the other.
"""

from __future__ import annotations

from typing import Any

from core.application.commands.simple_wire_commands import RemoveSimpleWireConnectionCommand
from core.model.endpoint_reference import EndpointReference, EndpointReferenceKind, EquipmentType


def _resolve_presentation(application: Any, selected_id: str) -> tuple[Any, str]:
    model = application.presentation.model
    connection = model.get_connection_optional(selected_id)
    if connection is not None:
        return connection, str(connection.properties.get("core_connection_id") or "")

    matches = tuple(
        item for item in model.connections
        if str(item.properties.get("core_connection_id") or "") == selected_id
    )
    if len(matches) != 1:
        raise ValueError(
            f"Simple Wire selection {selected_id!r} does not resolve to exactly one active SLD companion."
        )
    connection = matches[0]
    return connection, str(connection.properties.get("core_connection_id") or "")


def _core_endpoint(endpoint: Any) -> EndpointReference:
    if endpoint is None:
        raise ValueError("Simple Wire SLD projection is missing endpoint identity.")
    mapping = endpoint.to_dict() if hasattr(endpoint, "to_dict") else dict(endpoint)
    kind = str(mapping.get("kind") or "")
    if kind == "bus":
        return EndpointReference.bus(
            str(mapping["bus_id"] or mapping["node_id"]),
            str(mapping["attachment_id"]),
        )
    if kind == "equipment":
        equipment_type = EquipmentType(str(mapping["equipment_type"]))
        return EndpointReference.terminal(
            equipment_type=equipment_type,
            equipment_id=str(mapping["equipment_id"]),
            terminal_role=str(mapping["terminal_role"]),
        )
    raise ValueError(f"Unsupported SLD endpoint kind: {kind!r}")


def delete_selected_simple_wire(application: Any, selected_id: str) -> Any:
    """Delete a selected active Simple Wire through its canonical Core identity."""
    if application is None:
        raise ValueError("application is required")
    if not isinstance(selected_id, str) or not selected_id:
        raise ValueError("selected_id must be a non-empty string")

    connection, core_connection_id = _resolve_presentation(application, selected_id)
    if connection.properties.get("connection_kind") != "SIMPLE_WIRE":
        raise ValueError("Selected SLD connection is not a Simple Wire projection.")
    if str(connection.properties.get("lifecycle_state", "BOUND")).upper() != "BOUND":
        raise ValueError("Only BOUND SLD Simple Wire presentations can issue Core deletion.")
    if not core_connection_id:
        raise ValueError("Active SLD Simple Wire is missing its Core connection identity.")

    endpoint_a = _core_endpoint(connection.source_endpoint)
    endpoint_b = _core_endpoint(connection.target_endpoint)
    return application.execute(
        RemoveSimpleWireConnectionCommand(
            connection_id=core_connection_id,
            endpoint_a=endpoint_a,
            endpoint_b=endpoint_b,
        )
    )


__all__ = ["delete_selected_simple_wire"]
