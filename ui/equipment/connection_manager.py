# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/connection_manager.py
#
# Purpose:
#     Runtime manager for logical SLD equipment connections.
#
# Architectural Role:
#     ConnectionManager owns the collection of logical
#     EquipmentConnection instances belonging to the current
#     SLD document.
#
#     It provides stable lookup by:
#
#         - connection ID;
#         - equipment ID;
#         - terminal endpoint.
#
# Detailed Working:
#
#     EquipmentTerminal
#          |
#          | endpoint identity
#          v
#     EquipmentConnection
#          |
#          v
#     ConnectionManager
#          |
#          +------------------+
#          |                  |
#          v                  v
#     SLD Model          Canvas Adapter
#                              |
#                              v
#                         LineItem
#                              |
#                              v
#                         Renderer
#
# Responsibilities:
#     - add connections;
#     - remove connections;
#     - retrieve connections;
#     - determine whether a connection exists;
#     - enumerate connections;
#     - find connections involving equipment;
#     - find connections involving terminals;
#     - clear the connection collection.
#
# Does NOT:
#     - create QGraphicsItem objects;
#     - draw connection lines;
#     - route graphical lines;
#     - validate electrical topology;
#     - determine whether an electrical connection is legal;
#     - perform electrical calculations;
#     - modify Core network objects.
#
# Important Architectural Boundary:
#
#     ConnectionManager performs COLLECTION and LOOKUP.
#
#     It must not become the topology-validation engine.
#
#     Future topology validation belongs to the SLD connection/
#     topology subsystem and ultimately synchronizes with the
#     electrical Core.
#
# Identity Rule:
#
#     connection_id is unique inside one SLD document.
#
# Endpoint Rule:
#
#     An endpoint is represented by:
#
#         (equipment_id, terminal_id)
#
#     The manager indexes endpoints for lookup but does not own
#     EquipmentTerminal objects.
#
# Duplicate Endpoint Rule:
#
#     This manager deliberately does not reject multiple connections
#     involving the same endpoint.
#
#     Whether a terminal permits:
#
#         - one connection;
#         - multiple connections;
#         - bus-style fan-out;
#
#     is a topology/domain rule and must be handled elsewhere.
#
# ============================================================

"""
GridForge V2 — Connection Manager.

Qt-independent runtime collection of SLD connections.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Tuple

from .connection import EquipmentConnection


Endpoint = Tuple[str, str]


class ConnectionManager:
    """
    Owns logical SLD connection instances.

    The manager is intentionally limited to storage and lookup.
    Electrical topology rules are outside its responsibility.
    """

    def __init__(self) -> None:
        self._connections: Dict[
            str,
            EquipmentConnection,
        ] = {}

    # ------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------

    def add(
        self,
        connection: EquipmentConnection,
    ) -> None:
        """
        Add one connection to the current SLD model.

        Connection identity is determined by ``connection_id``.
        """
        if connection is None:
            raise ValueError(
                "connection must not be None"
            )

        connection_id = connection.connection_id

        if connection_id in self._connections:
            raise ValueError(
                f"Connection already exists: "
                f"{connection_id}"
            )

        self._connections[
            connection_id
        ] = connection

    def remove(
        self,
        connection_id: str,
    ) -> EquipmentConnection:
        """
        Remove and return one connection.
        """
        try:
            return self._connections.pop(
                connection_id
            )
        except KeyError as exc:
            raise KeyError(
                f"Unknown connection: {connection_id}"
            ) from exc

    # ------------------------------------------------------------
    # Lookup by identity
    # ------------------------------------------------------------

    def get(
        self,
        connection_id: str,
    ) -> Optional[EquipmentConnection]:
        """
        Return a connection or ``None`` if it does not exist.
        """
        return self._connections.get(
            connection_id
        )

    def require(
        self,
        connection_id: str,
    ) -> EquipmentConnection:
        """
        Return a connection or raise ``KeyError``.
        """
        connection = self.get(connection_id)

        if connection is None:
            raise KeyError(
                f"Unknown connection: {connection_id}"
            )

        return connection

    def contains(
        self,
        connection_id: str,
    ) -> bool:
        """
        Return whether a connection exists.
        """
        return connection_id in self._connections

    # ------------------------------------------------------------
    # Endpoint lookup
    # ------------------------------------------------------------

    def find_by_endpoint(
        self,
        equipment_id: str,
        terminal_id: str,
    ) -> tuple[EquipmentConnection, ...]:
        """
        Return all connections involving an endpoint.

        Multiple connections are intentionally supported here.

        Whether multiple connections are electrically legal is a
        separate topology rule.
        """
        endpoint: Endpoint = (
            equipment_id,
            terminal_id,
        )

        return tuple(
            connection
            for connection in self._connections.values()
            if connection.contains_endpoint(
                endpoint
            )
        )

    def find_by_equipment(
        self,
        equipment_id: str,
    ) -> tuple[EquipmentConnection, ...]:
        """
        Return all connections involving an equipment instance.
        """
        return tuple(
            connection
            for connection in self._connections.values()
            if connection.connects_equipment(
                equipment_id
            )
        )

    def find_between_endpoints(
        self,
        first_endpoint: Endpoint,
        second_endpoint: Endpoint,
    ) -> tuple[EquipmentConnection, ...]:
        """
        Return connections joining two endpoints.

        Connection direction is ignored for this lookup.

        Therefore:

            A -> B

        and:

            B -> A

        are considered the same endpoint pair for lookup purposes.
        """
        first = tuple(first_endpoint)
        second = tuple(second_endpoint)

        return tuple(
            connection
            for connection in self._connections.values()
            if (
                connection.source_endpoint == first
                and connection.target_endpoint == second
            )
            or (
                connection.source_endpoint == second
                and connection.target_endpoint == first
            )
        )

    # ------------------------------------------------------------
    # Enumeration
    # ------------------------------------------------------------

    def connections(
        self,
    ) -> Iterable[EquipmentConnection]:
        """
        Return a stable snapshot of all current connections.
        """
        return tuple(
            self._connections.values()
        )

    def connection_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return all current connection identifiers.
        """
        return tuple(
            self._connections.keys()
        )

    # ------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------

    def clear(self) -> None:
        """
        Remove all logical connections.
        """
        self._connections.clear()

    def __len__(self) -> int:
        return len(self._connections)

    def __contains__(
        self,
        connection_id: str,
    ) -> bool:
        return self.contains(
            connection_id
        )
