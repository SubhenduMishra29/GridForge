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
# Does NOT:
#     - create QGraphicsItem objects;
#     - render symbols;
#     - connect equipment to the electrical Core;
#     - validate electrical topology.
# ============================================================

"""
GridForge V2 — Equipment Factory.
"""

from __future__ import annotations

from typing import Any, Mapping

from .equipment_base import EquipmentBase
from .equipment_registry import EquipmentRegistry


class EquipmentFactory:
    """
    Creates UI-side equipment objects using an
    EquipmentRegistry.
    """

    def __init__(
        self,
        registry: EquipmentRegistry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "registry must not be None."
            )

        if not isinstance(
            registry,
            EquipmentRegistry,
        ):
            raise TypeError(
                "registry must be an EquipmentRegistry."
            )

        self._registry = registry

    @property
    def registry(self) -> EquipmentRegistry:
        """Return the equipment-definition registry."""
        return self._registry

    def create(
        self,
        equipment_type: str,
        equipment_id: str,
        *,
        name: str | None = None,
        position: tuple[float, float] = (0.0, 0.0),
        properties: Mapping[str, Any] | None = None,
    ) -> EquipmentBase:
        """
        Create one logical equipment instance.

        Definition defaults are copied first, then instance
        properties are applied over those defaults.

        An explicitly supplied ``name`` is preserved. Only
        ``None`` causes the equipment ID to be used as the
        default name.
        """

        # ----------------------------------------------------
        # Identity validation
        # ----------------------------------------------------

        if (
            not isinstance(equipment_type, str)
            or not equipment_type.strip()
        ):
            raise ValueError(
                "equipment_type must be a "
                "non-empty string."
            )

        if (
            not isinstance(equipment_id, str)
            or not equipment_id.strip()
        ):
            raise ValueError(
                "equipment_id must be a "
                "non-empty string."
            )

        # ----------------------------------------------------
        # Property validation
        # ----------------------------------------------------

        if properties is not None and not isinstance(
            properties,
            Mapping,
        ):
            raise TypeError(
                "properties must be a mapping or None."
            )

        # ----------------------------------------------------
        # Definition lookup
        # ----------------------------------------------------

        definition = self._registry.require(
            equipment_type
        )

        # ----------------------------------------------------
        # Default properties
        # ----------------------------------------------------

        merged_properties = (
            definition.create_default_properties()
        )

        # ----------------------------------------------------
        # Instance overrides
        # ----------------------------------------------------

        if properties is not None:
            merged_properties.update(
                properties
            )

        # ----------------------------------------------------
        # Runtime terminal identities
        # ----------------------------------------------------

        terminal_ids = [
            f"{equipment_id}:{terminal_name}"
            for terminal_name
            in definition.terminal_names
        ]

        # ----------------------------------------------------
        # Equipment instance
        # ----------------------------------------------------

        return EquipmentBase(
            equipment_id=equipment_id,
            equipment_type=definition.equipment_type,
            name=(
                equipment_id
                if name is None
                else name
            ),
            position=position,
            properties=merged_properties,
            terminal_ids=terminal_ids,
        )


__all__ = [
    "EquipmentFactory",
]
