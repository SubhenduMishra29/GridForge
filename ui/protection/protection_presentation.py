# ============================================================
# File: ui/protection/protection_presentation.py
# GridForge V2 — Protection Presentation Document
# Author: Subhendu Mishra
# ============================================================
"""Renderer-neutral authored Protection workspace presentation state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class ProtectionPresentationDocument:
    """Persistent Protection presentation state; never an electrical authority."""

    schema: int = 1
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    connections: dict[str, dict[str, Any]] = field(default_factory=dict)

    def node(self, object_id: str, *, default_x: float = 0.0, default_y: float = 0.0) -> dict[str, Any]:
        value = self.nodes.setdefault(
            str(object_id),
            {"object_id": str(object_id), "x": float(default_x), "y": float(default_y), "rotation": 0.0},
        )
        return value

    def set_node_position(self, object_id: str, x: float, y: float) -> None:
        node = self.node(object_id)
        node["x"] = float(x)
        node["y"] = float(y)

    def set_connection_route(self, connection_id: str, route: list[tuple[float, float]]) -> None:
        self.connections[str(connection_id)] = {
            "connection_id": str(connection_id),
            "route": [[float(x), float(y)] for x, y in route],
        }

    def clear(self) -> None:
        self.nodes.clear()
        self.connections.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "nodes": [dict(value) for value in self.nodes.values()],
            "connections": [dict(value) for value in self.connections.values()],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "ProtectionPresentationDocument":
        if data is None:
            return cls()
        if not isinstance(data, Mapping):
            raise TypeError("Protection presentation payload must be a mapping.")
        schema = int(data.get("schema", 1))
        if schema != 1:
            raise ValueError(f"Unsupported Protection presentation schema: {schema!r}")
        document = cls(schema=schema)
        for item in data.get("nodes", ()):
            if not isinstance(item, Mapping) or not str(item.get("object_id", "")).strip():
                raise ValueError("Protection presentation node requires object_id.")
            object_id = str(item["object_id"])
            document.nodes[object_id] = {
                "object_id": object_id,
                "x": float(item.get("x", 0.0)),
                "y": float(item.get("y", 0.0)),
                "rotation": float(item.get("rotation", 0.0)),
            }
        for item in data.get("connections", ()):
            if not isinstance(item, Mapping) or not str(item.get("connection_id", "")).strip():
                raise ValueError("Protection presentation connection requires connection_id.")
            connection_id = str(item["connection_id"])
            route = item.get("route", ())
            document.connections[connection_id] = {
                "connection_id": connection_id,
                "route": [[float(point[0]), float(point[1])] for point in route],
            }
        return document


__all__ = ["ProtectionPresentationDocument"]
