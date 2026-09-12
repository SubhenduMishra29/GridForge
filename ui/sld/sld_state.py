## ui/sld/sld_state.py
"""
GridForge V2 — SLD State.

Stores UI-level SLD interaction state without depending on Qt. Project
persistence dirtiness is owned by Application; this state only tracks local
presentation/view workflow dirtiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SLDState:
    """Transient SLD interaction and local-view state.

    ``local_view_dirty`` never means that the GridForge project requires a
    save. That decision belongs exclusively to ``Application.is_dirty``.
    ``dirty`` remains a compatibility alias for existing presentation code,
    but its meaning is explicitly local-view state only.
    """

    active_document_id: Optional[str] = None
    selected_node_ids: set[str] = field(default_factory=set)
    selected_connection_ids: set[str] = field(default_factory=set)
    active_tool_id: Optional[str] = None
    interaction_mode: str = "select"
    local_view_dirty: bool = False

    @property
    def dirty(self) -> bool:
        """Compatibility alias for transient local-view dirtiness only."""
        return self.local_view_dirty

    def select_node(self, node_id: str, *, additive: bool = False) -> None:
        if not additive:
            self.clear_selection()
        self.selected_node_ids.add(node_id)

    def deselect_node(self, node_id: str) -> None:
        self.selected_node_ids.discard(node_id)

    def select_connection(self, connection_id: str, *, additive: bool = False) -> None:
        if not additive:
            self.clear_selection()
        self.selected_connection_ids.add(connection_id)

    def deselect_connection(self, connection_id: str) -> None:
        self.selected_connection_ids.discard(connection_id)

    def clear_selection(self) -> None:
        self.selected_node_ids.clear()
        self.selected_connection_ids.clear()

    @property
    def has_selection(self) -> bool:
        return bool(self.selected_node_ids or self.selected_connection_ids)

    def mark_dirty(self) -> None:
        """Mark only local UI/view state as changed."""
        self.local_view_dirty = True

    def mark_clean(self) -> None:
        self.local_view_dirty = False

    def reset(self) -> None:
        self.active_document_id = None
        self.selected_node_ids.clear()
        self.selected_connection_ids.clear()
        self.active_tool_id = None
        self.interaction_mode = "select"
        self.local_view_dirty = False
