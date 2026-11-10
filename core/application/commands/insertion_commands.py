# ============================================================
# GridForge V2 — Electrical Equipment Insertion Command
# ============================================================

"""Immutable Application intent for inserting equipment into a Simple Wire."""

from __future__ import annotations

from typing import Mapping, Any
import math
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
        route_geometry: Mapping[str, Any] | None = None,
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
        if not math.isfinite(float(x)) or not math.isfinite(float(y)):
            raise ValueError("insertion_position coordinates must be finite.")
        if isinstance(orientation, bool) or not isinstance(orientation, (int, float)):
            raise TypeError("orientation must be numeric.")
        if not math.isfinite(float(orientation)):
            raise ValueError("orientation must be finite.")
        if isinstance(segment_index, bool) or not isinstance(segment_index, int) or segment_index < 0:
            raise ValueError("segment_index must be a non-negative integer.")
        if terminal_mapping is not None:
            if not isinstance(terminal_mapping, (tuple, list)) or len(terminal_mapping) != 2:
                raise TypeError("terminal_mapping must contain exactly two terminal roles.")
            if any(not isinstance(role, str) or not role.strip() for role in terminal_mapping):
                raise ValueError("terminal_mapping roles must be non-empty strings.")
        if creation_parameters is not None and not isinstance(creation_parameters, Mapping):
            raise TypeError("creation_parameters must be a mapping or None.")
        normalized_terminal_anchors: dict[str, tuple[float, float]] | None = None
        if terminal_anchors is not None:
            if not isinstance(terminal_anchors, Mapping):
                raise TypeError("terminal_anchors must be a mapping or None.")
            normalized_terminal_anchors = {}
            for role, anchor in terminal_anchors.items():
                if not isinstance(role, str) or not role.strip():
                    raise ValueError("terminal_anchors keys must be non-empty strings.")
                normalized_role = role.strip()
                if normalized_role in normalized_terminal_anchors:
                    raise ValueError("terminal_anchors keys must be unique after whitespace normalization.")
                if not isinstance(anchor, (tuple, list)) or len(anchor) != 2:
                    raise TypeError("terminal anchor positions must contain exactly two coordinates.")
                if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in anchor):
                    raise TypeError("terminal anchor coordinates must be numeric.")
                if any(not math.isfinite(float(value)) for value in anchor):
                    raise ValueError("terminal anchor coordinates must be finite.")
                normalized_terminal_anchors[normalized_role] = (float(anchor[0]), float(anchor[1]))

        normalized_route_geometry: dict[str, Any] | None = None
        if route_geometry is not None:
            if not isinstance(route_geometry, Mapping):
                raise TypeError("route_geometry must be a mapping or None.")
            presentation_id = route_geometry.get("presentation_id")
            core_connection_id = route_geometry.get("core_connection_id")
            if not isinstance(presentation_id, str) or not presentation_id.strip():
                raise ValueError("route_geometry.presentation_id must be non-empty.")
            if core_connection_id != connection_id.strip():
                raise ValueError("route_geometry.core_connection_id must match connection_id.")
            if route_geometry.get("route_ownership") not in {"auto", "engineer"}:
                raise ValueError("route_geometry.route_ownership must be 'auto' or 'engineer'.")

            def normalized_point(value: Any, field: str) -> tuple[float, float]:
                if not isinstance(value, (tuple, list)) or len(value) != 2:
                    raise TypeError(f"route_geometry.{field} must contain exactly two coordinates.")
                coordinates = []
                for coordinate in value:
                    if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)):
                        raise TypeError(f"route_geometry.{field} coordinates must be numeric.")
                    numeric = float(coordinate)
                    if not math.isfinite(numeric):
                        raise ValueError(f"route_geometry.{field} coordinates must be finite.")
                    coordinates.append(numeric)
                return (coordinates[0], coordinates[1])

            source_endpoint = route_geometry.get("source_endpoint")
            target_endpoint = route_geometry.get("target_endpoint")
            if not isinstance(source_endpoint, Mapping) or not isinstance(target_endpoint, Mapping):
                raise ValueError("route_geometry must carry both canonical SLD endpoint descriptors.")
            raw_points = route_geometry.get("points")
            if not isinstance(raw_points, (tuple, list)):
                raise TypeError("route_geometry.points must be a sequence.")
            normalized_route_geometry = {
                "presentation_id": presentation_id.strip(),
                "core_connection_id": connection_id.strip(),
                "source_endpoint": dict(source_endpoint),
                "target_endpoint": dict(target_endpoint),
                "source": normalized_point(route_geometry.get("source"), "source"),
                "target": normalized_point(route_geometry.get("target"), "target"),
                "points": tuple(
                    normalized_point(point, f"points[{index}]")
                    for index, point in enumerate(raw_points)
                ),
                "route_ownership": route_geometry["route_ownership"],
            }

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
                "terminal_anchors": normalized_terminal_anchors,
                "route_geometry": normalized_route_geometry,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


__all__ = [
    "INSERT_EQUIPMENT_INTO_CONNECTION",
    "InsertEquipmentIntoConnectionCommand",
]
