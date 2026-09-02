# ============================================================
# File: ui/tools/tool_base.py
# GridForge V2 — Tool Base Contract
# Author: Subhendu Mishra
# ============================================================
"""Base contract for GridForge V2 UI interaction tools.

Architectural role
------------------
Tools translate UI interaction into intent. They may use the
application command boundary, SelectionManager, and SnapSystem, but
never own electrical truth or rendering.

SLD rendering is intentionally outside this contract. Projection and
graphics realization are owned by the unified SLD projection path.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class ToolBase(ABC):
    """Abstract base class for GridForge V2 interaction tools."""

    def __init__(
        self,
        controller: Any,
        *,
        command_manager: Optional[Any] = None,
        selection_manager: Optional[Any] = None,
        snap_system: Optional[Any] = None,
    ) -> None:
        """Initialize injected interaction/application dependencies."""
        if controller is None:
            raise ValueError("controller must not be None.")

        self.controller = controller
        self.command_manager = command_manager
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
        """Return the human-readable tool name."""
        return self.tool_id.replace("_", " ").title()

    @property
    def description(self) -> str:
        """Return the human-readable tool description."""
        return self.name

    def activate(self) -> None:
        """Activate the tool and its transient interaction state."""
        self._ensure_not_disposed()
        if self._active:
            return
        self._active = True
        self.on_activate()

    def deactivate(self) -> None:
        """Deactivate the tool and clear its transient state."""
        self._ensure_not_disposed()
        if not self._active:
            return
        self.on_deactivate()
        self._active = False

    def on_activate(self) -> None:
        """Activation hook for concrete tools."""

    def on_deactivate(self) -> None:
        """Deactivation hook for concrete tools."""

    @property
    def is_active(self) -> bool:
        """Return whether the tool is active."""
        return self._active

    @property
    def disposed(self) -> bool:
        """Return whether the tool has been disposed."""
        return self._disposed

    def mouse_press(self, event: Any) -> bool:
        """Route a mouse-press event to the concrete tool."""
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        return bool(self.on_mouse_press(event))

    def mouse_move(self, event: Any) -> bool:
        """Route a mouse-move event to the concrete tool."""
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        return bool(self.on_mouse_move(event))

    def mouse_release(self, event: Any) -> bool:
        """Route a mouse-release event to the concrete tool."""
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        return bool(self.on_mouse_release(event))

    def mouse_double_click(self, event: Any) -> bool:
        """Route a mouse-double-click event to the concrete tool."""
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        return bool(self.on_mouse_double_click(event))

    def on_mouse_press(self, event: Any) -> bool:
        """Concrete-tool mouse-press hook."""
        return False

    def on_mouse_move(self, event: Any) -> bool:
        """Concrete-tool mouse-move hook."""
        return False

    def on_mouse_release(self, event: Any) -> bool:
        """Concrete-tool mouse-release hook."""
        return False

    def on_mouse_double_click(self, event: Any) -> bool:
        """Concrete-tool mouse-double-click hook."""
        return False

    def key_press(self, event: Any) -> bool:
        """Route keyboard input, treating Escape as cancellation."""
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        if self._is_escape_event(event):
            return bool(self.cancel())
        return bool(self.on_key_press(event))

    def key_release(self, event: Any) -> bool:
        """Route keyboard-release input."""
        self._ensure_active()
        if event is None:
            raise ValueError("event must not be None.")
        return bool(self.on_key_release(event))

    def on_key_press(self, event: Any) -> bool:
        """Concrete-tool keyboard-press hook."""
        return False

    def on_key_release(self, event: Any) -> bool:
        """Concrete-tool keyboard-release hook."""
        return False

    def cancel(self) -> bool:
        """Cancel the current transient tool operation."""
        self._ensure_active()
        return bool(self.on_cancel())

    def on_cancel(self) -> bool:
        """Concrete-tool cancellation hook."""
        return False

    def reset(self) -> None:
        """Reset transient tool state."""
        self._ensure_not_disposed()
        self.on_reset()

    def on_reset(self) -> None:
        """Concrete-tool reset hook."""

    def execute_command(self, command: Any) -> Any:
        """Submit a command through the configured CommandManager."""
        self._ensure_active()
        if command is None:
            raise ValueError("command must not be None.")
        if self.command_manager is None:
            raise RuntimeError("command_manager is not configured.")
        execute = getattr(self.command_manager, "execute", None)
        if not callable(execute):
            raise TypeError("command_manager must provide execute().")
        return execute(command)

    def get_selection_manager(self) -> Any:
        """Return the injected SelectionManager."""
        self._ensure_not_disposed()
        if self.selection_manager is None:
            raise RuntimeError("selection_manager is not configured.")
        return self.selection_manager

    def get_snap_system(self) -> Any:
        """Return the injected SnapSystem."""
        self._ensure_not_disposed()
        if self.snap_system is None:
            raise RuntimeError("snap_system is not configured.")
        return self.snap_system

    def get_controller(self) -> Any:
        """Return the authoritative application controller."""
        self._ensure_not_disposed()
        return self.controller

    @staticmethod
    def event_position(event: Any) -> Any:
        """Extract an event position without a concrete Qt dependency."""
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
        """Detect Escape using symbolic or Qt-compatible integer values."""
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
        """Return a diagnostic snapshot of this tool."""
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "active": self._active,
            "disposed": self._disposed,
            "has_command_manager": self.command_manager is not None,
            "has_selection_manager": self.selection_manager is not None,
            "has_snap_system": self.snap_system is not None,
        }

    def dispose(self) -> None:
        """Dispose the tool and prevent further use."""
        if self._disposed:
            return
        if self._active:
            self.deactivate()
        self.on_dispose()
        self._disposed = True

    def on_dispose(self) -> None:
        """Concrete-tool disposal hook."""

    def _ensure_active(self) -> None:
        """Ensure the tool is active and usable."""
        self._ensure_not_disposed()
        if not self._active:
            raise RuntimeError(f"Tool '{self.tool_id}' is not active.")

    def _ensure_not_disposed(self) -> None:
        """Ensure the tool has not been disposed."""
        if self._disposed:
            raise RuntimeError(f"Tool '{self.tool_id}' has been disposed.")

    def __repr__(self) -> str:
        """Return a concise diagnostic representation."""
        return (
            f"{type(self).__name__}("
            f"id={self.tool_id!r}, "
            f"active={self._active}, "
            f"disposed={self._disposed})"
        )


__all__ = ["ToolBase"]
