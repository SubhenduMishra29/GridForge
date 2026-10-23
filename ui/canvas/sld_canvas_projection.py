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
from typing import Any, Callable, Mapping

from core.application.read_models import ElementReadModel

from ui.equipment.symbol.symbol_base import SymbolBase
from ui.sld.sld_model import SLDConnection, SLDModel, SLDNode, SLDEndpoint, SLDRoute
from ui.canvas.draft_sld_projection import DraftSLDCanvasSnapshot


def _freeze_projection_value(value: Any) -> Any:
    """Detach supported property containers without coercing authored values."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_projection_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_projection_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_projection_value(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class SLDCanvasNode:
    """Renderer-neutral visual input for one SLD node."""

    node_id: str
    equipment_id: str | None
    x: float
    y: float
    properties: Mapping[str, Any]
    presentation: SymbolBase | None = None
    read_model: ElementReadModel | None = None


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
    draft: DraftSLDCanvasSnapshot

    def __post_init__(self) -> None:
        object.__setattr__(self, "committed", self.committed)
        object.__setattr__(self, "draft", self.draft)


class SLDCanvasProjection:
    """Create renderer-neutral canvas input from an SLDModel and current read projections."""

    def __init__(
        self,
        read_model_provider: Callable[[str], ElementReadModel | None] | None = None,
    ) -> None:
        if read_model_provider is not None and not callable(read_model_provider):
            raise TypeError("read_model_provider must be callable or None.")
        self._read_model_provider = read_model_provider

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

    def _project_node(self, node: SLDNode) -> SLDCanvasNode:
        read_model = None
        if self._read_model_provider is not None and node.equipment_id:
            read_model = self._read_model_provider(node.equipment_id)
            if read_model is not None:
                if not isinstance(read_model, ElementReadModel):
                    raise TypeError(
                        f"Read-model provider returned an unsupported value for {node.equipment_id!r}."
                    )
                if read_model.object_id != node.equipment_id:
                    raise ValueError(
                        f"Read-model provider identity mismatch for {node.equipment_id!r}."
                    )
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
            properties=_freeze_projection_value(node.properties),
            read_model=read_model,
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
            properties=_freeze_projection_value(properties),
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
