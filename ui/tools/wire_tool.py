# ============================================================
# File: ui/tools/wire_tool.py
# GridForge V2 — Simple Wired Connection Tool
# Author: Subhendu Mishra
# ============================================================
"""Create a logical terminal-to-terminal connection without Line/Cable semantics."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from core.application.commands.simple_wire_commands import CreateSimpleWireConnectionCommand

from .endpoint_identity_adapter import EndpointIdentityAdapter
from .tool_base import ToolBase


class WireTool(ToolBase):
    """Capture two terminal endpoints and submit one canonical connection command."""

    TOOL_ID = "wire"

    def __init__(self, controller: Any, application: Any, selection_manager: Any, snap_system: Any, preview_layer: Any = None) -> None:
        super().__init__(controller=controller, application=application, selection_manager=selection_manager, snap_system=snap_system)
        self._start_position: Optional[Tuple[float, float]] = None
        self._current_position: Optional[Tuple[float, float]] = None
        self._start_endpoint: Any = None
        self._current_endpoint: Any = None
        self._preview_active = False
        self._preview_layer = preview_layer or getattr(controller, "preview_layer", None)

    @property
    def tool_id(self) -> str:
        return self.TOOL_ID

    @property
    def name(self) -> str:
        return "Simple Wired Connection"

    @property
    def description(self) -> str:
        return "Connect two SLD terminals without creating a Line or Cable object."

    def on_activate(self) -> None:
        self._clear_state()

    def on_deactivate(self) -> None:
        self._clear_state()

    def on_mouse_press(self, event: Any) -> bool:
        self._ensure_active()
        snap_result = self._snap(event)
        if snap_result is None:
            return False
        position = self._position_tuple(snap_result.position)
        endpoint = EndpointIdentityAdapter.from_snap_result(snap_result)
        if self._start_endpoint is None:
            self._start_endpoint = endpoint
            self._start_position = position
            self._current_endpoint = endpoint
            self._current_position = position
            self._preview_active = True
            self._show_preview()
            return True
        self._current_endpoint = endpoint
        self._current_position = position
        self._execute_connection(self._start_endpoint, self._current_endpoint)
        self._clear_state()
        return True

    def on_mouse_move(self, event: Any) -> bool:
        self._ensure_active()
        if self._start_endpoint is None:
            return False
        snap_result = self._snap(event)
        if snap_result is None:
            return False
        self._current_position = self._position_tuple(snap_result.position)
        self._current_endpoint = EndpointIdentityAdapter.from_snap_result(snap_result)
        self._preview_active = True
        self._show_preview()
        return True

    def on_mouse_release(self, event: Any) -> bool:
        self._ensure_active()
        return self._start_endpoint is not None

    def on_mouse_double_click(self, event: Any) -> bool:
        return self.on_mouse_press(event)

    def on_key_press(self, event: Any) -> bool:
        self._ensure_active()
        if self._is_escape_event(event):
            return self.on_cancel()
        return False

    def on_cancel(self) -> bool:
        self._ensure_active()
        had_state = self._start_endpoint is not None or self._preview_active
        self._clear_state()
        return had_state

    def on_reset(self) -> None:
        self._ensure_active()
        self._clear_state()

    def _snap(self, event: Any) -> Any:
        scene_position = self.event_position(event)
        snap = getattr(self.get_snap_system(), "snap", None)
        if not callable(snap):
            raise TypeError("SnapSystem must provide snap().")
        result = snap(scene_position, allow_grid=True, allow_object=True)
        if getattr(result, "position", None) is None:
            return None
        return result

    def _execute_connection(self, endpoint_from: Any, endpoint_to: Any) -> Any:
        if not getattr(endpoint_from, "is_terminal", False) or not getattr(endpoint_to, "is_terminal", False):
            raise ValueError("Simple Wired Connection requires two terminal snaps.")
        command = CreateSimpleWireConnectionCommand(endpoint_a=endpoint_from, endpoint_b=endpoint_to)
        return self.execute_command(command)

    def _show_preview(self) -> None:
        layer = self._preview_layer
        if layer is None or not callable(getattr(layer, "show_segment", None)):
            return
        if self._start_position is None or self._current_position is None:
            return
        layer.show_segment(self._start_position, self._current_position)

    @staticmethod
    def _position_tuple(position: Any) -> Tuple[float, float]:
        if hasattr(position, "x") and hasattr(position, "y"):
            return float(position.x()), float(position.y())
        if isinstance(position, (tuple, list)) and len(position) >= 2:
            return float(position[0]), float(position[1])
        raise TypeError("SnapResult.position must provide x/y coordinates or a two-element position.")

    @staticmethod
    def _is_escape_event(event: Any) -> bool:
        if event is None:
            return False
        key = getattr(event, "key", None)
        if callable(key):
            key = key()
        if isinstance(event, dict):
            key = event.get("key", key)
        return key in ("Escape", "escape", 0x01000000)

    def _clear_state(self) -> None:
        if self._preview_layer is not None and callable(getattr(self._preview_layer, "clear", None)):
            self._preview_layer.clear()
        self._start_position = None
        self._current_position = None
        self._start_endpoint = None
        self._current_endpoint = None
        self._preview_active = False

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state.update({
            "start_position": self._start_position,
            "current_position": self._current_position,
            "start_endpoint": self._start_endpoint,
            "current_endpoint": self._current_endpoint,
            "preview_active": self._preview_active,
        })
        return state


__all__ = ["WireTool"]
