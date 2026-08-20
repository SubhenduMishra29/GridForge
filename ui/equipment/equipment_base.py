# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/equipment_base.py
#
# Purpose:
#     Base logical representation of an electrical equipment
#     object used by the GridForge SLD.
#
# Architectural Role:
#     EquipmentBase is the common non-Qt abstraction shared by
#     all SLD equipment objects.
#
# Responsibilities:
#     - maintain stable equipment identity;
#     - maintain equipment type;
#     - maintain logical position;
#     - maintain equipment properties;
#     - maintain terminal identifiers;
#     - provide serialization support.
#
# Does NOT:
#     - create QGraphicsItem objects;
#     - render symbols;
#     - calculate electrical quantities;
#     - own Core network objects;
#     - perform topology validation.
#
# ============================================================

"""
GridForge V2 — Equipment Base.

Qt-independent logical representation of an SLD equipment object.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional


class EquipmentBase:
    """
    Base class for all UI-side SLD equipment.

    EquipmentBase stores logical/document state only.

    It deliberately has no dependency on:

        - Qt;
        - QGraphicsItem;
        - renderers;
        - Core network objects;
        - electrical solvers.
    """

    def __init__(
        self,
        equipment_id: str,
        equipment_type: str,
        *,
        name: Optional[str] = None,
        position: tuple[float, float] = (0.0, 0.0),
        properties: Optional[Mapping[str, Any]] = None,
        terminal_ids: Optional[Iterable[str]] = None,
    ) -> None:
        self._equipment_id = self._validate_identifier(
            equipment_id,
            "equipment_id",
        )

        self._equipment_type = self._validate_identifier(
            equipment_type,
            "equipment_type",
        )

        if name is None:
            self._name = self._equipment_id
        else:
            self._name = self._validate_identifier(
                name,
                "name",
            )

        self._position = self._normalize_position(
            position
        )

        if properties is None:
            self._properties = {}
        elif isinstance(properties, Mapping):
            self._properties = dict(properties)
        else:
            raise TypeError(
                "properties must be a mapping"
            )

        self._terminal_ids: list[str] = []

        if terminal_ids is not None:
            for terminal_id in terminal_ids:
                self.add_terminal(
                    terminal_id
                )

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    @staticmethod
    def _validate_identifier(
        value: str,
        field_name: str,
    ) -> str:
        """
        Validate and normalize a required textual identifier.
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
        value: Any,
    ) -> tuple[float, float]:
        """
        Validate and normalize a two-dimensional position.
        """

        if isinstance(
            value,
            (str, bytes),
        ):
            raise TypeError(
                "position must contain two numeric coordinates"
            )

        try:
            coordinates = tuple(value)
        except TypeError as exc:
            raise TypeError(
                "position must contain two numeric coordinates"
            ) from exc

        if len(coordinates) != 2:
            raise ValueError(
                "position must contain exactly two coordinates"
            )

        try:
            return (
                float(coordinates[0]),
                float(coordinates[1]),
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise TypeError(
                "position coordinates must be numeric"
            ) from exc

    # ========================================================
    # IDENTITY
    # ========================================================

    @property
    def equipment_id(self) -> str:
        """
        Return the stable equipment identifier.
        """

        return self._equipment_id

    # --------------------------------------------------------

    @property
    def equipment_type(self) -> str:
        """
        Return the stable equipment type identifier.
        """

        return self._equipment_type

    # ========================================================
    # PRESENTATION IDENTITY
    # ========================================================

    @property
    def name(self) -> str:
        """
        Return the equipment display name.
        """

        return self._name

    # --------------------------------------------------------

    @name.setter
    def name(
        self,
        value: str,
    ) -> None:
        """
        Set the equipment display name.
        """

        self._name = self._validate_identifier(
            value,
            "name",
        )

    # ========================================================
    # POSITION
    # ========================================================

    @property
    def position(self) -> tuple[float, float]:
        """
        Return the equipment's logical canvas position.
        """

        return self._position

    # --------------------------------------------------------

    @position.setter
    def position(
        self,
        value: tuple[float, float],
    ) -> None:
        """
        Set the equipment's logical canvas position.
        """

        self._position = self._normalize_position(
            value
        )

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def properties(self) -> dict[str, Any]:
        """
        Return the mutable equipment property dictionary.

        Ownership remains with this equipment object.
        """

        return self._properties

    # --------------------------------------------------------

    def get_property(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Return an equipment property.
        """

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "property key must be a string"
            )

        return self._properties.get(
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
        Set an equipment property.
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

        self._properties[key] = value

    # --------------------------------------------------------

    def remove_property(
        self,
        key: str,
    ) -> Any:
        """
        Remove and return an equipment property.
        """

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "property key must be a string"
            )

        if key not in self._properties:
            raise KeyError(key)

        return self._properties.pop(
            key
        )

    # --------------------------------------------------------

    def has_property(
        self,
        key: str,
    ) -> bool:
        """
        Return whether a property exists.
        """

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "property key must be a string"
            )

        return key in self._properties

    # ========================================================
    # TERMINALS
    # ========================================================

    @property
    def terminal_ids(self) -> tuple[str, ...]:
        """
        Return an immutable snapshot of terminal identifiers.
        """

        return tuple(
            self._terminal_ids
        )

    # --------------------------------------------------------

    def add_terminal(
        self,
        terminal_id: str,
    ) -> None:
        """
        Register a logical terminal identifier.
        """

        terminal_id = self._validate_identifier(
            terminal_id,
            "terminal_id",
        )

        if terminal_id in self._terminal_ids:
            raise ValueError(
                f"Terminal already exists: {terminal_id}"
            )

        self._terminal_ids.append(
            terminal_id
        )

    # --------------------------------------------------------

    def remove_terminal(
        self,
        terminal_id: str,
    ) -> None:
        """
        Remove a registered terminal identifier.
        """

        if not isinstance(
            terminal_id,
            str,
        ):
            raise TypeError(
                "terminal_id must be a string"
            )

        try:
            self._terminal_ids.remove(
                terminal_id
            )
        except ValueError as exc:
            raise KeyError(
                terminal_id
            ) from exc

    # --------------------------------------------------------

    def has_terminal(
        self,
        terminal_id: str,
    ) -> bool:
        """
        Return whether the equipment owns the given terminal ID.
        """

        if not isinstance(
            terminal_id,
            str,
        ):
            raise TypeError(
                "terminal_id must be a string"
            )

        return terminal_id in self._terminal_ids

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize logical equipment state.

        The result contains no Qt objects.
        """

        return {
            "equipment_id": self.equipment_id,
            "equipment_type": self.equipment_type,
            "name": self.name,
            "position": [
                self.position[0],
                self.position[1],
            ],
            "properties": dict(
                self.properties
            ),
            "terminal_ids": list(
                self.terminal_ids
            ),
        }

    # --------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "EquipmentBase":
        """
        Reconstruct an EquipmentBase from serialized state.

        Concrete equipment factories may override this path for
        specialized equipment classes.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise TypeError(
                "data must be a mapping"
            )

        if "equipment_id" not in data:
            raise KeyError(
                "equipment_id"
            )

        if "equipment_type" not in data:
            raise KeyError(
                "equipment_type"
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

        terminal_ids = data.get(
            "terminal_ids",
            [],
        )

        if isinstance(
            terminal_ids,
            (str, bytes),
        ):
            raise TypeError(
                "terminal_ids must be an iterable of strings"
            )

        return cls(
            equipment_id=data[
                "equipment_id"
            ],
            equipment_type=data[
                "equipment_type"
            ],
            name=data.get(
                "name",
                data["equipment_id"],
            ),
            position=data.get(
                "position",
                (0.0, 0.0),
            ),
            properties=properties,
            terminal_ids=terminal_ids,
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            f"{self.__class__.__name__}("
            f"equipment_id={self.equipment_id!r}, "
            f"equipment_type={self.equipment_type!r}, "
            f"name={self.name!r}, "
            f"terminals={len(self._terminal_ids)})"
        )


__all__ = [
    "EquipmentBase",
]
