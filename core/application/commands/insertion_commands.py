# ============================================================
# GridForge V2 — Electrical Equipment Insertion Command
# ============================================================

"""Immutable Application intent for inserting equipment into a Simple Wire."""

from __future__ import annotations

from typing import Mapping, Any
from uuid import UUID, uuid4

from ..command import Command

INSERT_EQUIPMENT_INTO_CONNECTION = "connectivity.insert_equipment_into_connection"


class InsertEquipmentIntoConnectionCommand(Command):
    """Immutable intent for one atomic electrical insertion operation.

    The command carries only value data. Core objects, Qt objects, scene state,
    and mutable UI state never cross this boundary.
    """

    def __init__(
        self,
        *,
        connection_id: str,
        equipment_type: str,
        equipment_id: str | None = None,
        insertion_position: tuple[float, float],
        orientation: float = 0.0,
        terminal_mapping: tuple[str, str] | None = None,
        creation_parameters: Mapping[str, Any] | None = None,
        segment_index: int = 0,
        terminal_anchors: Mapping[str, tuple[float, float]] | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(connection_id, str) or not connection_id.strip():
            raise ValueError("connection_id must be a non-empty string.")
        if not isinstance(equipment_type, str) or not equipment_type.strip():
            raise ValueError("equipment_type must be a non-empty string.")
        if equipment_id is not None and (
            not isinstance(equipment_id, str) or not equipment_id.strip()
        ):
            raise ValueError("equipment_id must be a non-empty string when provided.")
        if (
            not isinstance(insertion_position, (tuple, list))
            or len(insertion_position) != 2
        ):
            raise TypeError("insertion_position must contain exactly two coordinates.")
        x, y = insertion_position
        if isinstance(x, bool) or isinstance(y, bool):
            raise TypeError("insertion_position coordinates must be numeric.")
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError("insertion_position coordinates must be numeric.")
        if isinstance(orientation, bool) or not isinstance(orientation, (int, float)):
            raise TypeError("orientation must be numeric.")
        if isinstance(segment_index, bool) or not isinstance(segment_index, int) or segment_index < 0:
            raise ValueError("segment_index must be a non-negative integer.")
        if terminal_mapping is not None:
            if not isinstance(terminal_mapping, (tuple, list)) or len(terminal_mapping) != 2:
                raise TypeError("terminal_mapping must contain exactly two terminal roles.")
            if any(not isinstance(role, str) or not role.strip() for role in terminal_mapping):
                raise ValueError("terminal_mapping roles must be non-empty strings.")
        if creation_parameters is not None and not isinstance(creation_parameters, Mapping):
            raise TypeError("creation_parameters must be a mapping or None.")
        if terminal_anchors is not None:
            if not isinstance(terminal_anchors, Mapping):
                raise TypeError("terminal_anchors must be a mapping or None.")
            for role, anchor in terminal_anchors.items():
                if not isinstance(role, str) or not role.strip():
                    raise ValueError("terminal_anchors keys must be non-empty strings.")
                if not isinstance(anchor, (tuple, list)) or len(anchor) != 2:
                    raise TypeError("terminal anchor positions must contain exactly two coordinates.")
                if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in anchor):
                    raise TypeError("terminal anchor coordinates must be numeric.")

        super().__init__(
            command_type=INSERT_EQUIPMENT_INTO_CONNECTION,
            payload={
                "connection_id": connection_id.strip(),
                "equipment_type": equipment_type.strip().lower(),
                "equipment_id": (
                    None if equipment_id is None else equipment_id.strip()
                ),
                "insertion_position": (float(x), float(y)),
                "orientation": float(orientation),
                "terminal_mapping": None if terminal_mapping is None else tuple(str(role).strip() for role in terminal_mapping),
                "creation_parameters": {} if creation_parameters is None else dict(creation_parameters),
                "segment_index": segment_index,
                "terminal_anchors": None if terminal_anchors is None else {
                    str(role).strip(): (float(anchor[0]), float(anchor[1]))
                    for role, anchor in terminal_anchors.items()
                },
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


__all__ = [
    "INSERT_EQUIPMENT_INTO_CONNECTION",
    "InsertEquipmentIntoConnectionCommand",
]
