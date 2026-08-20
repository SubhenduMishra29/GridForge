## ui/sld/sld_controller.py
"""
GridForge V2 — SLD Controller.

The controller coordinates the SLD model/document/state boundary.

It deliberately does not create Qt widgets and does not perform electrical
calculations.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .sld_document import SLDDocument
from .sld_model import SLDConnection, SLDNode
from .sld_state import SLDState


class SLDController:
    """
    Application-facing controller for the SLD workflow.

    The controller is intentionally lightweight. Complex responsibilities
    such as connection validation, equipment factories, tool dispatch,
    rendering, and Core synchronization will be attached through their
    dedicated subsystems in later implementation phases.
    """

    def __init__(
        self,
        state: Optional[SLDState] = None,
    ) -> None:
        self._state = state if state is not None else SLDState()
        self._documents: Dict[str, SLDDocument] = {}

    @property
    def state(self) -> SLDState:
        return self._state

    @property
    def active_document(self) -> Optional[SLDDocument]:
        document_id = self._state.active_document_id

        if document_id is None:
            return None

        return self._documents.get(document_id)

    # ------------------------------------------------------------------
    # Document lifecycle
    # ------------------------------------------------------------------

    def register_document(self, document: SLDDocument) -> None:
        if document.document_id in self._documents:
            raise ValueError(
                f"Document already registered: {document.document_id}"
            )

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

    def get_document(
        self,
        document_id: str,
    ) -> Optional[SLDDocument]:
        return self._documents.get(document_id)

    def activate_document(self, document_id: str) -> SLDDocument:
        document = self._documents.get(document_id)

        if document is None:
            raise KeyError(document_id)

        self._state.active_document_id = document_id
        self._state.clear_selection()

        return document

    @property
    def document_count(self) -> int:
        return len(self._documents)

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def add_node(
        self,
        node: SLDNode,
    ) -> None:
        document = self._require_active_document()

        document.model.add_node(node)
        document.mark_modified()
        self._state.mark_dirty()

    def remove_node(
        self,
        node_id: str,
    ) -> SLDNode:
        document = self._require_active_document()

        removed = document.model.remove_node(node_id)

        self._state.deselect_node(node_id)
        document.mark_modified()
        self._state.mark_dirty()

        return removed

    # ------------------------------------------------------------------
    # Connection operations
    # ------------------------------------------------------------------

    def add_connection(
        self,
        connection: SLDConnection,
    ) -> None:
        document = self._require_active_document()

        document.model.add_connection(connection)
        document.mark_modified()
        self._state.mark_dirty()

    def remove_connection(
        self,
        connection_id: str,
    ) -> SLDConnection:
        document = self._require_active_document()

        removed = document.model.remove_connection(connection_id)

        self._state.deselect_connection(connection_id)
        document.mark_modified()
        self._state.mark_dirty()

        return removed

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def select_node(
        self,
        node_id: str,
        *,
        additive: bool = False,
    ) -> None:
        document = self._require_active_document()

        if not document.model.has_node(node_id):
            raise KeyError(node_id)

        self._state.select_node(
            node_id,
            additive=additive,
        )

    def select_connection(
        self,
        connection_id: str,
        *,
        additive: bool = False,
    ) -> None:
        document = self._require_active_document()

        if not document.model.has_connection(connection_id):
            raise KeyError(connection_id)

        self._state.select_connection(
            connection_id,
            additive=additive,
        )

    def clear_selection(self) -> None:
        self._state.clear_selection()

    # ------------------------------------------------------------------
    # Tool / interaction state
    # ------------------------------------------------------------------

    def set_active_tool(self, tool_id: Optional[str]) -> None:
        self._state.active_tool_id = tool_id

    def set_interaction_mode(self, mode: str) -> None:
        if not mode:
            raise ValueError("mode must not be empty")

        self._state.interaction_mode = mode

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def mark_clean(self) -> None:
        document = self.active_document

        if document is not None:
            document.mark_clean()

        self._state.mark_clean()

    def get_state(self) -> Dict[str, Any]:
        return {
            "active_document_id": self._state.active_document_id,
            "selected_node_ids": tuple(
                sorted(self._state.selected_node_ids)
            ),
            "selected_connection_ids": tuple(
                sorted(self._state.selected_connection_ids)
            ),
            "active_tool_id": self._state.active_tool_id,
            "interaction_mode": self._state.interaction_mode,
            "dirty": self._state.dirty,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require_active_document(self) -> SLDDocument:
        document = self.active_document

        if document is None:
            raise RuntimeError("No active SLD document")

        return document
