
---

## `ui/equipment/equipment_base.py`

```python
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
# Detailed Working:
#
#     EquipmentFactory
#            |
#            v
#     EquipmentBase
#        /       \
#       v         v
#    identity   properties
#       |
#       v
#     SLDModel
#       |
#       v
#     Canvas / Item / Renderer
#
# ============================================================

"""
GridForge V2 — Equipment Base.

Qt-independent logical representation of an SLD equipment object.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


class EquipmentBase:
    """
    Base class for all UI-side SLD equipment.

    An equipment object is deliberately lightweight. It stores identity
    and UI/document metadata but does not perform electrical calculations.
    """

    def __init__(
        self,
        equipment_id: str,
        equipment_type: str,
        *,
        name: Optional[str] = None,
        position: tuple[float, float] = (0.0, 0.0),
        properties: Optional[Dict[str, Any]] = None,
        terminal_ids: Optional[Iterable[str]] = None,
    ) -> None:
        if not equipment_id:
            raise ValueError("equipment_id must not be empty")

        if not equipment_type:
            raise ValueError("equipment_type must not be empty")

        if len(position) != 2:
            raise ValueError(
                "position must contain exactly two coordinates"
            )

        self._equipment_id = str(equipment_id)
        self._equipment_type = str(equipment_type)
        self._name = str(name) if name else self._equipment_id

        self._position = (
            float(position[0]),
            float(position[1]),
        )

        self._properties: Dict[str, Any] = dict(properties or {})

        self._terminal_ids = list(terminal_ids or [])

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def equipment_id(self) -> str:
        return self._equipment_id

    @property
    def equipment_type(self) -> str:
        return self._equipment_type

    # ------------------------------------------------------------------
    # Presentation identity
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value:
            raise ValueError("name must not be empty")

        self._name = str(value)

    # ------------------------------------------------------------------
    # Position
    # ------------------------------------------------------------------

    @property
    def position(self) -> tuple[float, float]:
        return self._position

    @position.setter
    def position(
        self,
        value: tuple[float, float],
    ) -> None:
        if len(value) != 2:
            raise ValueError(
                "position must contain exactly two coordinates"
            )

        self._position = (
            float(value[0]),
            float(value[1]),
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def properties(self) -> Dict[str, Any]:
        """
        Return the mutable equipment property dictionary.

        The dictionary belongs to the equipment object. Callers should
        modify it through controlled higher-level commands once the
        command/state system is integrated.
        """
        return self._properties

    def get_property(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self._properties.get(key, default)

    def set_property(
        self,
        key: str,
        value: Any,
    ) -> None:
        if not key:
            raise ValueError("property key must not be empty")

        self._properties[key] = value

    def remove_property(self, key: str) -> Any:
        return self._properties.pop(key)

    # ------------------------------------------------------------------
    # Terminals
    # ------------------------------------------------------------------

    @property
    def terminal_ids(self) -> tuple[str, ...]:
        return tuple(self._terminal_ids)

    def add_terminal(self, terminal_id: str) -> None:
        if not terminal_id:
            raise ValueError("terminal_id must not be empty")

        if terminal_id in self._terminal_ids:
            raise ValueError(
                f"Terminal already exists: {terminal_id}"
            )

        self._terminal_ids.append(terminal_id)

    def remove_terminal(self, terminal_id: str) -> None:
        try:
            self._terminal_ids.remove(terminal_id)
        except ValueError as exc:
            raise KeyError(terminal_id) from exc

    def has_terminal(self, terminal_id: str) -> bool:
        return terminal_id in self._terminal_ids

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the logical equipment state.

        This representation is intentionally independent of Qt objects.
        """
        return {
            "equipment_id": self.equipment_id,
            "equipment_type": self.equipment_type,
            "name": self.name,
            "position": list(self.position),
            "properties": dict(self.properties),
            "terminal_ids": list(self.terminal_ids),
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "EquipmentBase":
        """
        Reconstruct an EquipmentBase from serialized data.

        Concrete equipment factories may later provide specialized
        reconstruction for derived equipment classes.
        """
        return cls(
            equipment_id=str(data["equipment_id"]),
            equipment_type=str(data["equipment_type"]),
            name=str(
                data.get(
                    "name",
                    data["equipment_id"],
                )
            ),
            position=tuple(
                data.get(
                    "position",
                    (0.0, 0.0),
                )
            ),
            properties=dict(
                data.get(
                    "properties",
                    {},
                )
            ),
            terminal_ids=data.get(
                "terminal_ids",
                [],
            ),
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"equipment_id={self.equipment_id!r}, "
            f"equipment_type={self.equipment_type!r}, "
            f"name={self.name!r})"
        )
