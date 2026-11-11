# ============================================================
# File: core/application/commands/sld_commands.py
# GridForge V2 — Immutable SLD presentation commands
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from uuid import UUID, uuid4
import math

from ..command import Command


SET_SLD_NODE_POSITION = "sld.set_node_position"
SET_SLD_NODE_POSITIONS = "sld.set_node_positions"
SET_SLD_NODE_TRANSFORMS = "sld.set_node_transforms"
ADD_SLD_NODE = "sld.add_node"
REMOVE_SLD_NODE = "sld.remove_node"
DELETE_SLD_SELECTION = "sld.delete_selection"
SET_SLD_NODE_PRESENTATION = "sld.set_node_presentation"
ADD_SLD_CONNECTION = "sld.add_connection"
REMOVE_SLD_CONNECTION = "sld.remove_connection"
SET_SLD_CONNECTION_ROUTE = "sld.set_connection_route"
SET_SLD_NODE_PROPERTIES = "sld.set_node_properties"
SET_SLD_ANNOTATION_BLOCKS = "sld.set_annotation_blocks"
CREATE_SLD_LAYER = "sld.create_layer"
UPDATE_SLD_LAYER = "sld.update_layer"
DELETE_SLD_LAYER = "sld.delete_layer"
REORDER_SLD_LAYERS = "sld.reorder_layers"


