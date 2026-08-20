# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/terminal.py
#
# Purpose:
#     Defines the terminal abstraction used by SLD equipment.
#
# Architectural Role:
#     A terminal is the explicit connection point through which
#     electrical equipment participates in the SLD topology.
#
#     Terminals are intentionally separate from graphics items.
#     A QGraphicsItem may visually display a terminal, but the
#     terminal itself is a logical UI/domain object.
#
# Responsibilities:
#     - identify an equipment terminal;
#     - identify its parent equipment;
#     - identify its terminal role/name;
#     - store logical local position;
#     - store terminal metadata;
#     - provide serialization.
#
# Does NOT:
#     - establish electrical network connections;
#     - validate topology;
#     - perform electrical calculations;
#     - render itself;
#     - create Qt objects.
#
# Relationship:
#
#     EquipmentBase
#          |
#          +---- Terminal
#          |
#          +---- Terminal
#          |
#          +---- Terminal
#                |
#                v
#        Connection Subsystem
#
# Important Boundary:
#     Terminal identity must remain stable independently of a
#     QGraphicsItem. This allows selection, snapping, connection
#     routing, serialization and Core synchronization to refer to
#     stable logical identifiers.
#
# ============================================================

"""
GridForge V2 — Equipment Terminal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class EquipmentTerminal:
    """
    Logical connection point belonging to one equipment object.

    ``local_position`` is expressed in the equipment's local
    coordinate system, not the global canvas coordinate system.
    """

    terminal_id: str
    equipment_id: str
    terminal_name: str
    local_position: tuple[float, float] = (0.0, 0.0)

    properties: Dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.terminal_id:
            raise ValueError(
                "terminal_id must not be empty"
            )

        if not self.equipment_id:
            raise ValueError(
                "equipment_id must not be empty"
            )

        if not self.terminal_name:
            raise ValueError(
                "terminal_name must not be empty"
            )

        if len(self.local_position) != 2:
            raise ValueError(
                "local_position must contain exactly "
                "two coordinates"
            )

        self.local_position = (
            float(self.local_position[0]),
            float(self.local_position[1]),
        )

    # --------------------------------------------------------
    # Position
    # --------------------------------------------------------

    @property
    def x(self) -> float:
        return self.local_position[0]

    @property
    def y(self) -> float:
        return self.local_position[1]

    def set_position(
        self,
        position: tuple[float, float],
    ) -> None:
        if len(position) != 2:
            raise ValueError(
                "position must contain exactly two coordinates"
            )

        self.local_position = (
            float(position[0]),
            float(position[1]),
        )

    # --------------------------------------------------------
    # Properties
    # --------------------------------------------------------

    def get_property(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.properties.get(
            key,
            default,
        )

    def set_property(
        self,
        key: str,
        value: Any,
    ) -> None:
        if not key:
            raise ValueError(
                "property key must not be empty"
            )

        self.properties[key] = value

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "terminal_id": self.terminal_id,
            "equipment_id": self.equipment_id,
            "terminal_name": self.terminal_name,
            "local_position": list(
                self.local_position
            ),
            "properties": dict(
                self.properties
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "EquipmentTerminal":
        return cls(
            terminal_id=str(
                data["terminal_id"]
            ),
            equipment_id=str(
                data["equipment_id"]
            ),
            terminal_name=str(
                data["terminal_name"]
            ),
            local_position=tuple(
                data.get(
                    "local_position",
                    (0.0, 0.0),
                )
            ),
            properties=dict(
                data.get(
                    "properties",
                    {},
                )
            ),
        )
