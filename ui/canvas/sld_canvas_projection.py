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

from ui.equipment.symbol.symbol_base import SymbolBase
from ui.sld.sld_model import SLDConnection, SLDModel, SLDNode, SLDEndpoint, SLDRoute


@dataclass(frozen=True, slots=True)
class SLDCanvasNode:
    """Renderer-neutral visual input for one SLD node."""

    node_id: str
    equipment_id: str | None
    x: float
    y: float
    properties: Mapping[str, Any]
    presentation: SymbolBase | None = None


@dataclass(frozen=True, slots=True)
class SLDCanvasConnection:
    """Renderer-neutral visual input for one semantic SLD connection."""

    connection_id: str
    source_node_id: str
    target_node_id: str
    source_endpoint: SLDEndpoint | None
    target_endpoint: SLDEndpoint | None
    route: SLDRoute
    connection_kind: str | None
    presentation_owner: str | None
    projection_source: str | None
    properties: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class SLDCanvasSnapshot:
    """Immutable canvas projection of one SLD document model."""

    nodes: tuple[SLDCanvasNode, ...]
    connections: tuple[SLDCanvasConnection, ...]


@dataclass(frozen=True, slots=True)
class CompositeSLDCanvasSnapshot:
    """Complete visible SLD canvas state: committed plus uncommitted DraftNetwork presentation."""

    committed: SLDCanvasSnapshot
    draft: Any

    def __post_init__(self) -> None:
        object.__setattr__(self, "committed", self.committed)
        object.__setattr__(self, "draft", self.draft)


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
            presentation=(
                None
                if node.presentation is None
                else SymbolBase.from_dict(node.presentation.to_dict())
            ),
            properties=MappingProxyType(dict(node.properties)),
        )

    @staticmethod
    def _project_connection(connection: SLDConnection) -> SLDCanvasConnection:
        """Preserve the complete semantic/presentation connection descriptor."""
        properties = dict(connection.properties)
        return SLDCanvasConnection(
            connection_id=connection.connection_id,
            source_node_id=connection.source_node_id,
            target_node_id=connection.target_node_id,
            source_endpoint=connection.source_endpoint,
            target_endpoint=connection.target_endpoint,
            route=connection.route,
            connection_kind=SLDCanvasProjection._property_value(properties, "connection_kind", "kind"),
            presentation_owner=SLDCanvasProjection._property_value(properties, "presentation_owner", "owner"),
            projection_source=SLDCanvasProjection._property_value(properties, "projection_source", "source"),
            properties=MappingProxyType(properties),
        )

    @staticmethod
    def _property_value(properties: Mapping[str, Any], *names: str) -> str | None:
        """Read an existing persisted vocabulary without creating a new identity."""
        for name in names:
            value = properties.get(name)
            if value is not None:
                return str(value)
        return None


__all__ = [
    "SLDCanvasNode",
    "SLDCanvasConnection",
    "SLDCanvasSnapshot",
    "CompositeSLDCanvasSnapshot",
    "SLDCanvasProjection",
]
