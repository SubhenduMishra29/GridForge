# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/connection.py
#
# Purpose:
#     Logical representation of a connection between two SLD
#     equipment terminals.
#
# Architectural Role:
#     Connection is the UI-side/document representation of an
#     electrical SLD connection.
#
#     It provides the stable logical relationship between:
#
#         Equipment A -> Terminal A
#                    |
#                    | Connection
#                    |
#         Equipment B -> Terminal B
#
#     The connection is deliberately independent of Qt graphics.
#
# Detailed Working:
#
#     EquipmentBase
#          |
#          +---- EquipmentTerminal
#                         |
#                         | terminal_id
#                         v
#                    Connection
#                         ^
#                         |
#                         | terminal_id
#                         |
#          +---- EquipmentTerminal
#          |
#     EquipmentBase
#
#     The canvas may later display this logical connection through
#     LineItem / LineRenderer, but the graphics object is NOT the
#     source of truth.
#
# Responsibilities:
#     - maintain stable connection identity;
#     - identify source equipment and terminal;
#     - identify target equipment and terminal;
#     - store connection metadata;
#     - provide serialization;
#     - provide endpoint identity helpers.
#
# Does NOT:
#     - create QGraphicsLineItem;
#     - draw the connection;
#     - route the visual line;
#     - validate electrical topology;
#     - calculate electrical quantities;
#     - modify Core network objects.
#
# Architectural Boundary:
#
#     Connection
#         = logical/document relationship
#
#     LineItem
#         = Qt/canvas representation
#
#     LineRenderer
#         = visual rendering
#
#     Core topology
#         = authoritative electrical network semantics
#
#     These layers must not be conflated.
#
# Identity:
#
#     connection_id must be unique within one SLD document.
#
# Endpoint Identity:
#
#     An endpoint is represented by:
#
#         equipment_id
#         terminal_id
#
#     Example:
#
#         T1:HV
#         BUS1:PORT1
#
#     The connection therefore remains valid independently of
#     equipment graphics, zoom, pan, canvas position, or renderer.
#
# Future Relationship:
#
#     Connection
#          |
#          +---- ConnectionManager
#          |
#          +---- SLDModel
#          |
#          +---- LineItem
#          |
#          +---- LineRenderer
#          |
#          +---- Core synchronization
#
# ============================================================

"""
GridForge V2 — SLD Connection.

Qt-independent logical representation of an SLD connection.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple


class EquipmentConnection:
    """
    Logical connection between two equipment terminals.

    A connection stores endpoint identities only.  It does not own
    terminal objects and does not perform topology validation.

    Endpoint representation:

        (equipment_id, terminal_id)
    """

    def __init__(
        self,
        connection_id: str,
        source_equipment_id: str,
        source_terminal_id: str,
        target_equipment_id: str,
        target_terminal_id: str,
        *,
        properties: Dict[str, Any] | None = None,
    ) -> None:
        if not connection_id:
            raise ValueError(
                "connection_id must not be empty"
            )

        if not source_equipment_id:
            raise ValueError(
                "source_equipment_id must not be empty"
            )

        if not source_terminal_id:
            raise ValueError(
                "source_terminal_id must not be empty"
            )

        if not target_equipment_id:
            raise ValueError(
                "target_equipment_id must not be empty"
            )

        if not target_terminal_id:
            raise ValueError(
                "target_terminal_id must not be empty"
            )

        self._connection_id = str(connection_id)

        self._source_equipment_id = str(
            source_equipment_id
        )

        self._source_terminal_id = str(
            source_terminal_id
        )

        self._target_equipment_id = str(
            target_equipment_id
        )

        self._target_terminal_id = str(
            target_terminal_id
        )

        self._properties: Dict[str, Any] = dict(
            properties or {}
        )

    # ------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------

    @property
    def connection_id(self) -> str:
        return self._connection_id

    # ------------------------------------------------------------
    # Source endpoint
    # ------------------------------------------------------------

    @property
    def source_equipment_id(self) -> str:
        return self._source_equipment_id

    @property
    def source_terminal_id(self) -> str:
        return self._source_terminal_id

    @property
    def source_endpoint(self) -> Tuple[str, str]:
        """
        Return the source endpoint as:

            (equipment_id, terminal_id)
        """
        return (
            self.source_equipment_id,
            self.source_terminal_id,
        )

    # ------------------------------------------------------------
    # Target endpoint
    # ------------------------------------------------------------

    @property
    def target_equipment_id(self) -> str:
        return self._target_equipment_id

    @property
    def target_terminal_id(self) -> str:
        return self._target_terminal_id

    @property
    def target_endpoint(self) -> Tuple[str, str]:
        """
        Return the target endpoint as:

            (equipment_id, terminal_id)
        """
        return (
            self.target_equipment_id,
            self.target_terminal_id,
        )

    # ------------------------------------------------------------
    # Endpoint helpers
    # ------------------------------------------------------------

    @property
    def endpoints(
        self,
    ) -> Tuple[Tuple[str, str], Tuple[str, str]]:
        """
        Return both connection endpoints.

        The order is:

            source, target
        """
        return (
            self.source_endpoint,
            self.target_endpoint,
        )

    def connects_equipment(
        self,
        equipment_id: str,
    ) -> bool:
        """
        Return whether this connection references the equipment.
        """
        return (
            self.source_equipment_id == equipment_id
            or self.target_equipment_id == equipment_id
        )

    def connects_terminal(
        self,
        equipment_id: str,
        terminal_id: str,
    ) -> bool:
        """
        Return whether this connection references the specified
        equipment terminal.
        """
        endpoint = (
            equipment_id,
            terminal_id,
        )

        return endpoint in self.endpoints

    def contains_endpoint(
        self,
        endpoint: Tuple[str, str],
    ) -> bool:
        """
        Return whether the specified endpoint participates in this
        connection.
        """
        return endpoint in self.endpoints

    # ------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------

    @property
    def properties(self) -> Dict[str, Any]:
        """
        Return connection metadata.

        The dictionary is intentionally UI/document metadata and
        does not represent electrical calculations.
        """
        return self._properties

    def get_property(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self._properties.get(
            key,
            default,
        )

    def set_property(
        self,
        key: str,
        value: Any,
    ) -> None:
        if not key:
            raise ValueError(
                "property key must not be empty"
            )

        self._properties[key] = value

    def remove_property(
        self,
        key: str,
    ) -> Any:
        return self._properties.pop(key)

    # ------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the logical connection state.

        No Qt or renderer state is included.
        """
        return {
            "connection_id": self.connection_id,
            "source_equipment_id": (
                self.source_equipment_id
            ),
            "source_terminal_id": (
                self.source_terminal_id
            ),
            "target_equipment_id": (
                self.target_equipment_id
            ),
            "target_terminal_id": (
                self.target_terminal_id
            ),
            "properties": dict(
                self.properties
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "EquipmentConnection":
        """
        Reconstruct a logical connection from serialized data.
        """
        return cls(
            connection_id=str(
                data["connection_id"]
            ),
            source_equipment_id=str(
                data["source_equipment_id"]
            ),
            source_terminal_id=str(
                data["source_terminal_id"]
            ),
            target_equipment_id=str(
                data["target_equipment_id"]
            ),
            target_terminal_id=str(
                data["target_terminal_id"]
            ),
            properties=dict(
                data.get(
                    "properties",
                    {},
                )
            ),
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"connection_id={self.connection_id!r}, "
            f"source={self.source_equipment_id!r}:"
            f"{self.source_terminal_id!r}, "
            f"target={self.target_equipment_id!r}:"
            f"{self.target_terminal_id!r})"
        )