class CreateSLDLayerCommand(Command):
    def __init__(self, *, layer_id: str, name: str, visible: bool = True, locked: bool = False, opacity: float = 1.0, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if not isinstance(layer_id, str) or not layer_id.strip() or not isinstance(name, str) or not name.strip():
            raise ValueError("layer_id and name must be non-empty strings.")
        if not isinstance(visible, bool) or not isinstance(locked, bool):
            raise TypeError("visible and locked must be boolean.")
        if isinstance(opacity, bool) or not isinstance(opacity, (int, float)) or not math.isfinite(float(opacity)) or not 0.0 <= float(opacity) <= 1.0:
            raise ValueError("opacity must be finite and between 0 and 1.")
        super().__init__(command_type=CREATE_SLD_LAYER, payload={"layer_id": layer_id, "name": name, "visible": visible, "locked": locked, "opacity": float(opacity)}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class UpdateSLDLayerCommand(Command):
    def __init__(self, *, layer_id: str, name: str | None = None, visible: bool | None = None, locked: bool | None = None, opacity: float | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if not isinstance(layer_id, str) or not layer_id.strip():
            raise ValueError("layer_id must be a non-empty string.")
        updates = {key: value for key, value in {"name": name, "visible": visible, "locked": locked, "opacity": opacity}.items() if value is not None}
        if not updates:
            raise ValueError("At least one layer field must be updated.")
        if "name" in updates and (not isinstance(name, str) or not name.strip()):
            raise ValueError("name must be a non-empty string.")
        if "visible" in updates and not isinstance(visible, bool):
            raise TypeError("visible must be boolean.")
        if "locked" in updates and not isinstance(locked, bool):
            raise TypeError("locked must be boolean.")
        if "opacity" in updates and (isinstance(opacity, bool) or not isinstance(opacity, (int, float)) or not math.isfinite(float(opacity)) or not 0.0 <= float(opacity) <= 1.0):
            raise ValueError("opacity must be finite and between 0 and 1.")
        super().__init__(command_type=UPDATE_SLD_LAYER, payload={"layer_id": layer_id, "updates": updates}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class DeleteSLDLayerCommand(Command):
    def __init__(self, *, layer_id: str, reassign_to: str = "default", command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if not isinstance(layer_id, str) or not layer_id.strip() or not isinstance(reassign_to, str) or not reassign_to.strip():
            raise ValueError("layer_id and reassign_to must be non-empty strings.")
        if layer_id == "default":
            raise ValueError("The default SLD layer cannot be deleted.")
        if layer_id == reassign_to:
            raise ValueError("Deleted layer contents must be reassigned to a different layer.")
        super().__init__(command_type=DELETE_SLD_LAYER, payload={"layer_id": layer_id, "reassign_to": reassign_to}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class ReorderSLDLayersCommand(Command):
    def __init__(self, *, layer_ids: list[str] | tuple[str, ...], command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        ids = tuple(layer_ids)
        if not ids or any(not isinstance(value, str) or not value.strip() for value in ids) or len(set(ids)) != len(ids):
            raise ValueError("layer_ids must be a non-empty sequence of unique non-empty strings.")
        super().__init__(command_type=REORDER_SLD_LAYERS, payload={"layer_ids": ids}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)




class SetSLDNodePositionCommand(Command):
    def __init__(self, *, node_id: str, x: float, y: float,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(command_type=SET_SLD_NODE_POSITION,
                         payload={"node_id": node_id, "x": float(x), "y": float(y)},
                         command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class SetSLDNodePositionsCommand(Command):
    """Move multiple SLD nodes atomically as one undoable presentation command."""

    def __init__(
        self,
        *,
        positions: list[dict],
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(positions, list) or not positions:
            raise ValueError("positions must be a non-empty list.")
        normalized = []
        seen = set()
        for item in positions:
            if not isinstance(item, dict):
                raise TypeError("each position must be a dictionary.")
            node_id = item.get("node_id")
            if not isinstance(node_id, str) or not node_id.strip():
                raise ValueError("each position requires a non-empty node_id.")
            if node_id in seen:
                raise ValueError(f"duplicate node_id in group move: {node_id!r}.")
            seen.add(node_id)
            x, y = item.get("x"), item.get("y")
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in (x, y)):
                raise ValueError("group move coordinates must be finite numbers.")
            normalized.append({"node_id": node_id, "x": float(x), "y": float(y)})
        super().__init__(
            command_type=SET_SLD_NODE_POSITIONS,
            payload={"positions": normalized},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class SetSLDNodeTransformsCommand(Command):
    """Apply one atomic group transform to SLD presentation nodes."""

    def __init__(
        self,
        *,
        transforms: list[dict],
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(transforms, list) or not transforms:
            raise ValueError("transforms must be a non-empty list.")
        normalized = []
        seen = set()
        for item in transforms:
            if not isinstance(item, dict):
                raise TypeError("each transform must be a dictionary.")
            node_id = item.get("node_id")
            if not isinstance(node_id, str) or not node_id.strip():
                raise ValueError("each transform requires a non-empty node_id.")
            if node_id in seen:
                raise ValueError(f"duplicate node_id in group transform: {node_id!r}.")
            seen.add(node_id)
            x, y = item.get("x"), item.get("y")
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in (x, y)
            ):
                raise ValueError("group transform coordinates must be finite numbers.")
            presentation = item.get("presentation")
            if not isinstance(presentation, dict):
                raise TypeError("each group transform requires a presentation dictionary.")
            normalized.append({
                "node_id": node_id,
                "x": float(x),
                "y": float(y),
                "presentation": dict(presentation),
            })
        super().__init__(
            command_type=SET_SLD_NODE_TRANSFORMS,
            payload={"transforms": normalized},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class AddSLDNodeCommand(Command):
    def __init__(self, *, node_id: str, equipment_id: str | None = None,
                 x: float = 0.0, y: float = 0.0,
                 presentation_owner: str = "engineer",
                 projection_source: str | None = None,
                 element_type: str | None = None,
                 presentation: dict | None = None,
                 presentation_properties: dict | None = None,
                 presentation_rotation: float | None = None,
                 layer_id: str = "default",
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(
            command_type=ADD_SLD_NODE,
            payload={
                "node_id": node_id,
                "equipment_id": equipment_id,
                "x": float(x),
                "y": float(y),
                "presentation_owner": presentation_owner,
                "projection_source": projection_source,
                "element_type": element_type,
                "presentation": None if presentation is None else dict(presentation),
                "presentation_properties": {} if presentation_properties is None else dict(presentation_properties),
                "presentation_rotation": presentation_rotation,
                "layer_id": layer_id,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class SetSLDNodePresentationCommand(Command):
    def __init__(
        self,
        *,
        node_id: str,
        presentation: dict,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(presentation, dict):
            raise TypeError("presentation must be a dictionary")
        super().__init__(
            command_type=SET_SLD_NODE_PRESENTATION,
            payload={"node_id": node_id, "presentation": dict(presentation)},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class RemoveSLDNodeCommand(Command):
    def __init__(self, *, node_id: str, projection_source: str | None = None,
                 command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(
            command_type=REMOVE_SLD_NODE,
            payload={"node_id": node_id, "projection_source": projection_source},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteSLDSelectionCommand(Command):
    """Delete one typed SLD selection as a single undoable presentation command."""

    def __init__(
        self,
        *,
        node_ids: tuple[str, ...] | list[str] = (),
        connection_ids: tuple[str, ...] | list[str] = (),
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        nodes = tuple(node_ids)
        connections = tuple(connection_ids)
        if bool(nodes) == bool(connections):
            raise ValueError("Provide a non-empty node_ids or connection_ids selection, but not both.")
        for label, values in (("node_ids", nodes), ("connection_ids", connections)):
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"{label} must contain only non-empty strings.")
            if len(set(values)) != len(values):
                raise ValueError(f"{label} must not contain duplicate identities.")
        super().__init__(
            command_type=DELETE_SLD_SELECTION,
            payload={"node_ids": nodes, "connection_ids": connections},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class AddSLDConnectionCommand(Command):
    """Create one persistent SLD connection with explicit ownership contract."""

    def __init__(
        self,
        *,
        connection_id: str,
        source_node_id: str,
        target_node_id: str,
        source_endpoint: dict | None = None,
        target_endpoint: dict | None = None,
        route: dict | None = None,
        connection_kind: str | None = None,
        core_connection_id: str | None = None,
        presentation_owner: str = "engineer",
        projection_source: str | None = None,
        layer_id: str = "default",
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if presentation_owner not in {"engineer", "projection"}:
            raise ValueError("presentation_owner must be 'engineer' or 'projection'.")
        if projection_source is not None and presentation_owner != "projection":
            raise ValueError("projection_source requires presentation_owner='projection'.")
        super().__init__(
            command_type=ADD_SLD_CONNECTION,
            payload={
                "connection_id": connection_id,
                "source_node_id": source_node_id,
                "target_node_id": target_node_id,
                "source_endpoint": None if source_endpoint is None else dict(source_endpoint),
                "target_endpoint": None if target_endpoint is None else dict(target_endpoint),
                "route": None if route is None else dict(route),
                "connection_kind": connection_kind,
                "core_connection_id": core_connection_id,
                "presentation_owner": presentation_owner,
                "projection_source": projection_source,
                "layer_id": layer_id,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

class SetSLDNodePropertiesCommand(Command):
    def __init__(self, *, node_id: str, properties: dict,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(properties, dict):
            raise TypeError("properties must be a dictionary")
        super().__init__(command_type=SET_SLD_NODE_PROPERTIES,
                         payload={"node_id": node_id, "properties": dict(properties)},
                         command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class SetSLDAnnotationBlocksCommand(Command):
    """Replace the annotation-block collection through the Application transaction."""

    def __init__(self, *, annotation_blocks: list[dict],
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(annotation_blocks, list) or any(not isinstance(item, dict) for item in annotation_blocks):
            raise TypeError("annotation_blocks must be a list of dictionaries")
        super().__init__(
            command_type=SET_SLD_ANNOTATION_BLOCKS,
            payload={"annotation_blocks": [dict(item) for item in annotation_blocks]},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class SetSLDConnectionRouteCommand(Command):
    def __init__(self, *, connection_id: str, route: dict,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(route, dict):
            raise TypeError("route must be a dictionary")
        super().__init__(command_type=SET_SLD_CONNECTION_ROUTE,
                         payload={"connection_id": connection_id, "route": dict(route)},
                         command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class RemoveSLDConnectionCommand(Command):
    def __init__(self, *, connection_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=REMOVE_SLD_CONNECTION, payload={"connection_id": connection_id},
                         command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


__all__ = [
    "SET_SLD_NODE_POSITION", "SET_SLD_NODE_POSITIONS", "SET_SLD_NODE_TRANSFORMS", "ADD_SLD_NODE", "REMOVE_SLD_NODE", "SET_SLD_NODE_PRESENTATION",
    "ADD_SLD_CONNECTION", "REMOVE_SLD_CONNECTION", "SET_SLD_CONNECTION_ROUTE", "SET_SLD_NODE_PROPERTIES", "SET_SLD_ANNOTATION_BLOCKS", "DELETE_SLD_SELECTION", "CREATE_SLD_LAYER", "UPDATE_SLD_LAYER", "DELETE_SLD_LAYER", "REORDER_SLD_LAYERS",
    "SetSLDNodePositionCommand", "SetSLDNodePositionsCommand", "SetSLDNodeTransformsCommand", "AddSLDNodeCommand", "SetSLDNodePresentationCommand", "RemoveSLDNodeCommand",
    "AddSLDConnectionCommand", "SetSLDConnectionRouteCommand", "SetSLDNodePropertiesCommand", "RemoveSLDConnectionCommand", "SetSLDAnnotationBlocksCommand", "DeleteSLDSelectionCommand", "CreateSLDLayerCommand", "UpdateSLDLayerCommand", "DeleteSLDLayerCommand", "ReorderSLDLayersCommand",
]
