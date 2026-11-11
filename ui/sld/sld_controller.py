# ============================================================
# GridForge V2
# ============================================================
# File: ui/sld/sld_controller.py
# Purpose: SLD document/state coordination and presentation edits.
# Author: Subhendu Mishra
# ============================================================
"""Controller for the presentation-owned SLD workflow.

The controller coordinates document structure and interaction state. Persistent
SLD mutations are submitted to the Application command boundary; the
controller never mutates the SLD document directly or composes Application
services.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.application import Application
from core.application.events import ProjectClosed, ProjectLoaded
from core.application.commands.sld_commands import (
    AddSLDConnectionCommand,
    AddSLDNodeCommand,
    RemoveSLDConnectionCommand,
    RemoveSLDNodeCommand,
    DeleteSLDSelectionCommand,
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

    @property
    def active_layer_id(self) -> str:
        """Transient authoring layer for the active SLD document."""
        document = self._require_active_document()
        active = self._active_layer_by_document.get(document.document_id, document.default_layer_id)
        if not any(layer.layer_id == active and layer.visible and not layer.locked for layer in document.layers):
            active = document.default_layer_id
            self._active_layer_by_document[document.document_id] = active
        return active

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
        if (changes.get("locked") is True or changes.get("visible") is False) and self._active_layer_by_document.get(document.document_id) == layer_id:
            self._active_layer_by_document[document.document_id] = document.default_layer_id

    def delete_layer(self, layer_id: str, *, reassign_to: str = "default") -> None:
        self._execute_layer_command(DeleteSLDLayerCommand(layer_id=layer_id, reassign_to=reassign_to))
        document = self._require_active_document()
        if self._active_layer_by_document.get(document.document_id) == layer_id:
            self._active_layer_by_document[document.document_id] = reassign_to

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
        """Delete the active typed SLD selection through one Application transaction."""
        document = self._require_active_document()
        node_ids = tuple(sorted(self._state.selected_node_ids))
        connection_ids = tuple(sorted(self._state.selected_connection_ids))
        if not node_ids and not connection_ids:
            return False
        if node_ids and connection_ids:
            raise RuntimeError("SLD selection spans incompatible domains; deletion is rejected.")

        if connection_ids:
            selected_connections = tuple(
                document.model.get_connection(connection_id) for connection_id in connection_ids
            )
            simple_wires = tuple(
                connection for connection in selected_connections
                if connection.properties.get("connection_kind") == "SIMPLE_WIRE"
            )
            if simple_wires:
                if len(selected_connections) != 1 or len(simple_wires) != 1:
                    raise RuntimeError(
                        "Multi-selection containing Simple Wires cannot be deleted "
                        "as a presentation-only batch. Delete each electrical connection "
                        "through its canonical Application command."
                    )
                self.remove_connection(connection_ids[0])
                return True
            if any(connection.properties.get("core_connection_id") for connection in selected_connections):
                raise RuntimeError(
                    "Selected connection is bound to Core connectivity but has no supported "
                    "SLD deletion command; refusing presentation-only deletion."
                )

        result = self.application.execute(
            DeleteSLDSelectionCommand(node_ids=node_ids, connection_ids=connection_ids)
        )
        if not result.success:
            raise RuntimeError(result.message)
        self._state.clear_selection()
        self._state.mark_dirty()
        return True

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
