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

from core.model import EndpointReference, EquipmentType
from ui.equipment.terminal import EquipmentTerminal
from ui.items.bus_item import BusItem


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

        if isinstance(source, BusItem):
            # A Bus is an endpoint kind of its own. Never manufacture a
            # terminal role for a Bus snap.
            return EndpointReference.bus(str(object_id))

        terminal_id = getattr(result, "terminal_id", None)
        terminal_name = getattr(result, "terminal_name", None)

        endpoint_reference = getattr(source, "endpoint_reference", None)
        if endpoint_reference is not None:
            # A presentation source may already carry the canonical immutable
            # reference. Reuse it, but never trust it blindly: the snap result
            # must still agree with the snapped object kind and, for terminals,
            # with the presentation terminal role/equipment identity.
            if not isinstance(endpoint_reference, EndpointReference):
                raise TypeError(
                    "Presentation endpoint_reference must be an EndpointReference."
                )
            if endpoint_reference.is_bus:
                if terminal_id is not None or terminal_name is not None:
                    raise ValueError(
                        "A Bus endpoint reference cannot be combined with terminal snap identity."
                    )
                return endpoint_reference
            if not endpoint_reference.is_terminal:
                raise ValueError("Unsupported endpoint reference kind on presentation source.")
            if str(endpoint_reference.equipment_id) != str(object_id):
                raise ValueError(
                    "Presentation EndpointReference equipment identity does not match the snap object."
                )
            if terminal_name is not None and str(endpoint_reference.terminal_role) != str(terminal_name):
                raise ValueError(
                    "Presentation EndpointReference terminal role does not match the snap result."
                )
            return endpoint_reference

        if terminal_name is None:
            raise ValueError("Terminal snap is missing its canonical terminal role.")

        equipment = getattr(source, "equipment", None)
        equipment_type = getattr(equipment, "equipment_type", None)
        if not isinstance(equipment_type, str) or not equipment_type.strip():
            raise ValueError("Terminal snap source does not expose canonical equipment_type.")

        # The presentation terminal role is valid only when it resolves to
        # exactly one terminal owned by the snapped presentation equipment.
        # terminal_id is only a presentation/registry identity and is never
        # promoted into EndpointReference.
        terminals = tuple(getattr(equipment, "terminals", ()) or ())
        matches = [
            terminal
            for terminal in terminals
            if terminal.equipment_id == str(object_id)
            and terminal.terminal_name == str(terminal_name)
            and (terminal_id is None or terminal.terminal_id == str(terminal_id))
        ]
        if len(matches) != 1:
            raise ValueError(
                "Terminal snap identity must resolve to exactly one presentation terminal: "
                f"equipment_id={object_id!r}, terminal_id={terminal_id!r}, "
                f"terminal_role={terminal_name!r}, matches={len(matches)}."
            )

        canonical_type = next(
            (
                candidate
                for candidate in EquipmentType
                if candidate.value == equipment_type.strip().lower()
            ),
            None,
        )
        if canonical_type is None:
            raise ValueError(
                f"Unsupported snapped equipment type: {equipment_type!r}"
            )
        return EndpointReference.terminal(
            equipment_type=canonical_type,
            equipment_id=str(object_id),
            terminal_role=matches[0].terminal_name,
        )


__all__ = ["EndpointIdentityAdapter"]
