
### `ui/sld/sld_model.py`

"""
GridForge V2 — SLD Model.

The SLD model represents the UI-side structural description of a Single
Line Diagram.

It intentionally contains no Qt dependencies and performs no electrical
calculation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional


@dataclass
class SLDNode:
    """
    UI-side representation of an electrical element in an SLD.

    Parameters
    ----------
    node_id:
        Stable UI/document identifier.

    equipment_type:
        Logical equipment type, for example ``bus``, ``generator``,
        ``transformer`` or ``breaker``.

    position:
        Canvas-independent logical position represented as ``(x, y)``.

    properties:
        Presentation/configuration metadata owned by the UI document.
    """

    node_id: str
    equipment_type: str
    position: tuple[float, float] = (0.0, 0.0)
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id must not be empty")

        if not self.equipment_type:
            raise ValueError("equipment_type must not be empty")

        if len(self.position) != 2:
            raise ValueError("position must contain exactly two coordinates")

        self.position = (
            float(self.position[0]),
            float(self.position[1]),
        )


@dataclass
class SLDConnection:
    """
    UI-side representation of an SLD connection.

    Connections use stable node identifiers rather than retaining direct
    object references to nodes.
    """

    connection_id: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.connection_id:
            raise ValueError("connection_id must not be empty")

        if not self.source_id:
            raise ValueError("source_id must not be empty")

        if not self.target_id:
            raise ValueError("target_id must not be empty")

        if self.source_id == self.target_id:
            raise ValueError("source_id and target_id must be different")


class SLDModel:
    """
    Container for the structural contents of an SLD document.

    The model intentionally remains independent of Qt and the electrical
    Core engine.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, SLDNode] = {}
        self._connections: Dict[str, SLDConnection] = {}

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    def add_node(self, node: SLDNode) -> None:
        if node.node_id in self._nodes:
            raise ValueError(f"Node already exists: {node.node_id}")

        self._nodes[node.node_id] = node

    def remove_node(self, node_id: str) -> SLDNode:
        node = self._nodes.pop(node_id, None)

        if node is None:
            raise KeyError(node_id)

        related = [
            connection_id
            for connection_id, connection in self._connections.items()
            if connection.source_id == node_id
            or connection.target_id == node_id
        ]

        for connection_id in related:
            del self._connections[connection_id]

        return node

    def get_node(self, node_id: str) -> Optional[SLDNode]:
        return self._nodes.get(node_id)

    def nodes(self) -> Iterable[SLDNode]:
        return tuple(self._nodes.values())

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    def add_connection(self, connection: SLDConnection) -> None:
        if connection.connection_id in self._connections:
            raise ValueError(
                f"Connection already exists: {connection.connection_id}"
            )

        if not self.has_node(connection.source_id):
            raise KeyError(
                f"Source node does not exist: {connection.source_id}"
            )

        if not self.has_node(connection.target_id):
            raise KeyError(
                f"Target node does not exist: {connection.target_id}"
            )

        self._connections[connection.connection_id] = connection

    def remove_connection(self, connection_id: str) -> SLDConnection:
        connection = self._connections.pop(connection_id, None)

        if connection is None:
            raise KeyError(connection_id)

        return connection

    def get_connection(
        self,
        connection_id: str,
    ) -> Optional[SLDConnection]:
        return self._connections.get(connection_id)

    def connections(self) -> Iterable[SLDConnection]:
        return tuple(self._connections.values())

    def has_connection(self, connection_id: str) -> bool:
        return connection_id in self._connections

    # ------------------------------------------------------------------
    # Position
    # ------------------------------------------------------------------

    def set_node_position(
        self,
        node_id: str,
        position: tuple[float, float],
    ) -> None:
        node = self._nodes.get(node_id)

        if node is None:
            raise KeyError(node_id)

        if len(position) != 2:
            raise ValueError("position must contain exactly two coordinates")

        node.position = (
            float(position[0]),
            float(position[1]),
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "equipment_type": node.equipment_type,
                    "position": list(node.position),
                    "properties": dict(node.properties),
                }
                for node_id, node in self._nodes.items()
            },
            "connections": {
                connection_id: {
                    "connection_id": connection.connection_id,
                    "source_id": connection.source_id,
                    "target_id": connection.target_id,
                    "properties": dict(connection.properties),
                }
                for connection_id, connection in self._connections.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SLDModel":
        model = cls()

        for raw_node in data.get("nodes", {}).values():
            model.add_node(
                SLDNode(
                    node_id=str(raw_node["node_id"]),
                    equipment_type=str(raw_node["equipment_type"]),
                    position=tuple(raw_node.get("position", (0.0, 0.0))),
                    properties=dict(raw_node.get("properties", {})),
                )
            )

        for raw_connection in data.get("connections", {}).values():
            model.add_connection(
                SLDConnection(
                    connection_id=str(raw_connection["connection_id"]),
                    source_id=str(raw_connection["source_id"]),
                    target_id=str(raw_connection["target_id"]),
                    properties=dict(raw_connection.get("properties", {})),
                )
            )

        return model

    def clear(self) -> None:
        self._nodes.clear()
        self._connections.clear()

    def __len__(self) -> int:
        return len(self._nodes)

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def connection_count(self) -> int:
        return len(self._connections)
