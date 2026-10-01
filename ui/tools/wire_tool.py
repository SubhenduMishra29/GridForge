# ============================================================
# File: ui/tools/wire_tool.py
# GridForge V2 — Simple Wired Connection Tool
# Author: Subhendu Mishra
# ============================================================
"""Create a logical endpoint-to-endpoint connection without Line/Cable semantics."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from core.application.commands.simple_wire_commands import CreateSimpleWireConnectionCommand

from ui.connections.connection_preview import ConnectionPreview

from .endpoint_identity_adapter import EndpointIdentityAdapter
from ui.core.snap_system import SnapType
from .tool_base import ToolBase


class WireTool(ToolBase):
    """Capture two valid electrical endpoints and submit one canonical connection command."""

    TOOL_ID = "wire"

    def __init__(self, controller: Any, application: Any, selection_manager: Any, snap_system: Any, preview_layer: Any = None) -> None:
        super().__init__(controller=controller, application=application, selection_manager=selection_manager, snap_system=snap_system)
        self._start_position: Optional[Tuple[float, float]] = None
        self._start_snap: Any = None
        self._current_position: Optional[Tuple[float, float]] = None
        self._last_snap_result: Any = None
        self._last_command_result: Any = None
        self._preview = ConnectionPreview()
        self._preview_layer = preview_layer or getattr(controller, "preview_layer", None)

    @property
    def tool_id(self) -> str:
        return self.TOOL_ID

    @property
    def name(self) -> str:
        return "Simple Wired Connection"

    @property
    def description(self) -> str:
        return "Connect two SLD endpoints without creating a Line or Cable object."

    def on_activate(self) -> None:
        self._clear_state()

    def on_deactivate(self) -> None:
        self._clear_state()

    def on_mouse_press(self, event: Any) -> bool:
        self._ensure_active()
        snap_result = self._snap(event)
        self._last_snap_result = snap_result
        if snap_result is None:
            return False
        if getattr(snap_result, "snap_type", None) is not SnapType.OBJECT:
            return False
        position = self._position_tuple(snap_result.position)
        endpoint = EndpointIdentityAdapter.from_snap_result(snap_result)
        if self._preview.source_endpoint is None:
            self._preview.begin(endpoint)
            self._start_snap = snap_result
            self._start_position = position
            self._current_position = position
            self._preview.update_cursor(position)
            self._show_preview()
            return True
        self._current_position = position
        self._preview.update_target(endpoint, valid=True)
        self._preview.update_cursor(position)
        result = self._execute_connection(
            *self._preview.get_endpoint_pair(),
            source_snap=self._start_snap,
            target_snap=snap_result,
        )
        self._last_command_result = result
        if not getattr(result, "success", False):
            # A failed Application command is not a committed connection.
            # Keep the routing preview alive so the user can retry or cancel.
            return False
        self._clear_state()
        return True

    def on_mouse_move(self, event: Any) -> bool:
        self._ensure_active()
        if self._preview.source_endpoint is None:
            return False
        snap_result = self._snap(event)
        self._last_snap_result = snap_result
        if snap_result is None:
            return False

        position = self._position_tuple(snap_result.position)
        self._current_position = position
        self._preview.update_cursor(position)

        # Grid/none snaps are valid cursor positions but are not electrical
        # endpoints. Never pass them to EndpointIdentityAdapter: the adapter
        # deliberately rejects missing object identity so that presentation
        # geometry cannot be promoted into an electrical connection.
        if getattr(getattr(snap_result, "snap_type", None), "name", None) != "OBJECT":
            self._preview.update_target(
                None,
                valid=False,
                reason="Move the cursor onto a stable electrical object endpoint.",
            )
            self._show_preview()
            return True

        endpoint = EndpointIdentityAdapter.from_snap_result(snap_result)
        self._preview.update_target(endpoint, valid=True)
        self._show_preview()
        return True

    def on_mouse_release(self, event: Any) -> bool:
        self._ensure_active()
        return self._preview.source_endpoint is not None

    def on_mouse_double_click(self, event: Any) -> bool:
        return self.on_mouse_press(event)

    def on_key_press(self, event: Any) -> bool:
        self._ensure_active()
        if self._is_escape_event(event):
            return self.on_cancel()
        return False

    def on_cancel(self) -> bool:
        self._ensure_active()
        had_state = self._preview.source_endpoint is not None
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

    def _execute_connection(self, endpoint_from: Any, endpoint_to: Any, *, source_snap: Any, target_snap: Any) -> Any:
        del source_snap, target_snap
        if endpoint_from is None or endpoint_to is None:
            raise ValueError("WireTool requires two canonical electrical endpoint references.")
        if endpoint_from == endpoint_to:
            self._preview.update_target(
                endpoint_to,
                valid=False,
                reason="Choose a different electrical endpoint.",
            )
            self._show_preview()
            return None
        command = CreateSimpleWireConnectionCommand(
            endpoint_a=endpoint_from,
            endpoint_b=endpoint_to,
        )
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
        if self._preview_layer is not None:
            clear_preview = getattr(self._preview_layer, "clear_preview", None)
            if callable(clear_preview):
                clear_preview()
            else:
                clear = getattr(self._preview_layer, "clear", None)
                if callable(clear):
                    clear()
        self._start_position = None
        self._start_snap = None
        self._current_position = None
        self._last_snap_result = None
        self._last_command_result = None
        self._preview.reset()

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state.update({
            "start_position": self._start_position,
            "current_position": self._current_position,
            "preview": self._preview.get_state(),
            "last_snap_result": self._last_snap_result,
            "last_command_result": self._last_command_result,
        })
        return state


__all__ = ["WireTool"]
