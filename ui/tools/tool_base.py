# ============================================================
# File: ui/tools/tool_base.py
# GridForge V2 — Tool Base Contract
# Author: Subhendu Mishra
# ============================================================
"""Base contract for GridForge V2 UI interaction tools.

Tools translate UI interaction into intent. The canonical mutation boundary
is ``core.application.Application``. Tools do not own CommandManager,
history, undo/redo, electrical truth, or rendering.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ToolBase(ABC):
    """Abstract base class for GridForge V2 interaction tools."""

    def __init__(
        self,
        controller: Any,
        *,
        application: Any,
        selection_manager: Any,
        snap_system: Any,
    ) -> None:
        if controller is None:
            raise ValueError("controller must not be None.")
        if application is None:
            raise ValueError("application must not be None.")
        if selection_manager is None:
            raise ValueError("selection_manager must not be None.")
        if snap_system is None:
            raise ValueError("snap_system must not be None.")

        self.controller = controller
        self.application = application
        self.selection_manager = selection_manager
        self.snap_system = snap_system
        self._active = False
        self._disposed = False

    @property
    @abstractmethod
    def tool_id(self) -> str:
        """Return the stable ToolManager identifier."""
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.tool_id.replace("_", " ").title()

    @property
    def description(self) -> str:
        return self.name

    def activate(self) -> None:
        self._ensure_not_disposed()
        if self._active:
            return
        self._active = True
        self.on_activate()

    def deactivate(self) -> None:
        self._ensure_not_disposed()
        if not self._active:
            return
        self.on_deactivate()
        self._active = False

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def disposed(self) -> bool:
        return self._disposed

    def mouse_press(self, event: Any) -> bool:
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        return bool(self.on_mouse_press(event))

    def mouse_move(self, event: Any) -> bool:
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        return bool(self.on_mouse_move(event))

    def mouse_release(self, event: Any) -> bool:
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        return bool(self.on_mouse_release(event))

    def mouse_double_click(self, event: Any) -> bool:
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        return bool(self.on_mouse_double_click(event))

    def on_mouse_press(self, event: Any) -> bool:
        return False

    def on_mouse_move(self, event: Any) -> bool:
        return False

    def on_mouse_release(self, event: Any) -> bool:
        return False

    def on_mouse_double_click(self, event: Any) -> bool:
        return False

    def key_press(self, event: Any) -> bool:
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        if self._is_escape_event(event):
            return bool(self.cancel())
        return bool(self.on_key_press(event))

    def key_release(self, event: Any) -> bool:
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        return bool(self.on_key_release(event))

    def on_key_press(self, event: Any) -> bool:
        return False

    def on_key_release(self, event: Any) -> bool:
        return False

    def cancel(self) -> bool:
        self._ensure_active()
        return bool(self.on_cancel())

    def on_cancel(self) -> bool:
        return False

    def reset(self) -> None:
        self._ensure_not_disposed()
        self.on_reset()

    def on_reset(self) -> None:
        pass

    def execute_command(self, command: Any) -> Any:
        """Submit an immutable command through the canonical Application boundary."""
        self._ensure_active()
        if command is None:
            raise ValueError("command must not be None.")
        return self.application.execute(command)

    def get_selection_manager(self) -> Any:
        self._ensure_not_disposed()
        return self.selection_manager

    def get_snap_system(self) -> Any:
        self._ensure_not_disposed()
        return self.snap_system

    def get_controller(self) -> Any:
        self._ensure_not_disposed()
        return self.controller

    @staticmethod
    def event_position(event: Any) -> Any:
        if event is None:
            raise ValueError("event must not be None.")
        position = getattr(event, "position", None)
        if callable(position):
            return position()
        if position is not None:
            return position
        if isinstance(event, dict) and "position" in event:
            return event["position"]
        raise AttributeError("event does not expose position().")

    @staticmethod
    def _is_escape_event(event: Any) -> bool:
        if event is None:
            return False
        key = getattr(event, "key", None)
        if callable(key):
            try:
                key = key()
            except TypeError:
                return False
        if isinstance(event, dict):
            key = event.get("key", key)
        return key in (16777216, "Escape", "Key_Escape")

    def get_state(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "active": self._active,
            "disposed": self._disposed,
            "has_application": self.application is not None,
            "has_selection_manager": self.selection_manager is not None,
            "has_snap_system": self.snap_system is not None,
        }

    def dispose(self) -> None:
        if self._disposed:
            return
        if self._active:
            self.deactivate()
        self.on_dispose()
        self._disposed = True

    def on_dispose(self) -> None:
        pass

    def _ensure_active(self) -> None:
        self._ensure_not_disposed()
        if not self._active:
            raise RuntimeError("Tool is not active.")

    def _ensure_not_disposed(self) -> None:
        if self._disposed:
            raise RuntimeError("Tool has been disposed.")


__all__ = ["ToolBase"]
