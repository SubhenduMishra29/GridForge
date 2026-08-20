# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/__init__.py
#
# Purpose:
#     Public package boundary for the GridForge V2 equipment
#     subsystem.
#
# Architectural Role:
#     The equipment subsystem defines the logical UI-side
#     representation of electrical equipment used by the SLD.
#
# Responsibilities:
#     - expose the public equipment API;
#     - expose equipment instances;
#     - expose equipment definitions;
#     - expose the equipment registry;
#     - expose the equipment factory;
#     - expose the runtime equipment manager;
#     - expose logical equipment terminals.
#
# Does NOT:
#     - create Qt widgets;
#     - render equipment;
#     - perform electrical calculations;
#     - manipulate QGraphicsScene directly;
#     - own Core electrical-network state;
#     - validate electrical topology.
#
# ============================================================

"""
GridForge V2 — Equipment Subsystem.

The equipment package provides the logical UI-side abstraction for
electrical equipment displayed in the Single Line Diagram (SLD).

The subsystem deliberately remains independent of Qt, rendering,
and the authoritative GridForge Core network.
"""

from .equipment_base import EquipmentBase
from .equipment_definition import EquipmentDefinition
from .equipment_registry import EquipmentRegistry
from .equipment_factory import EquipmentFactory
from .equipment_manager import EquipmentManager
from .terminal import EquipmentTerminal

__all__ = [
    "EquipmentBase",
    "EquipmentDefinition",
    "EquipmentRegistry",
    "EquipmentFactory",
    "EquipmentManager",
    "EquipmentTerminal",
]
