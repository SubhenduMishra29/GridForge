# ============================================================
# File: ui/interaction/interaction_session.py
# GridForge V2 — Interaction Session
# Author: Subhendu Mishra
# ============================================================
"""Transient presentation interaction state.

InteractionSession owns temporary UI interaction state only. It is not an
engineering model, does not mutate Core objects, and does not execute
Application commands. Tools/controllers use it to accumulate intent before
handing a command to the Application boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class InteractionSession:
    """Own transient selection, tool, connection and edit state."""

    active_tool_id: str | None = None
    selected_ids: tuple[str, ...] = ()
    connection_source_id: str | None = None
    drag_object_id: str | None = None
    preview: Any = None
    pending_intent: Any = None
    _closed: bool = field(default=False, init=False, repr=False)

    @property
    def closed(self) -> bool:
        return self._closed

    def activate_tool(self, tool_id: str) -> None:
        self._ensure_open()
        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError("tool_id must be a non-empty string")
        self.active_tool_id = tool_id

    def clear_tool(self) -> None:
        self._ensure_open()
        self.active_tool_id = None

    def set_selection(self, object_ids: tuple[str, ...] | list[str]) -> None:
        self._ensure_open()
        normalized = tuple(str(object_id) for object_id in object_ids)
        if any(not object_id for object_id in normalized):
            raise ValueError("selection IDs must not be empty")
        self.selected_ids = normalized

    def clear_selection(self) -> None:
        self._ensure_open()
        self.selected_ids = ()

    def begin_connection(self, source_id: str) -> None:
        self._ensure_open()
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("source_id must be a non-empty string")
        self.connection_source_id = source_id

    def cancel_connection(self) -> None:
        self._ensure_open()
        self.connection_source_id = None
        self.preview = None

    def begin_drag(self, object_id: str) -> None:
        self._ensure_open()
        if not isinstance(object_id, str) or not object_id:
            raise ValueError("object_id must be a non-empty string")
        self.drag_object_id = object_id

    def end_drag(self) -> None:
        self._ensure_open()
        self.drag_object_id = None
        self.preview = None

    def set_preview(self, preview: Any) -> None:
        self._ensure_open()
        self.preview = preview

    def set_intent(self, intent: Any) -> None:
        self._ensure_open()
        self.pending_intent = intent

    def clear_intent(self) -> None:
        self._ensure_open()
        self.pending_intent = None

    def cancel(self) -> None:
        """Cancel all transient interaction state without touching Core."""
        self._ensure_open()
        self.connection_source_id = None
        self.drag_object_id = None
        self.preview = None
        self.pending_intent = None

    def commit(self) -> Any:
        """Return pending intent for Application submission and clear it."""
        self._ensure_open()
        intent = self.pending_intent
        self.pending_intent = None
        self.preview = None
        return intent

    def close(self) -> None:
        """Make the session inert and release all transient state."""
        if self._closed:
            return
        self.cancel()
        self.active_tool_id = None
        self.selected_ids = ()
        self._closed = True

    def get_state(self) -> dict[str, Any]:
        """Return a diagnostic snapshot of transient session state."""
        return {
            "active_tool_id": self.active_tool_id,
            "selected_ids": self.selected_ids,
            "connection_source_id": self.connection_source_id,
            "drag_object_id": self.drag_object_id,
            "has_preview": self.preview is not None,
            "has_pending_intent": self.pending_intent is not None,
            "closed": self.closed,
        }

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("InteractionSession is closed.")


__all__ = ["InteractionSession"]
