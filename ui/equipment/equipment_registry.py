# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/equipment_registry.py
#
# Purpose:
#     Registry of available SLD equipment definitions.
#
# Architectural Role:
#     Provides one authoritative UI-side lookup mechanism for
#     equipment TYPE definitions.
#
# Responsibilities:
#     - register equipment definitions;
#     - remove definitions;
#     - look up definitions;
#     - test equipment availability;
#     - enumerate available equipment types.
#
# Does NOT:
#     - create QGraphicsItems;
#     - render symbols;
#     - maintain document instances;
#     - perform electrical calculations.
#
# Detailed Working:
#
#     EquipmentDefinition
#             |
#             v
#     EquipmentRegistry
#             |
#       +-----+------+
#       |            |
#       v            v
#    Factory      UI/tool menus
#       |
#       v
#    EquipmentBase
#
# ============================================================

"""
GridForge V2 — Equipment Registry.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .equipment_definition import EquipmentDefinition


class EquipmentRegistry:
    """
    Registry containing available equipment type definitions.
    """

    def __init__(self) -> None:
        self._definitions: Dict[
            str,
            EquipmentDefinition,
        ] = {}

    def register(
        self,
        definition: EquipmentDefinition,
    ) -> None:
        equipment_type = definition.equipment_type

        if equipment_type in self._definitions:
            raise ValueError(
                f"Equipment type already registered: "
                f"{equipment_type}"
            )

        self._definitions[equipment_type] = definition

    def unregister(
        self,
        equipment_type: str,
    ) -> EquipmentDefinition:
        definition = self._definitions.pop(
            equipment_type,
            None,
        )

        if definition is None:
            raise KeyError(equipment_type)

        return definition

    def get(
        self,
        equipment_type: str,
    ) -> Optional[EquipmentDefinition]:
        return self._definitions.get(equipment_type)

    def require(
        self,
        equipment_type: str,
    ) -> EquipmentDefinition:
        definition = self.get(equipment_type)

        if definition is None:
            raise KeyError(
                f"Unknown equipment type: {equipment_type}"
            )

        return definition

    def contains(
        self,
        equipment_type: str,
    ) -> bool:
        return equipment_type in self._definitions

    def definitions(
        self,
    ) -> Iterable[EquipmentDefinition]:
        return tuple(self._definitions.values())

    def equipment_types(self) -> tuple[str, ...]:
        return tuple(self._definitions.keys())

    def clear(self) -> None:
        self._definitions.clear()

    def __len__(self) -> int:
        return len(self._definitions)

    def __contains__(self, equipment_type: str) -> bool:
        return self.contains(equipment_type)
