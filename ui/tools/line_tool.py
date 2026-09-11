# ============================================================
# File: ui/tools/line_tool.py
# GridForge V2 — Line Tool
# Author: Subhendu Mishra
# ============================================================
"""SLD line-connection interaction tool."""

from __future__ import annotations

from typing import Any, Optional, Tuple
from uuid import uuid4

from core.application.commands.model_commands import CreateLineCommand

from .endpoint_identity_adapter import EndpointIdentityAdapter
from .tool_base import ToolBase


class LineTool(ToolBase):
    """Capture endpoint identities and execute CreateLineCommand."""

    TOOL_ID = "line"

    def __init__(
        self,
        controller: Any,
        application: Any,
        selection_manager: Any,
        snap_system: Any,
    ) -> None:
        super().__init__(
            controller=controller,
            application=application,
            selection_manager=selection_manager,
            snap_system=snap_system,
        )
        self._start_position: Optional[Tuple[float, float]] = None
        self._current_position: Optional[Tuple[float, float]] = None
        self._start_endpoint: Any = None
        self._current_endpoint: Any = None
        self._preview_active = False
        self._engineering_parameters: dict[str, Any] = {}

    @property
    def tool_id(self) -> str:
        return self.TOOL_ID

    @property
    def name(self) -> str:
        return "Line"

    @property
    def description(self) -> str:
        return "Create a connection between two SLD endpoints."

    def set_engineering_parameters(self, **parameters: Any) -> None:
        """Store UI-entered line configuration until command creation."""
        if not parameters:
            raise ValueError("Line engineering parameters must not be empty.")
        self._engineering_parameters = dict(parameters)

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
            return True
        self._current_endpoint = endpoint
        self._current_position = position
        self._execute_line_command(self._start_endpoint, self._current_endpoint)
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

    def _execute_line_command(self, endpoint_from: Any, endpoint_to: Any) -> Any:
        parameters = self._engineering_parameters
        required = ("resistance_ohm", "reactance_ohm", "rate_mva")
        missing = [name for name in required if name not in parameters]
        if missing:
            raise RuntimeError(
                "Line engineering parameters are incomplete: " + ", ".join(missing)
            )
        command = CreateLineCommand(
            line_id=f"line-{uuid4().hex}",
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            resistance_ohm=float(parameters["resistance_ohm"]),
            reactance_ohm=float(parameters["reactance_ohm"]),
            shunt_susceptance_siemens=float(parameters.get("shunt_susceptance_siemens", 0.0)),
            name=str(parameters.get("name", "")),
            rate_mva=float(parameters["rate_mva"]),
        )
        return self.execute_command(command)

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
            "has_engineering_parameters": bool(self._engineering_parameters),
        })
        return state


__all__ = ["LineTool"]
