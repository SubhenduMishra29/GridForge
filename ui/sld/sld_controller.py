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
    SetSLDNodePositionCommand,
    SetSLDNodePropertiesCommand,
    SetSLDConnectionRouteCommand,
)

from .sld_document import SLDDocument
from .sld_model import SLDConnection, SLDNode
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
        if self._application is not None:
            self._application.event_bus.subscribe(ProjectLoaded, self._on_project_loaded)
            self._application.event_bus.subscribe(ProjectClosed, self._on_project_closed)

    @property
    def state(self) -> SLDState:
        return self._state

    @property
    def application(self) -> Application:
        return self._require_application()

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
            lifecycle.documents.replace(document)
        if lifecycle.documents.active_document_id == document.document_id:
            self.reconcile_presentation()

    def unregister_document(self, document_id: str) -> SLDDocument:
        lifecycle = self._require_workspace_lifecycle()
        document = lifecycle.documents.require(document_id)
        if not isinstance(document, SLDDocument):
            raise TypeError("Document is not an SLDDocument.")
        lifecycle.remove_document(document_id)
        return document

    def replace_document(self, document: SLDDocument) -> SLDDocument:
        """Compatibility adapter; project lifecycle owns replacement/activation."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        lifecycle = self._require_workspace_lifecycle()
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
        self.reconcile_presentation()

    def _on_project_closed(self, _event: ProjectClosed) -> None:
        self._state.reset()

    def dispose(self) -> None:
        if self._application is not None:
            self._application.event_bus.unsubscribe(ProjectLoaded, self._on_project_loaded)
            self._application.event_bus.unsubscribe(ProjectClosed, self._on_project_closed)
        self._state.reset()

    @property
    def document_count(self) -> int:
        manager = self.document_manager
        return len(manager) if manager is not None else 0

    def add_node(self, node: SLDNode) -> None:
        self._require_active_document()
        result = self.application.execute(AddSLDNodeCommand(
            node_id=node.node_id, equipment_id=node.equipment_id, x=node.x, y=node.y,
        ))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def set_node_properties(self, node_id: str, properties: Dict[str, Any]) -> None:
        self._require_active_document()
        result = self.application.execute(SetSLDNodePropertiesCommand(node_id=node_id, properties=properties))
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

    def add_connection(self, connection: SLDConnection) -> None:
        self._require_active_document()
        result = self.application.execute(AddSLDConnectionCommand(
            connection_id=connection.connection_id,
            source_node_id=connection.source_node_id,
            target_node_id=connection.target_node_id,
            source_endpoint=None if connection.source_endpoint is None else connection.source_endpoint.to_dict(),
            target_endpoint=None if connection.target_endpoint is None else connection.target_endpoint.to_dict(),
            route=connection.route.to_dict(),
        ))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def set_connection_route(self, connection_id: str, points: tuple[tuple[float, float], ...] | list[tuple[float, float]], *, routing_mode: str = "manual") -> None:
        self._require_active_document()
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
