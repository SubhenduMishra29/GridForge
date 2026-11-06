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

from core.application.read_models import ElementReadModel, StudyResultReadModel

from ui.equipment.symbol.symbol_base import SymbolBase
from ui.sld.sld_model import SLDAnnotationBlock, SLDConnection, SLDModel, SLDNode, SLDEndpoint, SLDRoute
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
class SLDCanvasAnnotation:
    """Resolved presentation text sourced only from an Application read model."""

    block_id: str
    node_id: str
    x: float
    y: float
    text: str
    visible: bool


@dataclass(frozen=True, slots=True)
class SLDCanvasSnapshot:
    """Immutable canvas projection of one SLD document model."""

    nodes: tuple[SLDCanvasNode, ...]
    connections: tuple[SLDCanvasConnection, ...]
    annotations: tuple[SLDCanvasAnnotation, ...] = ()


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
        self._study_result: StudyResultReadModel | None = None

    def set_study_result(self, result: StudyResultReadModel | None) -> bool:
        """Set the selected Application result and report whether the canvas must refresh."""
        if result is not None and not isinstance(result, StudyResultReadModel):
            raise TypeError("result must be a StudyResultReadModel or None")
        previous = self._study_result
        self._study_result = result
        if previous is None or result is None:
            return previous is not result
        return not (
            previous.study_id == result.study_id
            and previous.source_revision == result.source_revision
            and previous.status == result.status
            and previous.current == result.current
            and previous.study_type == result.study_type
            and previous.value is result.value
        )

    def project(
        self,
        model: SLDModel,
        annotation_blocks: tuple[SLDAnnotationBlock, ...] | list[SLDAnnotationBlock] = (),
    ) -> SLDCanvasSnapshot:
        """Project SLD structure and resolve annotation values from Application read models."""
        if not isinstance(model, SLDModel):
            raise TypeError("model must be an SLDModel.")
        nodes = tuple(self._project_node(node) for node in model.nodes)
        connections = tuple(self._project_connection(connection) for connection in model.connections)
        nodes_by_id = {node.node_id: node for node in nodes}
        annotations = tuple(self._project_annotation(block, nodes_by_id) for block in annotation_blocks)
        annotations += self._project_study_result_annotations(nodes, self._study_result)
        return SLDCanvasSnapshot(nodes=nodes, connections=connections, annotations=annotations)

    @staticmethod
    def _project_annotation(
        block: SLDAnnotationBlock,
        nodes_by_id: Mapping[str, SLDCanvasNode],
    ) -> SLDCanvasAnnotation:
        if not isinstance(block, SLDAnnotationBlock):
            raise TypeError("annotation_blocks must contain SLDAnnotationBlock values.")
        node = nodes_by_id.get(block.node_id)
        if node is None:
            raise ValueError("Annotation block references an absent SLD node: " + block.node_id)
        read_model = node.read_model
        lines: list[str] = []
        if read_model is not None:
            for field in block.fields:
                if field == "identity":
                    value, label = read_model.object_id, "ID"
                elif field == "type":
                    value, label = read_model.element_type, "Type"
                elif field.startswith("label:"):
                    label = field[6:]
                    value = read_model.labels.get(label)
                elif field.startswith("attribute:"):
                    label = field[10:]
                    value = read_model.attributes.get(label)
                elif field.startswith("parameter:"):
                    label = field[10:]
                    parameter = next(
                        (item for item in read_model.engineering_parameters if item.parameter_id == label),
                        None,
                    )
                    value = None if parameter is None else parameter.value
                    if parameter is not None and parameter.unit and value is not None:
                        value = f"{value} {parameter.unit}"
                else:
                    continue
                if value is not None:
                    lines.append(f"{label}: {value}")
        return SLDCanvasAnnotation(
            block_id=block.block_id,
            node_id=block.node_id,
            x=node.x + block.offset_x,
            y=node.y + block.offset_y,
            text="\n".join(lines),
            visible=block.visible and bool(lines),
        )

    @staticmethod
    def _project_study_result_annotations(
        nodes: tuple[SLDCanvasNode, ...],
        result: StudyResultReadModel | None,
    ) -> tuple[SLDCanvasAnnotation, ...]:
        """Overlay current successful power-flow voltages without changing the SLD document."""
        if (
            result is None
            or result.status != "completed"
            or not result.current
            or result.study_type != "power_flow"
        ):
            return ()

        value = result.value
        numerical_result = getattr(value, "numerical_result", value)
        if not bool(getattr(numerical_result, "success", False)):
            return ()

        engineering_buses = tuple(getattr(value, "buses", ()))
        if engineering_buses:
            result_rows = tuple(
                (
                    getattr(bus, "bus_id", None),
                    getattr(bus, "voltage_pu", None),
                    getattr(bus, "angle_deg", None),
                )
                for bus in engineering_buses
            )
        else:
            bus_ids = tuple(getattr(numerical_result, "bus_ids", ()))
            magnitudes = tuple(getattr(numerical_result, "voltage_magnitudes", ()))
            angles = tuple(getattr(numerical_result, "voltage_angles", ()))
            if not bus_ids or len(bus_ids) != len(magnitudes) or len(bus_ids) != len(angles):
                return ()
            result_rows = tuple(zip(bus_ids, magnitudes, angles))

        nodes_by_bus_id = {
            node.equipment_id: node
            for node in nodes
            if node.equipment_id
            and node.read_model is not None
            and str(node.read_model.element_type).strip().lower() == "bus"
        }
        overlays: list[SLDCanvasAnnotation] = []
        for bus_id, magnitude, angle in result_rows:
            if bus_id is None or magnitude is None or angle is None:
                continue
            try:
                magnitude_value = float(magnitude)
                angle_value = float(angle)
            except (TypeError, ValueError):
                continue
            node = nodes_by_bus_id.get(str(bus_id))
            if node is None:
                continue
            overlays.append(
                SLDCanvasAnnotation(
                    block_id=f"__study_result__:{result.study_id}:{node.node_id}",
                    node_id=node.node_id,
                    x=node.x + 70.0,
                    y=node.y + 20.0,
                    text=f"Study V: {magnitude_value:.5f} pu\nAngle: {angle_value:.3f} deg",
                    visible=True,
                )
            )
        return tuple(overlays)

    def _project_node(self, node: SLDNode) -> SLDCanvasNode:
        read_model = None
        projection_errors: dict[str, str] = {}
        if self._read_model_provider is not None and node.equipment_id:
            try:
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
            except Exception as exc:
                # A stale/unavailable Application projection for one object
                # must not prevent unrelated SLD nodes from being rendered.
                # Keep the failure attached to this presentation snapshot; the
                # renderer can use legacy semantic properties when available
                # and report a node-local realization diagnostic otherwise.
                read_model = None
                projection_errors["_projection_read_model_error"] = (
                    f"{type(exc).__name__}: {exc}"
                )
        # Persisted presentation is user-editable presentation data, not
        # electrical truth. A malformed/obsolete symbol payload must not abort
        # projection of every other node in the document. Leave the presentation
        # absent so SemanticPresentationRealization can rebuild the canonical
        # symbol from the Application read model and equipment registry.
        properties = dict(node.properties)
        properties.update(projection_errors)
        presentation = None
        if node.presentation is not None:
            try:
                presentation = SymbolBase.from_dict(node.presentation.to_dict())
            except Exception as exc:
                properties["_projection_presentation_error"] = (
                    f"{type(exc).__name__}: {exc}"
                )

        return SLDCanvasNode(
            node_id=node.node_id,
            equipment_id=node.equipment_id,
            x=node.x,
            y=node.y,
            presentation=presentation,
            properties=_freeze_projection_value(properties),
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
    "SLDCanvasAnnotation",
    "SLDCanvasSnapshot",
    "CompositeSLDCanvasSnapshot",
    "SLDCanvasProjection",
]
