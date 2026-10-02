# ============================================================
# File: ui/sld/sld_state.py
# GridForge V2 — SLD Presentation View State
# Author: Subhendu Mishra
# ============================================================
"""SLD-specific view/document state.

Selection is owned by SelectionManager and active-tool lifecycle is owned by
ToolManager. This compatibility type deliberately stores neither authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SLDState:
    """Transient SLD document/view state only.

    active_document_id and local-view dirtiness are SLD-specific. Legacy
    selection/tool access is read-through only when canonical authorities are
    attached.
    """

    active_document_id: Optional[str] = None
    local_view_dirty: bool = False
    selection_manager: Any = None
    tool_manager: Any = None

    @property
    def selected_node_ids(self) -> frozenset[str]:
        manager = self.selection_manager
        if manager is None:
            return frozenset()
        getter = getattr(manager, "get_selected_ids", None)
        if not callable(getter):
            return frozenset()
        return frozenset(str(value) for value in getter())

    @property
    def selected_connection_ids(self) -> frozenset[str]:
        return frozenset()

    @property
    def active_tool_id(self) -> Optional[str]:
        manager = self.tool_manager
        return getattr(manager, "active_tool_id", None) if manager is not None else None

    @property
    def interaction_mode(self) -> str:
        """Derive a display mode from ToolManager without storing it."""
        tool_id = self.active_tool_id
        if tool_id is None:
            return "idle"
        if tool_id == "select":
            return "select"
        if tool_id == "wire":
            return "connect"
        return "create"

    def select_node(self, node_id: str, *, additive: bool = False) -> None:
        manager = self.selection_manager
        if manager is None:
            raise RuntimeError("SelectionManager must be attached for selection operations.")
        manager.select(node_id, multi=additive)

    def deselect_node(self, node_id: str) -> None:
        manager = self.selection_manager
        if manager is None:
            raise RuntimeError("SelectionManager must be attached for selection operations.")
        if manager.is_selected(node_id):
            manager.toggle_selection(node_id)

    def select_connection(self, connection_id: str, *, additive: bool = False) -> None:
        self.select_node(connection_id, additive=additive)

    def deselect_connection(self, connection_id: str) -> None:
        self.deselect_node(connection_id)

    def clear_selection(self) -> None:
        manager = self.selection_manager
        if manager is None:
            raise RuntimeError("SelectionManager must be attached for selection operations.")
        manager.clear()

    @property
    def dirty(self) -> bool:
        return self.local_view_dirty

    @property
    def has_selection(self) -> bool:
        return bool(self.selected_node_ids or self.selected_connection_ids)

    def mark_dirty(self) -> None:
        self.local_view_dirty = True

    def mark_clean(self) -> None:
        self.local_view_dirty = False

    def reset(self) -> None:
        self.active_document_id = None
        self.local_view_dirty = False


__all__ = ["SLDState"]
