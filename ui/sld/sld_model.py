# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/sld/sld_model.py
#
# Purpose:
#     UI-side structural model for the GridForge Single Line
#     Diagram (SLD) subsystem.
#
# Architectural Role# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/sld/sld_model.py
#
# Purpose:
#     UI-side structural model for the GridForge Single Line
#     Diagram (SLD) subsystem.
#
# Architectural Role:
#     SLD is a first-class GridForge V2 UI capability. This file
#     defines the document-level visual structure represented by
#     the SLD without introducing Qt, rendering, or electrical
#     calculation responsibilities.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple


# ============================================================
# SLD Node
# ============================================================


@dataclass
class SLDNode:
    """
    Structural node in an SLD document.

    This is a UI/document representation only. It does not own
    the authoritative electrical equipment model.
    """

    node_id: str
    equipment_id: Optional[str] = None
    x: float = 0.0
    y: float = 0.0
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id:
            raise ValueError("node_id must be a non-empty string")

        if isinstance(self.x, bool) or not isinstance(self.x, (int, float)):
            raise TypeError("x must be numeric")

        if isinstance(self.y, bool) or not isinstance(self.y, (int, float)):
            raise TypeError("y must be numeric")

        self.node_id = str(self.node_id)

        if self.equipment_id is not None:
            self.equipment_id = str(self.equipment_id)

        self.x = float(self.x)
        self.y = float(self.y)

        self.properties = dict(self.properties)

    @property
    def position(self) -> Tuple[float, float]:
        """Return the logical SLD position."""
        return self.x, self.y

    def set_position(self, x: float, y: float) -> None:
        """Update the logical SLD position."""
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError("x must be numeric")

        if isinstance(y, bool) or not isinstance(y, (int, float)):
            raise TypeError("y must be numeric")

        self.x = float(x)
        self.y = float(y)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this node."""
        return {
            "node_id": self.node_id,
            "equipment_id": self.equipment_id,
            "x": self.x,
            "y": self.y,
            "properties": dict(self.properties),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SLDNode":
        """Deserialize an SLD node."""
        return cls(
            node_id=str(data["node_id"]),
            equipment_id=(
                None
                if data.get("equipment_id") is None
                else str(data["equipment_id"])
            ),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            properties=dict(data.get("properties", {})),
        )


# ============================================================
# SLD Connection
# ============================================================


@dataclass
class SLDConnection:
    """
    Structural connection between two SLD nodes.

    This class represents document structure only. It does not
    validate or calculate electrical topology.
    """

    connection_id: str
    source_node_id: str
    target_node_id: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.connection_id, str) or not self.connection_id:
            raise ValueError("connection_id must be a non-empty string")

        if (
            not isinstance(self.source_node_id, str)
            or not self.source_node_id
        ):
            raise ValueError("source_node_id must be a non-empty string")

        if (
            not isinstance(self.target_node_id, str)
            or not self.target_node_id
        ):
            raise ValueError("target_node_id must be a non-empty string")

        self.connection_id = str(self.connection_id)
        self.source_node_id = str(self.source_node_id)
        self.target_node_id = str(self.target_node_id)
        self.properties = dict(self.properties)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this connection."""
        return {
            "connection_id": self.connection_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "properties": dict(self.properties),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SLDConnection":
        """Deserialize an SLD connection."""
        return cls(
            connection_id=str(data["connection_id"]),
            source_node_id=str(data["source_node_id"]),
            target_node_id=str(data["target_node_id"]),
            properties=dict(data.get("properties", {})),
        )


# ============================================================
# SLD Model
# ============================================================


class SLDModel:
    """
    Structural document model for an SLD.

    The model owns UI/document structure only.

    It does not:
        - perform electrical calculations;
        - own the authoritative Core network;
        - create Qt graphics objects;
        - render;
        - process input events;
        - execute tools;
        - perform solver operations.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, SLDNode] = {}
        self._connections: Dict[str, SLDConnection] = {}

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

    @property
    def nodes(self) -> Tuple[SLDNode, ...]:
        """Return an immutable snapshot of all nodes."""
        return tuple(self._nodes.values())

    @property
    def node_count(self) -> int:
        """Return the number of SLD nodes."""
        return len(self._nodes)

    def add_node(self, node: SLDNode) -> SLDNode:
        """Add a node to the model."""
        if not isinstance(node, SLDNode):
            raise TypeError("node must be an SLDNode")

        if node.node_id in self._nodes:
            raise ValueError(
                f"node already exists: {node.node_id!r}"
            )

        self._nodes[node.node_id] = node
        return node

    def create_node(
        self,
        node_id: str,
        equipment_id: Optional[str] = None,
        x: float = 0.0,
        y: float = 0.0,
        properties: Optional[Mapping[str, Any]] = None,
    ) -> SLDNode:
        """Create and add an SLD node."""
        node = SLDNode(
            node_id=node_id,
            equipment_id=equipment_id,
            x=x,
            y=y,
            properties=dict(properties or {}),
        )
        return self.add_node(node)

    def get_node(self, node_id: str) -> SLDNode:
        """Return a node or raise KeyError."""
        try:
            return self._nodes[node_id]
        except KeyError:
            raise KeyError(f"unknown node: {node_id!r}") from None

    def get_node_optional(self, node_id: str) -> Optional[SLDNode]:
        """Return a node or None."""
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        """Return whether a node exists."""
        return node_id in self._nodes

    def remove_node(self, node_id: str) -> SLDNode:
        """
        Remove a node.

        Connections referencing the removed node are also removed
        because they can no longer represent valid document
        structure.
        """
        node = self.get_node(node_id)

        connection_ids = [
            connection_id
            for connection_id, connection in self._connections.items()
            if (
                connection.source_node_id == node_id
                or connection.target_node_id == node_id
            )
        ]

        for connection_id in connection_ids:
            del self._connections[connection_id]

        del self._nodes[node_id]
        return node

    # --------------------------------------------------------
    # Connections
    # --------------------------------------------------------

    @property
    def connections(self) -> Tuple[SLDConnection, ...]:
        """Return an immutable snapshot of all connections."""
        return tuple(self._connections.values())

    @property
    def connection_count(self) -> int:
        """Return the number of SLD connections."""
        return len(self._connections)

    def add_connection(
        self,
        connection: SLDConnection,
    ) -> SLDConnection:
        """Add a connection to the model."""
        if not isinstance(connection, SLDConnection):
            raise TypeError("connection must be an SLDConnection")

        if connection.connection_id in self._connections:
            raise ValueError(
                f"connection already exists: "
                f"{connection.connection_id!r}"
            )

        if connection.source_node_id not in self._nodes:
            raise ValueError(
                f"unknown source node: "
                f"{connection.source_node_id!r}"
            )

        if connection.target_node_id not in self._nodes:
            raise ValueError(
                f"unknown target node: "
                f"{connection.target_node_id!r}"
            )

        self._connections[connection.connection_id] = connection
        return connection

    def create_connection(
        self,
        connection_id: str,
        source_node_id: str,
        target_node_id: str,
        properties: Optional[Mapping[str, Any]] = None,
    ) -> SLDConnection:
        """Create and add an SLD connection."""
        connection = SLDConnection(
            connection_id=connection_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            properties=dict(properties or {}),
        )
        return self.add_connection(connection)

    def get_connection(
        self,
        connection_id: str,
    ) -> SLDConnection:
        """Return a connection or raise KeyError."""
        try:
            return self._connections[connection_id]
        except KeyError:
            raise KeyError(
                f"unknown connection: {connection_id!r}"
            ) from None

    def get_connection_optional(
        self,
        connection_id: str,
    ) -> Optional[SLDConnection]:
        """Return a connection or None."""
        return self._connections.get(connection_id)

    def has_connection(self, connection_id: str) -> bool:
        """Return whether a connection exists."""
        return connection_id in self._connections

    def remove_connection(
        self,
        connection_id: str,
    ) -> SLDConnection:
        """Remove a connection."""
        connection = self.get_connection(connection_id)
        del self._connections[connection_id]
        return connection

    # --------------------------------------------------------
    # Model lifecycle
    # --------------------------------------------------------

    def clear(self) -> None:
        """Remove all nodes and connections."""
        self._nodes.clear()
        self._connections.clear()

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the complete SLD model."""
        return {
            "nodes": [
                node.to_dict()
                for node in self._nodes.values()
            ],
            "connections": [
                connection.to_dict()
                for connection in self._connections.values()
            ],
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "SLDModel":
        """Deserialize an SLD model."""
        model = cls()

        for node_data in data.get("nodes", []):
            model.add_node(
                SLDNode.from_dict(node_data)
            )

        for connection_data in data.get("connections", []):
            model.add_connection(
                SLDConnection.from_dict(connection_data)
            )

        return model

    # --------------------------------------------------------
    # Diagnostics
    # --------------------------------------------------------

    def get_state(self) -> Dict[str, Any]:
        """Return a diagnostic snapshot."""
        return {
            "node_count": self.node_count,
            "connection_count": self.connection_count,
            "node_ids": tuple(self._nodes.keys()),
            "connection_ids": tuple(self._connections.keys()),
        }

    def __repr__(self) -> str:
        return (
            f"SLDModel("
            f"nodes={self.node_count}, "
            f"connections={self.connection_count})"
        )
#     SLD is a first-class GridForge V2 UI capability. This file
#     defines the document-level visual structure represented by
#     the SLD without introducing Qt, rendering, or electrical
#     calculation responsibilities.
#
# Responsibilities:
#     - represent SLD nodes/equipment references;
#     - represent SLD connections;
#     - maintain stable UI identifiers;
#     - maintain logical positions;
#     - maintain UI/document properties;
#     - provide serialization boundaries.
#
# Does NOT:
#     - perform electrical calculations;
#     - execute power-flow/short-circuit/other analysis;
#     - create Qt graphics objects;
#     - render symbols;
#     - process mouse/keyboard events;
#     - replace the Core electrical network model.
#
# Relationship:
#
#     SLDDocument
#          |
#          v
#      SLDModel
#       /    \
#      v      v
#    Nodes  Connections
#       |
#       v
#    Canvas / Items / Renderers
#
# Important Boundary:
#     The SLD model is a UI/document representation. The Core
#     remains authoritative for electrical-engine data and
#     calculations. Synchronization will be introduced through
#     the appropriate controller/adapter layer.
#
# ============================================================
