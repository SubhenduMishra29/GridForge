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
#     A terminal is the explicit logical connection point through
#     which electrical equipment participates in the SLD topology.
#
#     Terminals are independent of Qt graphics objects.
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
#     - establish connections;
#     - validate topology;
#     - perform electrical calculations;
#     - render itself;
#     - create Qt objects.
#
# ============================================================

"""
GridForge V2 — Equipment Terminal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class EquipmentTerminal:
    """
    Logical connection point belonging to one equipment object.

    ``local_position`` is expressed in the equipment-local
    coordinate system rather than global canvas coordinates.

    Terminal identity is stable and independent of any
    QGraphicsItem.
    """

    terminal_id: str
    equipment_id: str
    terminal_name: str

    local_position: tuple[float, float] = (0.0, 0.0)

    properties: dict[str, Any] = field(
        default_factory=dict
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    def __post_init__(self) -> None:
        """
        Validate and normalize terminal state.
        """

        self.terminal_id = self._validate_identifier(
            self.terminal_id,
            "terminal_id",
        )

        self.equipment_id = self._validate_identifier(
            self.equipment_id,
            "equipment_id",
        )

        self.terminal_name = self._validate_identifier(
            self.terminal_name,
            "terminal_name",
        )

        self.local_position = self._normalize_position(
            self.local_position
        )

        if not isinstance(
            self.properties,
            dict,
        ):
            raise TypeError(
                "properties must be a dictionary"
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_identifier(
        value: str,
        field_name: str,
    ) -> str:
        """
        Validate a required logical identifier.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return value

    # --------------------------------------------------------

    @staticmethod
    def _normalize_position(
        position: Any,
    ) -> tuple[float, float]:
        """
        Validate and normalize a two-dimensional position.
        """

        if isinstance(
            position,
            (str, bytes),
        ):
            raise TypeError(
                "local_position must contain two numeric coordinates"
            )

        try:
            values = tuple(position)
        except TypeError as exc:
            raise TypeError(
                "local_position must contain two numeric coordinates"
            ) from exc

        if len(values) != 2:
            raise ValueError(
                "local_position must contain exactly "
                "two coordinates"
            )

        try:
            return (
                float(values[0]),
                float(values[1]),
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise TypeError(
                "local_position coordinates must be numeric"
            ) from exc

    # ========================================================
    # POSITION
    # ========================================================

    @property
    def x(self) -> float:
        """
        Return the local X coordinate.
        """

        return self.local_position[0]

    # --------------------------------------------------------

    @property
    def y(self) -> float:
        """
        Return the local Y coordinate.
        """

        return self.local_position[1]

    # --------------------------------------------------------

    def set_position(
        self,
        position: tuple[float, float],
    ) -> None:
        """
        Set the terminal's local position.
        """

        self.local_position = self._normalize_position(
            position
        )

    # ========================================================
    # METADATA
    # ========================================================

    def get_property(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Return a terminal property.
        """

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "property key must be a string"
            )

        return self.properties.get(
            key,
            default,
        )

    # --------------------------------------------------------

    def set_property(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Set a terminal property.
        """

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "property key must be a string"
            )

        key = key.strip()

        if not key:
            raise ValueError(
                "property key must not be empty"
            )

        self.properties[key] = value

    # --------------------------------------------------------

    def has_property(
        self,
        key: str,
    ) -> bool:
        """
        Return whether the terminal contains a property.
        """

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "property key must be a string"
            )

        return key in self.properties

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the terminal into a plain dictionary.
        """

        return {
            "terminal_id": self.terminal_id,
            "equipment_id": self.equipment_id,
            "terminal_name": self.terminal_name,
            "local_position": [
                self.local_position[0],
                self.local_position[1],
            ],
            "properties": dict(
                self.properties
            ),
        }

    # --------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "EquipmentTerminal":
        """
        Construct a terminal from serialized data.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise TypeError(
                "data must be a mapping"
            )

        required_fields = (
            "terminal_id",
            "equipment_id",
            "terminal_name",
        )

        for field_name in required_fields:
            if field_name not in data:
                raise KeyError(
                    field_name
                )

        properties = data.get(
            "properties",
            {},
        )

        if not isinstance(
            properties,
            Mapping,
        ):
            raise TypeError(
                "properties must be a mapping"
            )

        return cls(
            terminal_id=data[
                "terminal_id"
            ],
            equipment_id=data[
                "equipment_id"
            ],
            terminal_name=data[
                "terminal_name"
            ],
            local_position=data.get(
                "local_position",
                (0.0, 0.0),
            ),
            properties=dict(
                properties
            ),
        )


__all__ = [
    "EquipmentTerminal",
]
