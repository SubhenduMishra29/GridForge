# ============================================================
# File: ui/sld/simple_wire_selection.py
# GridForge V2 — Simple Wire Selection/Deletion Boundary
# ============================================================

"""Translate a committed SLD Simple Wire selection into an Application command."""

from __future__ import annotations

from typing import Any

from core.application.commands.simple_wire_commands import RemoveSimpleWireConnectionCommand


def delete_selected_simple_wire(application: Any, connection_id: str) -> Any:
    """Delete a selected projection by authoritative connection identity."""
    if application is None:
        raise ValueError("application is required")
    presentation = application.presentation
    connection = presentation.model.get_connection(connection_id)
    if connection.properties.get("connection_kind") != "SIMPLE_WIRE":
        raise ValueError("Selected SLD connection is not a Simple Wire projection.")
    endpoint_a = connection.properties.get("endpoint_a")
    endpoint_b = connection.properties.get("endpoint_b")
    from core.model import EndpointReference
    if not isinstance(endpoint_a, EndpointReference) or not isinstance(endpoint_b, EndpointReference):
        raise ValueError("Simple Wire SLD projection is missing canonical endpoint identity.")
    return application.execute(
        RemoveSimpleWireConnectionCommand(
            connection_id=connection_id,
            endpoint_a=endpoint_a,
            endpoint_b=endpoint_b,
        )
    )


__all__ = ["delete_selected_simple_wire"]
