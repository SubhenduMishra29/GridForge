# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/model/sld_model.py
#
# Purpose:
#     Central logical document model for the GridForge V2
#     Single Line Diagram (SLD).
#
# Architectural Role:
#     SLDModel is the UI-side/document source of truth for the
#     current SLD structure.
#
#     It brings together:
#
#         EquipmentManager
#         ConnectionManager
#
#     while remaining completely independent of Qt graphics.
#
# Detailed Working:
#
#                 SLDModel
#                    |
#          +---------+---------+
#          |                   |
#          v                   v
#    EquipmentManager    ConnectionManager
#          |                   |
#          v                   v
#    EquipmentBase       EquipmentConnection
#          |                   |
#          v                   v
#    EquipmentTerminal  Endpoint references
#
#                    |
#                    v
#             SLD Controllers
#                    |
#                    v
#               Canvas Layer
#                    |
#          +---------+---------+
#          |                   |
#          v                   v
#      QGraphicsItem       LineItem
#
# IMPORTANT:
#
#     The Canvas is NOT the source of truth.
#
#     QGraphicsScene/QGraphicsItem objects are visual projections
#     of this model.
#
# Responsibilities:
#     - own the current SLD equipment collection;
#     - own the current SLD connection collection;
#     - provide stable lookup;
#     - provide model-level add/remove operations;
#     - provide serialization/deserialization;
#     - expose document-level state.
#
# Does NOT:
#     - create QGraphicsItem objects;
#     - render equipment;
#     - handle mouse events;
#     - perform canvas navigation;
#     - perform electrical calculations;
#     - directly manipulate Core network objects;
#     - perform renderer operations.
#
# Architectural Boundary:
#
#     SLDModel
#          |
#          +---- logical document state
#          |
#          +---- equipment
#          |
#          +---- connections
#
#     Canvas
#          |
#          +---- visual projection of SLDModel
#
#     Core
#          |
#          +---- authoritative electrical semantics
#
#     Synchronization between UI model and Core must occur through
#     an explicit controller/adapter boundary, not inside this
#     model.
#
# Identity:
#
#     Equipment IDs and connection IDs must be unique within this
#     SLD document.
#
# Connection Safety:
#
#     This model verifies that referenced equipment and terminals
#     exist before accepting a connection.
#
#     It deliberately does NOT decide whether the connection is
#     electrically valid. That remains the responsibility of the
#     topology/domain layer.
#
# ============================================================

