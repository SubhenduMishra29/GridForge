# ============================================================
# File: ui/tools/endpoint_identity_adapter.py
# GridForge V2 — SLD Endpoint Identity Adapter
# Author: Subhendu Mishra
# ============================================================
"""
Translate presentation snap identity into Application endpoint intent.

Architecture
------------

    SnapResult
        |
        v
    EndpointIdentityAdapter
        |
        v
    EndpointReference
        |
        v
    Application Command

This module is a presentation/application boundary helper.
It never resolves Core objects, mutates Core, or performs topology.

BusItem and LineItem remain unchanged. The adapter uses existing
presentation identity and type information only.
"""

from __future__ import annotations

from typing import Any

from core.application.endpoint_reference import EndpointReference, EquipmentType
from ui.equipment.terminal import EquipmentTerminal


class EndpointIdentityAdapter:
    """Convert a snapped presentation endpoint into an immutable reference."""

    @staticmethod
    def from_equipment_terminal(
        terminal: EquipmentTerminal,
        equipment_type: EquipmentType,
    ) -> EndpointReference:
        """Adapt a UI terminal to the canonical Core endpoint identity.

        ``EquipmentTerminal.terminal_id`` is only the UI registry identity.
        It is deliberately not copied into ``EndpointReference``. The Core
        endpoint identity is ``equipment_id + terminal_role``; here
        ``terminal_name`` is the presentation-side terminal role.
        """
        if not isinstance(terminal, EquipmentTerminal):
            raise TypeError("terminal must be an EquipmentTerminal.")
        if not isinstance(equipment_type, EquipmentType):
            raise TypeError("equipment_type must be an EquipmentType.")
        return EndpointReference.terminal(
            equipment_type=equipment_type,
            equipment_id=terminal.equipment_id,
            terminal_role=terminal.terminal_name,
        )
    @staticmethod
    def from_snap_result(result: Any) -> EndpointReference:
        """Return an EndpointReference for a supported object snap."""
        if result is None:
            raise ValueError("Snap result must not be None.")

        object_id = getattr(result, "object_id", None)
        source = getattr(result, "source", None)
        snap_type = getattr(result, "snap_type", None)

        if object_id is None:
            raise ValueError(
                "Line connection requires an object snap with a stable object_id."
            )

        if snap_type is not None and getattr(snap_type, "name", None) != "OBJECT":
            raise ValueError(
                "Line connection requires an object endpoint snap."
            )

        if source is not None and source.__class__.__name__ == "BusItem":
            return EndpointReference.bus(str(object_id))

        endpoint_reference = getattr(source, "endpoint_reference", None)
        if isinstance(endpoint_reference, EndpointReference):
            return endpoint_reference

        terminal_name = getattr(result, "terminal_name", None)
        terminal_id = getattr(result, "terminal_id", None)
        if terminal_name is None:
            raise ValueError("Terminal snap is missing its canonical terminal role.")
        equipment = getattr(source, "equipment", None)
        equipment_type = getattr(equipment, "equipment_type", None)
        if not isinstance(equipment_type, str) or not equipment_type.strip():
            raise ValueError("Terminal snap source does not expose canonical equipment_type.")
        try:
            canonical_type = EquipmentType(equipment_type)
        except ValueError as exc:
            raise ValueError(f"Unsupported snapped equipment type: {equipment_type!r}") from exc
        if terminal_id is None:
            raise ValueError("Terminal snap is missing presentation terminal identity.")
        return EndpointReference.terminal(
            equipment_type=canonical_type,
            equipment_id=str(object_id),
            terminal_role=str(terminal_name),
        )


__all__ = ["EndpointIdentityAdapter"]
