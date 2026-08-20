# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/equipment_factory.py
#
# Purpose:
#     Factory responsible for creating UI-side equipment
#     instances from registered equipment definitions.
#
# Architectural Role:
#     Separates equipment creation from:
#
#         - SLD controller
#         - tools
#         - canvas
#         - Qt graphics objects
#
# Responsibilities:
#     - resolve an equipment definition;
#     - generate/accept a stable equipment ID;
#     - construct EquipmentBase;
#     - apply default properties;
#     - apply caller-provided properties;
#     - construct terminal identifiers.
#
# Does NOT:
#     - create QGraphicsItem objects;
#     - render symbols;
#     - connect equipment to the electrical Core;
#     - validate electrical topology.
#
# Detailed Working:
#
#     Tool / Controller
#             |
#             | equipment_type
#             v
#     EquipmentFactory
#             |
#             v
#     EquipmentRegistry
#             |
#             v
#     EquipmentDefinition
#             |
#             v
#     EquipmentBase
#
# Later:
#
#     EquipmentBase
#          |
#          v
#     Item Factory / Adapter
#          |
#          v
#     QGraphicsItem
#
# ============================================================

"""
GridForge V2 — Equipment Factory.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .equipment_base import EquipmentBase
from .equipment_registry import EquipmentRegistry


class EquipmentFactory:
    """
    Creates UI-side equipment objects using an EquipmentRegistry.
    """

    def __init__(
        self,
        registry: EquipmentRegistry,
    ) -> None:
        if registry is None:
            raise ValueError("registry must not be None")

        self._registry = registry

    @property
    def registry(self) -> EquipmentRegistry:
        return self._registry

    def create(
        self,
        equipment_type: str,
        equipment_id: str,
        *,
        name: Optional[str] = None,
        position: tuple[float, float] = (0.0, 0.0),
        properties: Optional[Dict[str, Any]] = None,
    ) -> EquipmentBase:
        """
        Create one equipment instance.

        The factory performs definition lookup and combines the
        definition's default properties with instance-specific
        properties.

        Instance properties override defaults.
        """
        if not equipment_id:
            raise ValueError(
                "equipment_id must not be empty"
            )

        definition = self._registry.require(
            equipment_type
        )

        merged_properties = (
            definition.create_default_properties()
        )

        if properties:
            merged_properties.update(properties)

        terminal_ids = [
            f"{equipment_id}:{terminal_name}"
            for terminal_name in definition.terminal_names
        ]

        return EquipmentBase(
            equipment_id=equipment_id,
            equipment_type=definition.equipment_type,
            name=name or equipment_id,
            position=position,
            properties=merged_properties,
            terminal_ids=terminal_ids,
        )
