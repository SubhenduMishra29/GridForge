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
controller never mutates the SLD document directly.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.application.application import Application
from core.application.commands.sld_commands import (
    AddSLDConnectionCommand,
    AddSLDNodeCommand,
    RemoveSLDConnectionCommand,
    RemoveSLDNodeCommand,
    SetSLDNodePositionCommand,
)
from core.application.services.sld_service import SLDService

from .sld_document import SLDDocument
from .sld_model import SLDConnection, SLDNode
from .sld_projection_manager import SLDProjectionManager
from .sld_state import SLDState


class SLDController:
    """Application-facing controller for SLD document operations."""

    def __init__(self, state: Optional[SLDState] = None,
                 projection_manager: Optional[SLDProjectionManager] = None,
                 application: Optional[Application] = None) -> None:
        self._state = state if state is not None else SLDState()
        self._projection_manager = projection_manager if projection_manager is not None else SLDProjectionManager()
        self._application = application
        self._documents: Dict[str, SLDDocument] = {}

    @property
    def state(self) -> SLDState:
        return self._state

    @property
    def application(self) -> Application:
        return self._require_application()

    @property
    def active_document(self) -> Optional[SLDDocument]:
        document_id = self._state.active_document_id
        if document_id is None:
            return None
        return self._documents.get(document_id)

    def register_document(self, document: SLDDocument) -> None:
        if document.document_id in self._documents:
            raise ValueError(f"Document already registered: {document.document_id}")
        self._documents[document.document_id] = document
        if self._state.active_document_id is None:
            self.activate_document(document.document_id)

    def unregister_document(self, document_id: str) -> SLDDocument:
        if document_id not in self._documents:
            raise KeyError(document_id)
        if self._state.active_document_id == document_id:
            self._state.active_document_id = None
            self._state.clear_selection()
        return self._documents.pop(document_id)

    def replace_document(self, document: SLDDocument) -> SLDDocument:
        """Replace the active persistent SLD document after project load."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        old = self.active_document
        if old is not None:
            self._documents.pop(old.document_id, None)
        self._documents.clear()
        self._state.reset()
        self.register_document(document)
        self.activate_document(document.document_id)
        self._state.mark_clean()
        return document

    def get_document(self, document_id: str) -> Optional[SLDDocument]:
        return self._documents.get(document_id)

    def activate_document(self, document_id: str) -> SLDDocument:
        document = self._documents.get(document_id)
        if document is None:
            raise KeyError(document_id)
        self._state.active_document_id = document_id
        self._state.clear_selection()
        if self._application is not None:
            try:
                self._application.sld_service.bind_document(document)
            except RuntimeError:
                self._application.attach_sld_service(SLDService(document))
        return document

    @property
    def document_count(self) -> int:
        return len(self._documents)

    def add_node(self, node: SLDNode) -> None:
        self._require_active_document()
        result = self.application.execute(AddSLDNodeCommand(
            node_id=node.node_id, equipment_id=node.equipment_id, x=node.x, y=node.y,
        ))
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
        ))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.mark_dirty()

    def remove_connection(self, connection_id: str) -> SLDConnection:
        document = self._require_active_document()
        connection = document.model.get_connection(connection_id)
        result = self.application.execute(RemoveSLDConnectionCommand(connection_id=connection_id))
        if not result.success:
            raise RuntimeError(result.message)
        self._state.deselect_connection(connection_id)
        self._state.mark_dirty()
        return connection

    def select_node(self, node_id: str, *, additive: bool = False) -> None:
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

    def set_active_tool(self, tool_id: Optional[str]) -> None:
        self._state.active_tool_id = tool_id

    def set_interaction_mode(self, mode: str) -> None:
        if not mode:
            raise ValueError("mode must not be empty")
        self._state.interaction_mode = mode

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

    def _require_application(self) -> Application:
        if self._application is None:
            raise RuntimeError("SLDController requires an Application for persistent mutations.")
        return self._application

    def _require_active_document(self) -> SLDDocument:
        document = self.active_document
        if document is None:
            raise RuntimeError("No active SLD document")
        return document