"""
GridForge V2 — SLD Model.

Qt-independent document model for the Single Line Diagram.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ui.equipment.connection import EquipmentConnection
from ui.equipment.connection_manager import ConnectionManager
from ui.equipment.equipment_base import EquipmentBase
from ui.equipment.equipment_manager import EquipmentManager


class SLDModel:
    """
    Logical document model representing one GridForge SLD.

    The model owns document-level logical state but remains completely
    independent of Qt and rendering.
    """

    def __init__(self) -> None:
        self._equipment = EquipmentManager()
        self._connections = ConnectionManager()

    # ------------------------------------------------------------
    # Managers
    # ------------------------------------------------------------

    @property
    def equipment(self) -> EquipmentManager:
        """
        Return the equipment manager.

        The manager is the authoritative collection of equipment
        instances inside this SLD document.
        """
        return self._equipment

    @property
    def connections(self) -> ConnectionManager:
        """
        Return the connection manager.

        The manager is the authoritative collection of logical
        SLD connections inside this document.
        """
        return self._connections

    # ------------------------------------------------------------
    # Equipment operations
    # ------------------------------------------------------------

    def add_equipment(
        self,
        equipment: EquipmentBase,
    ) -> None:
        """
        Add one equipment instance to the SLD.
        """
        self._equipment.add(equipment)

    def remove_equipment(
        self,
        equipment_id: str,
    ) -> EquipmentBase:
        """
        Remove an equipment instance.

        Connections involving that equipment are intentionally
        removed first so the resulting model cannot contain
        dangling endpoint references.

        This is document consistency management, not electrical
        topology validation.
        """
        related_connections = (
            self._connections.find_by_equipment(
                equipment_id
            )
        )

        for connection in related_connections:
            self._connections.remove(
                connection.connection_id
            )

        return self._equipment.remove(
            equipment_id
        )

    def get_equipment(
        self,
        equipment_id: str,
    ) -> Optional[EquipmentBase]:
        """
        Return an equipment instance or ``None``.
        """
        return self._equipment.get(
            equipment_id
        )

    def require_equipment(
        self,
        equipment_id: str,
    ) -> EquipmentBase:
        """
        Return an equipment instance or raise ``KeyError``.
        """
        return self._equipment.require(
            equipment_id
        )

    # ------------------------------------------------------------
    # Connection operations
    # ------------------------------------------------------------

    def add_connection(
        self,
        connection: EquipmentConnection,
    ) -> None:
        """
        Add a logical connection after verifying its endpoint
        references.

        This checks document consistency only.

        It does NOT perform electrical topology validation.
        """
        self.require_equipment(
            connection.source_equipment_id
        )

        self.require_equipment(
            connection.target_equipment_id
        )

        source_equipment = self.require_equipment(
            connection.source_equipment_id
        )

        target_equipment = self.require_equipment(
            connection.target_equipment_id
        )

        if not source_equipment.has_terminal(
            connection.source_terminal_id
        ):
            raise KeyError(
                "Unknown source terminal: "
                f"{connection.source_equipment_id}:"
                f"{connection.source_terminal_id}"
            )

        if not target_equipment.has_terminal(
            connection.target_terminal_id
        ):
            raise KeyError(
                "Unknown target terminal: "
                f"{connection.target_equipment_id}:"
                f"{connection.target_terminal_id}"
            )

        self._connections.add(
            connection
        )

    def remove_connection(
        self,
        connection_id: str,
    ) -> EquipmentConnection:
        """
        Remove one logical connection.
        """
        return self._connections.remove(
            connection_id
        )

    def get_connection(
        self,
        connection_id: str,
    ) -> Optional[EquipmentConnection]:
        """
        Return a connection or ``None``.
        """
        return self._connections.get(
            connection_id
        )

    def require_connection(
        self,
        connection_id: str,
    ) -> EquipmentConnection:
        """
        Return a connection or raise ``KeyError``.
        """
        return self._connections.require(
            connection_id
        )

    # ------------------------------------------------------------
    # Document state
    # ------------------------------------------------------------

    @property
    def equipment_count(self) -> int:
        return len(self._equipment)

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    def clear(self) -> None:
        """
        Clear the complete logical SLD document.

        This removes connections and equipment from the UI-side
        document model only.
        """
        self._connections.clear()
        self._equipment.clear()

    # ------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the complete SLD document.

        Only logical/document state is serialized. Qt graphics
        objects and renderer state are deliberately excluded.
        """
        return {
            "equipment": [
                equipment.to_dict()
                for equipment
                in self._equipment.equipment()
            ],
            "connections": [
                connection.to_dict()
                for connection
                in self._connections.connections()
            ],
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "SLDModel":
        """
        Reconstruct an SLD model from serialized logical state.

        Equipment is restored before connections because connection
        endpoints depend on equipment and terminal identities.
        """
        model = cls()

        for equipment_data in data.get(
            "equipment",
            [],
        ):
            equipment = EquipmentBase.from_dict(
                equipment_data
            )

            model.add_equipment(
                equipment
            )

        for connection_data in data.get(
            "connections",
            [],
        ):
            connection = EquipmentConnection.from_dict(
                connection_data
            )

            model.add_connection(
                connection
            )

        return model

    # ------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"equipment_count={self.equipment_count}, "
            f"connection_count={self.connection_count})"
        )
