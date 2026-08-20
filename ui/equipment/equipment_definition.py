# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/equipment_definition.py
#
# Purpose:
#     Immutable-style metadata describing an equipment type.
#
# Architectural Role:
#     Separates the definition of an equipment TYPE from an
#     individual equipment INSTANCE.
#
# Example:
#
#     Definition:
#         transformer
#         terminals = 4
#         symbol = transformer
#
#     Instance:
#         equipment_id = T1
#         name = Main Transformer
#         position = (500, 300)
#
# Responsibilities:
#     - identify equipment type;
#     - define display name;
#     - define terminal identifiers;
#     - define default properties;
#     - provide factory metadata.
#
# Does NOT:
#     - create graphics;
#     - calculate electrical parameters;
#     - validate network topology.
#
# ============================================================

"""
GridForge V2 — Equipment Definition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class EquipmentDefinition:
    """
    Static definition of an equipment type.

    Definitions are registry metadata, not individual SLD objects.
    """

    equipment_type: str

    display_name: str

    terminal_names: Tuple[str, ...] = ()

    symbol_id: str = ""

    default_properties: Dict[str, Any] = field(
        default_factory=dict
    )

    category: str = "electrical"

    def __post_init__(self) -> None:
        if not self.equipment_type:
            raise ValueError(
                "equipment_type must not be empty"
            )

        if not self.display_name:
            raise ValueError(
                "display_name must not be empty"
            )

        if not self.symbol_id:
            object.__setattr__(
                self,
                "symbol_id",
                self.equipment_type,
            )

        # Defensive copy because dictionaries are mutable even inside
        # an otherwise frozen dataclass.
        object.__setattr__(
            self,
            "default_properties",
            dict(self.default_properties),
        )

    @property
    def terminal_count(self) -> int:
        return len(self.terminal_names)

    def create_default_properties(self) -> Dict[str, Any]:
        """
        Return a fresh copy of the default property set.

        Each equipment instance receives its own dictionary.
        """
        return dict(self.default_properties)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "equipment_type": self.equipment_type,
            "display_name": self.display_name,
            "terminal_names": list(self.terminal_names),
            "symbol_id": self.symbol_id,
            "default_properties": dict(
                self.default_properties
            ),
            "category": self.category,
        }
