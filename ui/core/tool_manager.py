# ============================================================
# File: ui/core/tool_manager.py
# GridForge V2 — Tool Manager
# Author: Subhendu Mishra
# ============================================================
"""Authoritative runtime lifecycle manager for UI interaction tools.

ToolManager owns concrete tool instances, lifecycle, and input dispatch.
The registry provides factories; every factory receives the single canonical
dependency contract: controller, application, selection_manager, and
snap_system.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

_LOGGER = logging.getLogger(__name__)

from ui.creation.creation_context import CreationContext


ToolFactory = Callable[..., Any]


class _ClipboardPasteInteraction:
    """Transient canvas interaction for accepting or cancelling a clipboard preview.

    It owns no engineering state. The supplied callback submits the one
    Application command only after the user accepts the preview.
    """

    tool_id = "clipboard-paste"
    cancel_parent_tool_on_cancel = False
    cancel_creation_context_on_cancel = False
    cancel_creation_context_on_complete = False

    def __init__(self, preview_layer: Any, items: tuple[Any, ...], origin: tuple[float, float], on_accept: Callable[[tuple[float, float]], bool]) -> None:
        if preview_layer is None or not items or not callable(on_accept):
            raise ValueError("Clipboard preview requires a PreviewLayer, graphics items, and an acceptance callback.")
        self._preview_layer = preview_layer
        self._items = tuple(items)
        self._origin = (float(origin[0]), float(origin[1]))
        self._on_accept = on_accept
        self._base_positions = tuple(
            (float(item.pos().x()), float(item.pos().y())) for item in self._items
        )
        self._delta = (0.0, 0.0)
        self._active = False
        self._finished = False

    def activate(self) -> None:
        if self._finished:
            raise RuntimeError("Clipboard preview interaction is already finished.")
        self._active = True

    def deactivate(self) -> None:
        self.cancel()

    @staticmethod
    def _event_point(event: Any) -> tuple[float, float]:
        point = getattr(event, "scene_position", None)
        if point is None:
            point = getattr(event, "position", None)
            if callable(point):
                point = point()
        if isinstance(event, dict):
            point = event.get("scene_position", event.get("position", point))
        if point is None:
            raise AttributeError("Clipboard placement event has no scene position.")
        if hasattr(point, "x") and hasattr(point, "y"):
            x = point.x() if callable(point.x) else point.x
            y = point.y() if callable(point.y) else point.y
            return float(x), float(y)
        if isinstance(point, (tuple, list)) and len(point) >= 2:
            return float(point[0]), float(point[1])
        raise TypeError("Clipboard placement position must expose x/y coordinates.")

    def _clear_preview(self) -> None:
        # Remove only this interaction's items. PreviewLayer is shared with
        # other active tools, so clipboard cancellation must not clear their
        # unrelated transient graphics.
        for item in self._items:
            self._preview_layer.remove(item)

    def _move_to(self, event: Any) -> None:
        x, y = self._event_point(event)
        self._delta = (x - self._origin[0], y - self._origin[1])
        dx, dy = self._delta
        for item, (base_x, base_y) in zip(self._items, self._base_positions):
            item.setPos(base_x + dx, base_y + dy)

    def mouse_move(self, event: Any) -> bool:
        if not self._active or self._finished:
            return False
        self._move_to(event)
        return True

    def mouse_press(self, event: Any) -> bool:
        return self._active and not self._finished

    def mouse_release(self, event: Any) -> bool:
        if not self._active or self._finished:
            return False
        self._move_to(event)
        if not self._on_accept(self._delta):
            return False
        self._finished = True
        self._active = False
        self._clear_preview()
        return True

    def key_press(self, event: Any) -> bool:
        key = getattr(event, "key", None)
        if callable(key):
            key = key()
        if isinstance(event, dict):
            key = event.get("key", key)
        if key not in ("Escape", "escape", "Key_Escape", 0x01000000, 16777216):
            return False
        return self.cancel()

    def cancel(self) -> bool:
        """Cancel the temporary interaction and only the transient owners it controls."""
        self._ensure_active()
        interaction_tool = self._interaction_tool
        result = False
        cancel_parent = getattr(interaction_tool, "cancel_parent_tool_on_cancel", True)
        cancel_context = getattr(interaction_tool, "cancel_creation_context_on_cancel", True)
        if interaction_tool is not None:
            result = bool(interaction_tool.cancel())
            self._clear_interaction_tool()

        active_tool = self._active_tool
        if cancel_parent and active_tool is not None and active_tool is not interaction_tool:
            result = bool(active_tool.cancel()) or result

        if cancel_context:
            had_draft = self.creation_context.active
            self.creation_context.cancel()
            callback = getattr(self.controller, "_on_creation_cancelled", None)
            if callable(callback) and had_draft:
                callback()
        return result

    def reset(self) -> None:
        self._ensure_active()
        # Reset is a lifecycle boundary for every transient interaction,
        # including staged clipboard previews that have not reached Application.
        self._clear_interaction_tool()
        if self._active_tool is not None:
            self._active_tool.reset()
        had_draft = self.creation_context.active
        if had_draft:
            self.creation_context.cancel()
            callback = getattr(self.controller, "_on_creation_cancelled", None)
            if callable(callback):
                callback()

    def get_state(self) -> dict[str, Any]:
        return {
            "disposed": self._disposed,
            "tool_ids": self.get_tool_ids() if not self._disposed else (),
            "active_tool_id": self._active_tool_id,
            "active": self._active_tool is not None,
            "instance_count": len(self._tool_instances),
            "interaction_tool_id": getattr(self._interaction_tool, "tool_id", None),
        }

    def dispose(self) -> None:
        if self._disposed:
            return
        self._clear_interaction_tool()
        if self._active_tool is not None:
            previous_id = self._active_tool_id
            self._active_tool.deactivate()
            self._active_tool = None
            self._active_tool_id = None
            self._notify_controller_tool_change(previous_id, None)
        for tool_id, tool in tuple(self._tool_instances.items()):
            self._dispose_tool(tool)
            del self._tool_instances[tool_id]
        self.creation_context.discard()
        self._tool_registry.clear()
        self._disposed = True

    def _definition_for_tool(self, tool_id: str) -> Any | None:
        registry = self.equipment_registry
        require = getattr(registry, "require", None) if registry is not None else None
        if not callable(require):
            return None
        try:
            definition = require(tool_id)
        except KeyError:
            return None
        return definition if getattr(definition, "tool_id", None) == tool_id else None

    @staticmethod
    def _dispose_tool(tool: Any) -> None:
        dispose = getattr(tool, "dispose", None)
        if callable(dispose):
            dispose()

    @staticmethod
    def _validate_tool_id(tool_id: str) -> None:
        if not isinstance(tool_id, str):
            raise TypeError("tool_id must be a string.")
        if not tool_id.strip():
            raise ValueError("tool_id must not be empty.")

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("ToolManager has been disposed.")


__all__ = ["ToolFactory", "ToolManager"]
