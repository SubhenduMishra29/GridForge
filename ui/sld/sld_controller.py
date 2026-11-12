# ============================================================
# GridForge V2
# ============================================================
# File: ui/sld/sld_controller.py
# Purpose: SLD document/state coordination and presentation edits.
# Author: Subhendu Mishra
# ============================================================
"""Controller for the presentation-owned SLD workflow.

The controller coordinates SLD document structure, presentation geometry and
interaction state. Electrical/domain mutations cross the Application command
boundary; document-owned presentation metadata is persisted by SLDDocument.
The controller never composes Application services.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Optional

from core.application import Application
from core.application.commands.selection_commands import DeleteSelectionBatchCommand
from core.application.commands.model_commands import DeleteBusCommand, DeleteTransformerCommand
from core.application.commands.breaker_commands import DeleteBreakerCommand
from core.application.commands.simple_wire_commands import RemoveSimpleWireConnectionCommand
from core.application.commands.draft_commands import RemoveDraftEquipmentCommand, RemoveDraftConnectionCommand
from core.application.events import ProjectClosed, ProjectLoaded
from core.application.commands.sld_commands import (
    AddSLDConnectionCommand,
    AddSLDNodeCommand,
    RemoveSLDConnectionCommand,
    RemoveSLDNodeCommand,
    SetSLDNodePositionCommand,
    SetSLDNodePresentationCommand,
    SetSLDNodePropertiesCommand,
    SetSLDAnnotationBlocksCommand,
    SetSLDConnectionRouteCommand,
    CreateSLDLayerCommand,
    UpdateSLDLayerCommand,
    DeleteSLDLayerCommand,
    ReorderSLDLayersCommand,
)

from .sld_document import SLDDocument
from .sld_model import SLDAnnotationBlock, SLDConnection, SLDNode
from .sld_projection_manager import SLDProjectionManager
from .sld_state import SLDState
from ui.workspace.project_workspace import ProjectWorkspaceLifecycle


class SLDController:
    """Application-facing controller for SLD document operations."""

    def __init__(
        self,
        state: Optional[SLDState] = None,
        projection_manager: Optional[SLDProjectionManager] = None,
        application: Optional[Application] = None,
        workspace_lifecycle: Optional[ProjectWorkspaceLifecycle] = None,
    ) -> None:
        if not isinstance(projection_manager, SLDProjectionManager):
            raise TypeError(
                "SLDController requires the canonical SLDProjectionManager "
                "from the Application read/projection composition."
            )
        self._state = state if state is not None else SLDState()
        self._projection_manager = projection_manager
        self._application = application
        self._workspace_lifecycle = workspace_lifecycle
        self._document_activation_handler = None
        self._active_layer_by_document: dict[str, str] = {}
        if self._application is not None:
            self._application.event_bus.subscribe(ProjectLoaded, self._on_project_loaded)
            self._application.event_bus.subscribe(ProjectClosed, self._on_project_closed)

    @property
    def state(self) -> SLDState:
        return self._state

    @property
    def application(self) -> Application:
        return self._require_application()

    def bind_workspace_lifecycle(
        self,
        lifecycle: ProjectWorkspaceLifecycle,
    ) -> None:
        """Bind the one canonical workspace lifecycle after UI composition.

        The composition graph creates SLDController before the workspace host
        can be realized. This explicit one-time binding completes that graph
        without creating a second controller or inferring lifecycle ownership.
        """
        if not isinstance(lifecycle, ProjectWorkspaceLifecycle):
            raise TypeError(
                "lifecycle must be the canonical ProjectWorkspaceLifecycle."
            )
        if self._workspace_lifecycle is lifecycle:
            return
        if self._workspace_lifecycle is not None:
            raise RuntimeError(
                "SLDController is already bound to a different ProjectWorkspaceLifecycle."
            )
        self._workspace_lifecycle = lifecycle

    def bind_document_activation_handler(self, handler: Any) -> None:
        """Bind document activation to the coordinated workspace transaction.

        The composition root supplies ProjectWorkspaceApplicationAdapter.activate_document
        so controller callers cannot bypass transition guards, presentation bridging,
        workspace publication, and projection reconciliation.
        """
        if not callable(handler):
            raise TypeError("document activation handler must be callable.")
        if self._document_activation_handler is handler:
            return
        if self._document_activation_handler is not None:
            raise RuntimeError("A document activation handler is already bound.")
        self._document_activation_handler = handler

    @property
    def active_document(self) -> Optional[SLDDocument]:
        lifecycle = self._workspace_lifecycle
        if lifecycle is None:
            presentation = self.application.presentation
            return presentation if isinstance(presentation, SLDDocument) else None
        document = lifecycle.documents.active_document
        if document is None:
            return None
        if not isinstance(document, SLDDocument):
            raise TypeError("The active workspace document is not an SLDDocument.")
        return document

    @property
    def document_manager(self):
        lifecycle = self._workspace_lifecycle
        return lifecycle.documents if lifecycle is not None else None

    def register_document(self, document: SLDDocument) -> None:
        """Compatibility adapter: registration belongs to ProjectWorkspaceLifecycle."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        lifecycle = self._workspace_lifecycle
        if lifecycle is None:
            raise RuntimeError("SLDController requires the canonical ProjectWorkspaceLifecycle.")
        existing = lifecycle.documents.get(document.document_id)
        if existing is None:
            lifecycle.documents.register(document)
        elif existing is not document:
            self._active_layer_by_document.pop(document.document_id, None)
            lifecycle.documents.replace(document)
        if lifecycle.documents.active_document_id == document.document_id:
            self.reconcile_presentation()

    def unregister_document(self, document_id: str) -> SLDDocument:
        lifecycle = self._require_workspace_lifecycle()
        document = lifecycle.documents.require(document_id)
        if not isinstance(document, SLDDocument):
            raise TypeError("Document is not an SLDDocument.")
        lifecycle.remove_document(document_id)
        self._active_layer_by_document.pop(document_id, None)
        return document

    def replace_document(self, document: SLDDocument) -> SLDDocument:
        """Compatibility adapter; project lifecycle owns replacement/activation."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        lifecycle = self._require_workspace_lifecycle()
        existing = lifecycle.documents.get(document.document_id)
        if existing is not document:
            self._active_layer_by_document.pop(document.document_id, None)
        lifecycle.replace_document(document)
        self.reconcile_presentation()
        return document

    def get_document(self, document_id: str) -> Optional[SLDDocument]:
        lifecycle = self._workspace_lifecycle
        if lifecycle is None:
            return None
        document = lifecycle.documents.get(document_id)
        return document if isinstance(document, SLDDocument) else None

    def activate_document(self, document_id: str) -> SLDDocument:
        """Request activation from the canonical workspace lifecycle."""
        lifecycle = self._require_workspace_lifecycle()
        document = lifecycle.documents.require(document_id)
        if not isinstance(document, SLDDocument):
            raise TypeError("Document is not an SLDDocument.")
        activation_handler = self._document_activation_handler
        if activation_handler is not None:
            activation_handler(document_id)
            # The workspace adapter publishes the committed transition; its
            # subscriber reconciles controller state and all document projections.
            if lifecycle.documents.active_document is not document:
                raise RuntimeError(
                    "Workspace activation completed without adopting the requested SLD document."
                )
            if self.application.presentation is not document:
                raise RuntimeError(
                    "Workspace activation completed without updating the Application presentation."
                )
        else:
            # Compatibility path for isolated controller compositions that have
            # not yet installed the workspace adapter.
            previous = lifecycle.documents.active_document_id
            if previous != document_id:
                lifecycle.activate_document_id(document_id)
                try:
                    self.application.activate_presentation(document)
                except BaseException:
                    if previous is not None:
                        lifecycle.documents.activate(previous)
                        previous_document = lifecycle.documents.active_document
                        if previous_document is not None:
                            try:
                                self.application.activate_presentation(previous_document)
                            except BaseException:
                                pass
                    raise
        self._state.active_document_id = document_id
        self._state.clear_selection()
        self._state.mark_clean() if not lifecycle.documents.is_dirty(document_id) else None
        if self.application.sld_service.document is not document:
            self.application.sld_service.bind_document(document)
        return document

    def reconcile_presentation(self) -> Optional[SLDDocument]:
        """Reconcile controller state to the canonical active workspace document."""
        document = self.active_document
        if document is None:
            self._state.reset()
            return None
        if self.application.presentation is not document:
            self.application.activate_presentation(document)
        self._state.active_document_id = document.document_id
        self._state.clear_selection()
        return document

    def _on_project_loaded(self, _event: ProjectLoaded) -> None:
        # Active-layer selection is transient UI state, not project persistence.
        # A newly loaded project may reuse document/layer IDs, so never carry
        # authoring selection across the project boundary.
        self._active_layer_by_document.clear()
        self.reconcile_presentation()

    def _on_project_closed(self, _event: ProjectClosed) -> None:
        self._active_layer_by_document.clear()
        self._state.reset()

    def dispose(self) -> None:
        if self._application is not None:
            self._application.event_bus.unsubscribe(ProjectLoaded, self._on_project_loaded)
            self._application.event_bus.unsubscribe(ProjectClosed, self._on_project_closed)
        self._active_layer_by_document.clear()
        self._state.reset()
        self._document_activation_handler = None

    @property
    def document_count(self) -> int:
        manager = self.document_manager
        return len(manager) if manager is not None else 0

    def _repair_active_layer_selection(self, document: SLDDocument) -> str | None:
        """Choose the first authorable layer, or clear transient selection if none exists."""
        candidates = sorted(
            (layer for layer in document.layers if layer.visible and not layer.locked),
            key=lambda layer: (layer.order, layer.layer_id),
        )
        if not candidates:
            self._active_layer_by_document.pop(document.document_id, None)
            return None
        layer_id = candidates[0].layer_id
        self._active_layer_by_document[document.document_id] = layer_id
        return layer_id

    @property
    def active_layer_id(self) -> str:
        """Transient authoring layer for the active SLD document."""
        document = self._require_active_document()
        active = self._active_layer_by_document.get(document.document_id)
        if active is not None and any(
            layer.layer_id == active and layer.visible and not layer.locked
            for layer in document.layers
        ):
            return active
        repaired = self._repair_active_layer_selection(document)
        if repaired is None:
            raise RuntimeError("No visible, unlocked SLD layer is available for authoring.")
        return repaired

    def set_active_layer(self, layer_id: str) -> None:
        document = self._require_active_document()
        layer = next((item for item in document.layers if item.layer_id == layer_id), None)
        if layer is None:
            raise KeyError(f"Unknown SLD layer: {layer_id}")
        if layer.locked or not layer.visible:
            raise ValueError("An SLD authoring layer must be visible and unlocked.")
        self._active_layer_by_document[document.document_id] = layer_id

    def _execute_layer_command(self, command: Any) -> None:
        self._require_active_document()
        result = self.application.execute(command)
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def create_layer(self, *, layer_id: str, name: str, opacity: float = 1.0) -> None:
        self._execute_layer_command(CreateSLDLayerCommand(layer_id=layer_id, name=name, opacity=opacity))
        self._active_layer_by_document[self._require_active_document().document_id] = layer_id

    def update_layer(self, layer_id: str, **changes: Any) -> None:
        self._execute_layer_command(UpdateSLDLayerCommand(layer_id=layer_id, **changes))
        document = self._require_active_document()
        selected = self._active_layer_by_document.get(document.document_id)
        if selected == layer_id:
            self._repair_active_layer_selection(document)

    def delete_layer(self, layer_id: str, *, reassign_to: str = "default") -> None:
        self._execute_layer_command(DeleteSLDLayerCommand(layer_id=layer_id, reassign_to=reassign_to))
        document = self._require_active_document()
        if self._active_layer_by_document.get(document.document_id) == layer_id:
            target = next((layer for layer in document.layers if layer.layer_id == reassign_to), None)
            if target is not None and target.visible and not target.locked:
                self._active_layer_by_document[document.document_id] = reassign_to
            else:
                self._repair_active_layer_selection(document)

    def reorder_layers(self, layer_ids: list[str] | tuple[str, ...]) -> None:
        self._execute_layer_command(ReorderSLDLayersCommand(layer_ids=layer_ids))

    def add_node(self, node: SLDNode) -> None:
        document = self._require_active_document()
        layer_id = node.layer_id if node.layer_id != "default" else self.active_layer_id
        if not any(layer.layer_id == layer_id and not layer.locked for layer in document.layers):
            raise ValueError("The target SLD layer is missing or locked.")
        result = self.application.execute(AddSLDNodeCommand(
            node_id=node.node_id, equipment_id=node.equipment_id, x=node.x, y=node.y, layer_id=layer_id,
        ))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def set_node_presentation(self, node_id: str, presentation: Any) -> None:
        """Persist a presentation-only symbol change through Application history."""
        self._require_active_document()
        result = self.application.execute(
            SetSLDNodePresentationCommand(
                node_id=node_id,
                presentation=presentation.to_dict()
                if callable(getattr(presentation, "to_dict", None))
                else dict(presentation),
            )
        )
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def set_node_properties(self, node_id: str, properties: Dict[str, Any]) -> None:
        self._require_active_document()
        result = self.application.execute(SetSLDNodePropertiesCommand(node_id=node_id, properties=properties))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def set_annotation_blocks(self, annotation_blocks: list[dict[str, Any]]) -> None:
        """Persist annotation edits through Application history on their owning layers.

        New blocks without an explicit layer inherit the active authoring layer.
        Existing blocks retain their current layer when callers submit legacy
        payloads without layer_id. Locked-layer content is immutable, including
        deletion through this full-replacement API.
        """
        document = self._require_active_document()
        if not isinstance(annotation_blocks, list):
            raise TypeError("annotation_blocks must be supplied as a list.")
        existing = {block.block_id: block for block in document.annotation_blocks}
        proposed: list[dict[str, Any]] = []
        proposed_ids: set[str] = set()
        active_layer_id = self.active_layer_id
        layers = {layer.layer_id: layer for layer in document.layers}
        for value in annotation_blocks:
            if callable(getattr(value, "to_dict", None)):
                payload = value.to_dict()
            elif isinstance(value, dict):
                payload = dict(value)
            else:
                raise TypeError("Each annotation block must be a mapping or SLDAnnotationBlock.")
            block_id = payload.get("block_id")
            if not isinstance(block_id, str) or not block_id.strip():
                raise ValueError("Annotation block requires a non-empty block_id.")
            if block_id in proposed_ids:
                raise ValueError("Duplicate SLD annotation block ID: " + block_id)
            proposed_ids.add(block_id)
            current = existing.get(block_id)
            if "layer_id" not in payload:
                payload["layer_id"] = (
                    current.layer_id if current is not None else active_layer_id
                )
            elif current is None and payload["layer_id"] == "default":
                # Match equipment/wire authoring: Default means the current
                # authoring layer for newly created visual objects.
                payload["layer_id"] = active_layer_id
            normalized = SLDAnnotationBlock.from_dict(payload)
            payload = normalized.to_dict()
            layer = layers.get(normalized.layer_id)
            if layer is None:
                raise ValueError("Annotation block references an unknown SLD layer.")
            if layer.locked:
                unchanged = current is not None and normalized == current
                if not unchanged:
                    raise ValueError("Cannot create, edit, move, or remove annotation content on a locked SLD layer.")
            proposed.append(payload)
        removed_locked = [
            block.block_id for block in document.annotation_blocks
            if block.layer_id in layers and layers[block.layer_id].locked
            and block.block_id not in proposed_ids
        ]
        if removed_locked:
            raise ValueError(
                "Cannot remove annotation content from locked SLD layer(s): "
                + ", ".join(sorted(removed_locked))
            )
        result = self.application.execute(
            SetSLDAnnotationBlocksCommand(annotation_blocks=proposed)
        )
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def set_node_position(self, node_id: str, x: float, y: float) -> None:
        self._require_active_document()
        result = self.application.execute(SetSLDNodePositionCommand(node_id=node_id, x=x, y=y))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def arrange_nodes(self, object_ids: tuple[str, ...] | list[str] | None = None) -> tuple:
        document = self._require_active_document()
        ids = tuple(node.node_id for node in document.model.nodes) if object_ids is None else tuple(object_ids)
        for node_id in ids:
            if not document.model.has_node(node_id):
                raise KeyError(node_id)
        placements = self._projection_manager.arrange(ids)
        for placement in placements:
            self.set_node_position(placement.object_id, placement.x, placement.y)
        return placements

    def remove_node(self, node_id: str) -> SLDNode:
        """Remove only the persistent SLD representation identified by ``node_id``.

        This method intentionally does not infer or initiate Core-equipment deletion.
        A future coordinated engineer-deletion intent must enter the Application as
        a dedicated compound command and is not implied by SLD node removal.
        """
        document = self._require_active_document()
        node = document.model.get_node(node_id)
        result = self.application.execute(RemoveSLDNodeCommand(node_id=node_id))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.deselect_node(node_id)
        self._state.mark_dirty()
        return node

    def delete_selection(self) -> bool:
        """Delete a mixed semantic SLD selection through one document-scoped Application transaction."""
        document = self._require_active_document()
        application = self._require_application()
        node_ids = tuple(sorted(str(value) for value in self._state.selected_node_ids))
        selected_connection_ids = tuple(sorted(str(value) for value in self._state.selected_connection_ids))
        if not node_ids and not selected_connection_ids:
            return False

        network = application.read_network()
        elements = {str(item.object_id): item for item in network.elements}
        wires = {str(item.connection_id): item for item in network.simple_wires}
        draft_data = application.read_draft_network(document.document_id)
        draft_data = draft_data if isinstance(draft_data, Mapping) else {}
        draft_equipment = {
            str(item.get("draft_id", "")): item
            for item in draft_data.get("equipment", ()) if isinstance(item, Mapping)
        }
        draft_connections = {
            str(item.get("connection_id", "")): item
            for item in draft_data.get("connections", ()) if isinstance(item, Mapping)
        }
        commands: list[Any] = []
        command_keys: set[tuple[str, str]] = set()
        selected_core_equipment: set[str] = set()
        selected_draft_equipment: set[str] = set()

        def append(command: Any, identity: str) -> None:
            key = (command.command_type, identity)
            if key not in command_keys:
                command_keys.add(key)
                commands.append(command)

        def endpoint_equipment_id(endpoint: Any) -> str | None:
            if hasattr(endpoint, "to_mapping"):
                endpoint = endpoint.to_mapping()
            elif hasattr(endpoint, "to_dict"):
                endpoint = endpoint.to_dict()
            if not isinstance(endpoint, Mapping):
                return None
            if str(endpoint.get("kind", "")).strip().lower() not in {"terminal", "bus"}:
                return None
            reference = endpoint.get("endpoint", endpoint)
            if not isinstance(reference, Mapping):
                return None
            value = str(reference.get("object_id", "")).strip()
            return value or None

        for node_id in node_ids:
            node = document.model.get_node_optional(node_id)
            if node is None:
                by_equipment = getattr(document.model, "get_node_by_equipment_id_optional", None)
                node = by_equipment(node_id) if callable(by_equipment) else None
            if node is None:
                if node_id in elements:
                    element_type = str(elements[node_id].element_type).strip().upper()
                    if element_type == "BUS":
                        append(DeleteBusCommand(bus_id=node_id), node_id)
                    elif element_type == "TRANSFORMER":
                        append(DeleteTransformerCommand(transformer_id=node_id), node_id)
                    elif element_type == "BREAKER":
                        append(DeleteBreakerCommand(breaker_id=node_id), node_id)
                    else:
                        raise ValueError(
                            f"Deletion of Core equipment type {element_type!r} is unsupported; selection was not changed."
                        )
                    selected_core_equipment.add(node_id)
                    continue
                if node_id in draft_equipment:
                    append(RemoveDraftEquipmentCommand(draft_id=node_id, document_id=document.document_id), node_id)
                    selected_draft_equipment.add(node_id)
                    continue
                raise KeyError(f"Selected SLD node {node_id!r} is no longer in the active document or DraftNetwork.")
            equipment_id = str(node.equipment_id or "").strip()
            if equipment_id and equipment_id in elements:
                element_type = str(elements[equipment_id].element_type).strip().upper()
                if element_type == "BUS":
                    append(DeleteBusCommand(bus_id=equipment_id), equipment_id)
                elif element_type == "TRANSFORMER":
                    append(DeleteTransformerCommand(transformer_id=equipment_id), equipment_id)
                elif element_type == "BREAKER":
                    append(DeleteBreakerCommand(breaker_id=equipment_id), equipment_id)
                else:
                    raise ValueError(
                        f"Deletion of Core equipment type {element_type!r} is unsupported; selection was not changed."
                    )
                selected_core_equipment.add(equipment_id)
                continue
            properties = node.properties if isinstance(node.properties, Mapping) else {}
            draft_id = str(properties.get("draft_id") or properties.get("draft_equipment_id") or "").strip()
            if draft_id and draft_id in draft_equipment:
                append(RemoveDraftEquipmentCommand(draft_id=draft_id, document_id=document.document_id), draft_id)
                selected_draft_equipment.add(draft_id)
                continue
            if equipment_id:
                raise ValueError(f"Selected SLD node {node_id!r} references unresolved equipment {equipment_id!r}.")
            append(RemoveSLDNodeCommand(node_id=node_id), node_id)

        for selected_id in selected_connection_ids:
            connection = document.model.get_connection_optional(selected_id)
            if connection is None and selected_id in draft_connections:
                append(RemoveDraftConnectionCommand(connection_id=selected_id, document_id=document.document_id), selected_id)
                continue
            if connection is None:
                matches = tuple(
                    item for item in document.model.connections
                    if str(item.properties.get("core_connection_id") or "") == selected_id
                    or str(item.properties.get("draft_connection_id") or "") == selected_id
                )
                if len(matches) != 1:
                    raise KeyError(
                        f"Selected connection {selected_id!r} does not resolve in the active SLD document."
                    )
                connection = matches[0]
            properties = connection.properties
            core_id = str(properties.get("core_connection_id") or "").strip()
            draft_id = str(properties.get("draft_connection_id") or "").strip()
            if properties.get("connection_kind") == "SIMPLE_WIRE" or core_id:
                if not core_id or core_id not in wires:
                    raise ValueError(
                        f"Selected Core-backed connection {connection.connection_id!r} has no resolvable Simple Wire identity."
                    )
                append(RemoveSimpleWireConnectionCommand(connection_id=core_id), core_id)
            elif draft_id or connection.connection_id in draft_connections:
                identity = draft_id or connection.connection_id
                if identity not in draft_connections:
                    raise ValueError(f"Selected DraftNetwork connection {identity!r} is stale.")
                append(RemoveDraftConnectionCommand(connection_id=identity, document_id=document.document_id), identity)
            else:
                append(RemoveSLDConnectionCommand(connection_id=connection.connection_id), connection.connection_id)

        for equipment_id in selected_core_equipment:
            for wire_id, wire in wires.items():
                if equipment_id in {
                    endpoint_equipment_id(wire.endpoint_a),
                    endpoint_equipment_id(wire.endpoint_b),
                }:
                    append(RemoveSimpleWireConnectionCommand(connection_id=wire_id), wire_id)

        for draft_id in selected_draft_equipment:
            for connection_id, item in draft_connections.items():
                attached = any(
                    isinstance(item.get(endpoint_name), Mapping)
                    and item[endpoint_name].get("scope") == "draft"
                    and str(item[endpoint_name].get("object_id", "")).strip() == draft_id
                    for endpoint_name in ("source", "target")
                )
                if attached:
                    append(
                        RemoveDraftConnectionCommand(connection_id=connection_id, document_id=document.document_id),
                        connection_id,
                    )

        if not commands:
            return False
        result = application.execute(
            DeleteSelectionBatchCommand(commands=tuple(commands), document_id=document.document_id)
        )
        if not result.success:
            raise RuntimeError(result.message)
        self._state.clear_selection()
        self._state.mark_dirty()
        return True
    def read_instrumentation_wiring_projection(self):
        """Project canonical physical wiring onto the active SLD document nodes.

        The returned value is a detached presentation snapshot. This method
        does not add SLDConnection records, mutate Core topology, or persist
        duplicate cable/wire identity in the document.
        """
        document = self._require_active_document()
        from .instrumentation_wiring_projection import SLDInstrumentationWiringAdapter

        read_model = self.application.read_instrumentation_wiring()
        return SLDInstrumentationWiringAdapter().project(
            read_model, document.model,
            route_overrides=document.instrumentation_wiring_routes(),
        )

    def add_connection(self, connection: SLDConnection) -> None:
        self._require_active_document()
        document = self._require_active_document()
        layer_id = connection.layer_id if connection.layer_id != "default" else self.active_layer_id
        if not any(layer.layer_id == layer_id and not layer.locked for layer in document.layers):
            raise ValueError("The target SLD layer is missing or locked.")
        result = self.application.execute(AddSLDConnectionCommand(
            connection_id=connection.connection_id,
            source_node_id=connection.source_node_id,
            target_node_id=connection.target_node_id,
            source_endpoint=None if connection.source_endpoint is None else connection.source_endpoint.to_dict(),
            target_endpoint=None if connection.target_endpoint is None else connection.target_endpoint.to_dict(),
            route=connection.route.to_dict(),
            layer_id=layer_id,
        ))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def set_instrumentation_wiring_route(
        self,
        carrier_kind: str,
        carrier_id: str,
        segment_index: int,
        points: tuple[tuple[float, float], ...] | list[tuple[float, float]],
    ) -> None:
        """Persist SLD-only physical route geometry for a canonical carrier segment."""
        document = self._require_active_document()
        # Re-read the Application inventory and resolve the requested carrier
        # identity before accepting presentation geometry.
        projection = self.read_instrumentation_wiring_projection()
        match = next((
            segment for segment in projection.segments
            if segment.carrier_kind == carrier_kind
            and segment.carrier_id == carrier_id
            and segment.segment_index == segment_index
        ), None)
        if match is None:
            raise ValueError("Physical wiring route target is not present in the active Application projection.")
        document.set_instrumentation_wiring_route(carrier_kind, carrier_id, segment_index, points)
        self._state.mark_dirty()

    def clear_instrumentation_wiring_route(
        self, carrier_kind: str, carrier_id: str, segment_index: int,
    ) -> None:
        """Return one physical segment to automatic presentation routing."""
        document = self._require_active_document()
        projection = self.read_instrumentation_wiring_projection()
        if not any(
            segment.carrier_kind == carrier_kind
            and segment.carrier_id == carrier_id
            and segment.segment_index == segment_index
            for segment in projection.segments
        ):
            raise ValueError("Physical wiring route target is not present in the active Application projection.")
        document.clear_instrumentation_wiring_route(carrier_kind, carrier_id, segment_index)
        self._state.mark_dirty()

    def set_connection_route(
        self,
        connection_id: str,
        points: tuple[tuple[float, float], ...] | list[tuple[float, float]],
        *,
        routing_mode: str = "manual",
        core_connection_id: str | None = None,
    ) -> None:
        document = self._require_active_document()
        if core_connection_id is not None:
            connection = document.model.get_connection(connection_id)
            bound_core_id = connection.properties.get("core_connection_id")
            if bound_core_id != core_connection_id:
                raise ValueError(
                    "SLD route edit rejected because the presentation connection "
                    "is not bound to the requested Core connection identity."
                )
        result = self.application.execute(SetSLDConnectionRouteCommand(
            connection_id=connection_id,
            route={"routing_mode": routing_mode, "ownership": "engineer", "points": [list(point) for point in points]},
        ))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def remove_connection(self, connection_id: str) -> SLDConnection:
        document = self._require_active_document()
        connection = document.model.get_connection(connection_id)
        if connection.properties.get("connection_kind") == "SIMPLE_WIRE":
            from .simple_wire_selection import delete_selected_simple_wire
            result = delete_selected_simple_wire(self.application, connection_id)
        else:
            result = self.application.execute(RemoveSLDConnectionCommand(connection_id=connection_id))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.deselect_connection(connection_id)
        self._state.mark_dirty()
        return connection

    def select_node(self, node_id: str, *, additive: bool = False) -> None:
        """Update transient SLD selection only; selection is not deletion intent."""
        document = self._require_active_document()
        if not document.model.has_node(node_id):
            raise KeyError(node_id)
        self._state.select_node(node_id, additive=additive)

    def select_connection(self, connection_id: str, *, additive: bool = False) -> None:
        document = self._require_active_document()
        if not document.model.has_connection(connection_id):
            raise KeyError(connection_id)
        self._state.select_connection(connection_id, additive=additive)

    def clear_selection(self) -> None:
        self._state.clear_selection()

    def mark_clean(self) -> None:
        document = self.active_document
        if document is not None:
            document.mark_clean()
        self._state.mark_clean()

    def get_state(self) -> Dict[str, Any]:
        return {
            "active_document_id": self._state.active_document_id,
            "selected_node_ids": tuple(sorted(self._state.selected_node_ids)),
            "selected_connection_ids": tuple(sorted(self._state.selected_connection_ids)),
            "active_tool_id": self._state.active_tool_id,
            "interaction_mode": self._state.interaction_mode,
            "local_view_dirty": self._state.local_view_dirty,
        }

    def _require_workspace_lifecycle(self) -> ProjectWorkspaceLifecycle:
        if self._workspace_lifecycle is None:
            raise RuntimeError("SLDController requires the canonical ProjectWorkspaceLifecycle.")
        return self._workspace_lifecycle

    def _require_application(self) -> Application:
        if self._application is None:
            raise RuntimeError("SLDController requires an Application for persistent mutations.")
        return self._application

    def _require_active_document(self) -> SLDDocument:
        document = self.active_document
        if document is None:
            raise RuntimeError("No active SLD document")
        return document
