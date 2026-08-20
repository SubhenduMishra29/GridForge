# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/equipment_manager.py
#
# Purpose:
#     Runtime manager for UI-side SLD equipment instances.
#
# Architectural Role:
#     EquipmentManager owns the collection of equipment instances
#     that currently belong to an SLD document/model.
#
#     It is deliberately separate from:
#
#         EquipmentRegistry
#             -> owns EQUIPMENT TYPE definitions
#
#         EquipmentFactory
#             -> CREATES equipment instances
#
#         EquipmentBase
#             -> represents ONE equipment instance
#
#         EquipmentTerminal
#             -> represents ONE logical connection endpoint
#
#     The manager therefore acts as the runtime instance boundary.
#
# Detailed Working:
#
#     EquipmentDefinition
#             |
#             v
#     EquipmentRegistry
#             |
#             v
#     EquipmentFactory
#             |
#             v
#     EquipmentBase
#             |
#             v
#     EquipmentManager
#        /          \
#       v            v
#   Equipment     Equipment
#   Instance       Instance
#       |              |
#       v              v
#   Terminals       Terminals
#
#     The SLD document/model can use EquipmentManager to:
#
#         - add equipment;
#         - remove equipment;
#         - retrieve equipment by stable ID;
#         - determine whether an equipment ID exists;
#         - enumerate current equipment;
#         - clear the current equipment collection.
#
# Architectural Boundary:
#
#     EquipmentManager is NOT the electrical network engine.
#
#     It does not:
#
#         - calculate Y-bus;
#         - validate electrical topology;
#         - create Core network elements;
#         - establish electrical connections;
#         - create QGraphicsItems;
#         - render symbols.
#
#     It stores UI-side SLD instances so that higher-level SLD
#     controllers/models can coordinate them.
#
# Identity Rule:
#
#     equipment_id is the authoritative runtime identity.
#
#     Two equipment instances with the same equipment_id cannot
#     coexist in one EquipmentManager.
#
# Future Relationship:
#
#     EquipmentManager
#          |
#          +----> ConnectionManager
#          |
#          +----> SelectionModel
#          |
#          +----> SLD serialization
#          |
#          +----> Canvas synchronization
#
# ============================================================

"""
GridForge V2 — Equipment Manager.

Runtime collection of logical SLD equipment instances.

This module is intentionally Qt-independent.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .equipment_base import EquipmentBase


class EquipmentManager:
    """
    Owns the runtime collection of SLD equipment instances.

    The manager is document/model infrastructure.  It does not create
    equipment itself; construction remains the responsibility of
    :class:`EquipmentFactory`.
    """

    def __init__(self) -> None:
        self._equipment: Dict[str, EquipmentBase] = {}

    # ------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------

    def add(
        self,
        equipment: EquipmentBase,
    ) -> None:
        """
        Add one equipment instance to the current SLD model.

        Equipment identity is determined exclusively by
        ``equipment.equipment_id``.
        """
        if equipment is None:
            raise ValueError(
                "equipment must not be None"
            )

        equipment_id = equipment.equipment_id

        if equipment_id in self._equipment:
            raise ValueError(
                f"Equipment already exists: {equipment_id}"
            )

        self._equipment[equipment_id] = equipment

    def remove(
        self,
        equipment_id: str,
    ) -> EquipmentBase:
        """
        Remove and return one equipment instance.

        The manager does not automatically remove connections or
        graphics objects. Those responsibilities belong to the
        higher-level SLD/model coordination layer.
        """
        try:
            return self._equipment.pop(equipment_id)
        except KeyError as exc:
            raise KeyError(
                f"Unknown equipment: {equipment_id}"
            ) from exc

    # ------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------

    def get(
        self,
        equipment_id: str,
    ) -> Optional[EquipmentBase]:
        """
        Return an equipment instance or ``None`` if it is absent.
        """
        return self._equipment.get(equipment_id)

    def require(
        self,
        equipment_id: str,
    ) -> EquipmentBase:
        """
        Return an equipment instance.

        Raises:
            KeyError:
                If the equipment does not exist.
        """
        equipment = self.get(equipment_id)

        if equipment is None:
            raise KeyError(
                f"Unknown equipment: {equipment_id}"
            )

        return equipment

    def contains(
        self,
        equipment_id: str,
    ) -> bool:
        """
        Return whether an equipment instance exists.
        """
        return equipment_id in self._equipment

    # ------------------------------------------------------------
    # Enumeration
    # ------------------------------------------------------------

    def equipment(
        self,
    ) -> Iterable[EquipmentBase]:
        """
        Return a stable snapshot of current equipment instances.

        A tuple is returned so callers cannot mutate the manager's
        internal dictionary through the returned collection.
        """
        return tuple(self._equipment.values())

    def equipment_ids(self) -> tuple[str, ...]:
        """
        Return all current equipment identifiers.
        """
        return tuple(self._equipment.keys())

    # ------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------

    def clear(self) -> None:
        """
        Remove all equipment instances from the manager.

        This affects only the UI-side equipment collection.
        """
        self._equipment.clear()

    def __len__(self) -> int:
        return len(self._equipment)

    def __contains__(
        self,
        equipment_id: str,
    ) -> bool:
        return self.contains(equipment_id)
