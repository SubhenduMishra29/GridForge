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
#     - create equipment instances;
#     - create QGraphicsItems;
#     - render symbols;
#     - maintain document instances;
#     - perform electrical calculations;
#     - validate electrical topology.
#
# ============================================================

"""
GridForge V2 — Equipment Registry.

Qt-independent registry of available SLD equipment definitions.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .equipment_definition import EquipmentDefinition


class EquipmentRegistry:
    """
    Registry containing available equipment type definitions.

    EquipmentRegistry owns TYPE metadata only.

    It does not own runtime equipment instances. Those belong to
    EquipmentManager.
    """

    def __init__(self) -> None:
        self._definitions: Dict[
            str,
            EquipmentDefinition,
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        definition: EquipmentDefinition,
    ) -> None:
        """
        Register one equipment definition.

        Duplicate equipment types are rejected.
        """

        if definition is None:
            raise ValueError(
                "definition must not be None"
            )

        if not isinstance(
            definition,
            EquipmentDefinition,
        ):
            raise TypeError(
                "definition must be an "
                "EquipmentDefinition instance"
            )

        equipment_type = definition.equipment_type

        if equipment_type in self._definitions:
            raise ValueError(
                f"Equipment type already registered: "
                f"{equipment_type}"
            )

        self._definitions[
            equipment_type
        ] = definition

    # ========================================================
    # REMOVAL
    # ========================================================

    def unregister(
        self,
        equipment_type: str,
    ) -> EquipmentDefinition:
        """
        Remove and return an equipment definition.

        Raises:
            KeyError:
                If the equipment type is not registered.
        """

        definition = self._definitions.pop(
            equipment_type,
            None,
        )

        if definition is None:
            raise KeyError(
                equipment_type
            )

        return definition

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        equipment_type: str,
    ) -> Optional[EquipmentDefinition]:
        """
        Return a definition or None when absent.
        """

        return self._definitions.get(
            equipment_type
        )

    def require(
        self,
        equipment_type: str,
    ) -> EquipmentDefinition:
        """
        Return a registered definition.

        Raises:
            KeyError:
                If the equipment type is unknown.
        """

        definition = self.get(
            equipment_type
        )

        if definition is None:
            raise KeyError(
                f"Unknown equipment type: "
                f"{equipment_type}"
            )

        return definition

    def contains(
        self,
        equipment_type: str,
    ) -> bool:
        """
        Return whether an equipment type is registered.
        """

        return equipment_type in self._definitions

    # ========================================================
    # ENUMERATION
    # ========================================================

    def definitions(
        self,
    ) -> Iterable[EquipmentDefinition]:
        """
        Return a stable snapshot of all definitions.
        """

        return tuple(
            self._definitions.values()
        )

    def equipment_types(
        self,
    ) -> tuple[str, ...]:
        """
        Return all registered equipment type identifiers.
        """

        return tuple(
            self._definitions.keys()
        )

    # ========================================================
    # COLLECTION MANAGEMENT
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all equipment type definitions.
        """

        self._definitions.clear()

    # ========================================================
    # PROTOCOL HELPERS
    # ========================================================

    def __len__(
        self,
    ) -> int:
        return len(
            self._definitions
        )

    def __contains__(
        self,
        equipment_type: str,
    ) -> bool:
        return self.contains(
            equipment_type
        )
