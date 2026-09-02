# ============================================================
# File: ui/canvas/sld_canvas_projection.py
# GridForge V2 — SLD Canvas Projection Boundary
# Author: Subhendu Mishra
# ============================================================
"""Translate the presentation-owned SLD model into canvas render input.

This boundary deliberately sits between SLD document structure and Canvas
rendering. It consumes only SLD data and produces immutable, renderer-neutral
snapshots. It never receives Core electrical objects and never mutates the
SLD document or the Core network.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from ui.sld.sld_model import SLDConnection, SLDModel, SLDNode


@dataclass(frozen=True, slots=True)
class SLDCanvasNode:
    """Renderer-neutral visual input for one SLD node."""

    node_id: str
    equipment_id: str | None
    x: float
    y: float
    properties: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class SLDCanvasConnection:
    """Renderer-neutral visual input for one SLD connection."""

    connection_id: str
    source_node_id: str
    target_node_id: str
    properties: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class SLDCanvasSnapshot:
    """Immutable canvas projection of one SLD document model."""

    nodes: tuple[SLDCanvasNode, ...]
    connections: tuple[SLDCanvasConnection, ...]


class SLDCanvasProjection:
    """Create renderer-neutral canvas input from an SLDModel."""

    def project(self, model: SLDModel) -> SLDCanvasSnapshot:
        """Project SLD document structure without touching Core state."""
        if not isinstance(model, SLDModel):
            raise TypeError("model must be an SLDModel.")

        nodes = tuple(self._project_node(node) for node in model.nodes)
        connections = tuple(
            self._project_connection(connection)
            for connection in model.connections
        )
        return SLDCanvasSnapshot(nodes=nodes, connections=connections)

    @staticmethod
    def _project_node(node: SLDNode) -> SLDCanvasNode:
        return SLDCanvasNode(
            node_id=node.node_id,
            equipment_id=node.equipment_id,
            x=node.x,
            y=node.y,
            properties=MappingProxyType(dict(node.properties)),
        )

    @staticmethod
    def _project_connection(connection: SLDConnection) -> SLDCanvasConnection:
        return SLDCanvasConnection(
            connection_id=connection.connection_id,
            source_node_id=connection.source_node_id,
            target_node_id=connection.target_node_id,
            properties=MappingProxyType(dict(connection.properties)),
        )


__all__ = [
    "SLDCanvasNode",
    "SLDCanvasConnection",
    "SLDCanvasSnapshot",
    "SLDCanvasProjection",
]
