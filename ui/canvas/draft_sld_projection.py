# ============================================================
# GridForge V2 — Draft SLD Presentation Projection
# ============================================================
"""Project Application-owned DraftNetwork state into immutable SLD canvas data.

This module is presentation-only. It never creates Core objects, QGraphicsItems,
or a second canvas. DraftNetwork is read through the Application boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from core.application.draft.network import DraftEndpointReference
from core.application.events import DraftChanged, ProjectClosed, ProjectLoaded


def _freeze(value: Any) -> Any:
    """Recursively freeze presentation mappings and collections."""
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze(v) for v in value)
    return value


@dataclass(frozen=True, slots=True)
class DraftSLDCanvasNode:
    draft_id: str
    equipment_type: str
    display_name: str
    x: float
    y: float
    rotation: float
    terminal_roles: tuple[str, ...]
    presentation: Mapping[str, Any]
    validation_state: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "terminal_roles", tuple(str(v) for v in self.terminal_roles))
        object.__setattr__(self, "presentation", _freeze(dict(self.presentation)))
        object.__setattr__(self, "validation_state", _freeze(dict(self.validation_state)))


@dataclass(frozen=True, slots=True)
class DraftSLDCanvasConnection:
    connection_id: str
    source: DraftEndpointReference
    target: DraftEndpointReference
    connection_kind: str
    route: tuple[tuple[float, float], ...]
    validation_state: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", DraftEndpointReference.from_value(self.source))
        object.__setattr__(self, "target", DraftEndpointReference.from_value(self.target))
        object.__setattr__(
            self,
            "route",
            tuple((float(point[0]), float(point[1])) for point in self.route),
        )
        object.__setattr__(self, "validation_state", _freeze(dict(self.validation_state)))


@dataclass(frozen=True, slots=True)
class DraftSLDCanvasSnapshot:
    nodes: tuple[DraftSLDCanvasNode, ...]
    connections: tuple[DraftSLDCanvasConnection, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "connections", tuple(self.connections))


class DraftSLDProjection:
    """Application/UI presentation projection for the authoritative DraftNetwork."""

    event_types = (DraftChanged, ProjectLoaded, ProjectClosed)

    def __init__(self, *, application: Any) -> None:
        if application is None or not callable(getattr(application, "read_draft_network", None)):
            raise TypeError("application must expose read_draft_network().")
        self._application = application
        self._snapshot = DraftSLDCanvasSnapshot(nodes=(), connections=())
        self._disposed = False

    @property
    def snapshot(self) -> DraftSLDCanvasSnapshot:
        return self._snapshot

    def project(self) -> DraftSLDCanvasSnapshot:
        """Read and deterministically project the current DraftNetwork."""
        data = self._application.read_draft_network()
        if data is None:
            self._snapshot = DraftSLDCanvasSnapshot(nodes=(), connections=())
            return self._snapshot

        equipment = tuple(
            sorted(
                tuple(data.get("equipment", ())),
                key=lambda item: str(item.get("draft_id", "")),
            )
        )
        connections = tuple(
            sorted(
                tuple(data.get("connections", ())),
                key=lambda item: str(item.get("connection_id", "")),
            )
        )

        nodes: list[DraftSLDCanvasNode] = []
        for item in equipment:
            placement = item.get("placement")
            if placement is None:
                continue
            presentation = dict(item.get("presentation", {}))
            rotation = presentation.get("rotation", presentation.get("orientation", 0.0))
            nodes.append(
                DraftSLDCanvasNode(
                    draft_id=str(item["draft_id"]),
                    equipment_type=str(item["equipment_type"]),
                    display_name=str(item.get("display_name") or item["equipment_type"]),
                    x=float(placement[0]),
                    y=float(placement[1]),
                    rotation=float(rotation or 0.0),
                    terminal_roles=tuple(str(v) for v in item.get("terminal_contract", ())),
                    presentation=presentation,
                    validation_state=dict(item.get("validation_state", {})),
                )
            )

        draft_connections: list[DraftSLDCanvasConnection] = []
        for item in connections:
            route_data = item.get("route", {})
            points = ()
            if isinstance(route_data, Mapping):
                points = route_data.get("points", ())
            elif isinstance(route_data, (tuple, list)):
                points = route_data
            draft_connections.append(
                DraftSLDCanvasConnection(
                    connection_id=str(item["connection_id"]),
                    source=DraftEndpointReference.from_value(item["source"]),
                    target=DraftEndpointReference.from_value(item["target"]),
                    connection_kind=str(item.get("connection_kind", "simple_wire")),
                    route=tuple(points),
                    validation_state=dict(item.get("validation_state", {})),
                )
            )

        self._snapshot = DraftSLDCanvasSnapshot(
            nodes=tuple(nodes),
            connections=tuple(draft_connections),
        )
        return self._snapshot

    def refresh(self, event: Any) -> None:
        if self._disposed:
            return
        if not isinstance(event, self.event_types):
            return
        self.project()

    def dispose(self) -> None:
        self._snapshot = DraftSLDCanvasSnapshot(nodes=(), connections=())
        self._disposed = True


__all__ = [
    "DraftSLDCanvasNode",
    "DraftSLDCanvasConnection",
    "DraftSLDCanvasSnapshot",
    "DraftSLDProjection",
]
