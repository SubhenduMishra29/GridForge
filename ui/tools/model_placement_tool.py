# ============================================================
# File: ui/tools/model_placement_tool.py
# GridForge V2 — Model Placement Tool
# Author: Subhendu Mishra
# ============================================================
"""Shared UI-only placement behavior for concrete model tools."""

from __future__ import annotations

from typing import Any, Optional, Tuple
from uuid import uuid4

from .endpoint_identity_adapter import EndpointIdentityAdapter

from .tool_base import ToolBase


class ModelPlacementTool(ToolBase):
    """Reusable placement interaction for concrete SLD model tools."""

    MODEL_NAME = "Model"
    TOOL_ID = "model"
    COMMAND_CLASS = None
    ID_FIELD = "equipment_id"
    ENDPOINT_FIELDS: tuple[str, ...] = ()
    COMMAND_DEFAULTS: dict[str, Any] = {}
    ENDPOINT_ROLE_MAP: dict[str, str] = {}

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
        self._position: Optional[Tuple[float, float]] = None
        self._preview_active = False
        self._endpoints: list[Any] = []
        self._endpoint_by_field: dict[str, Any] = {}

    @property
    def tool_id(self) -> str:
        return self.TOOL_ID

    @property
    def name(self) -> str:
        return self.MODEL_NAME

    @property
    def description(self) -> str:
        return f"Place a {self.MODEL_NAME.lower()} on the SLD canvas."

    def on_activate(self) -> None:
        self._clear_state()

    def on_deactivate(self) -> None:
        self._clear_state()

    def on_mouse_press(self, event: Any) -> bool:
        self._ensure_active()
        snap_result = self._snap_result(event)
        if snap_result is None:
            return False
        self._position = self._position_tuple(snap_result.position)
        self._preview_active = True
        if self.ENDPOINT_FIELDS:
            endpoint = EndpointIdentityAdapter.from_snap_result(snap_result)
            terminal_name = getattr(snap_result, "terminal_name", None)
            if self.ENDPOINT_ROLE_MAP:
                if not isinstance(terminal_name, str) or terminal_name not in self.ENDPOINT_ROLE_MAP:
                    raise ValueError(f"{self.MODEL_NAME} requires an explicit supported terminal role.")
                field = self.ENDPOINT_ROLE_MAP[terminal_name]
                if field in self._endpoint_by_field:
                    raise ValueError(f"{self.MODEL_NAME} terminal role {terminal_name!r} was already selected.")
                self._endpoint_by_field[field] = endpoint
                self._endpoints = list(self._endpoint_by_field.values())
            else:
                if endpoint in self._endpoints:
                    raise ValueError(f"{self.MODEL_NAME} requires distinct endpoint references.")
                self._endpoints.append(endpoint)
            if len(self._endpoints) < len(self.ENDPOINT_FIELDS):
                return True
        command = self._build_command()
        self.execute_command(command)
        self._clear_state()
        return True

    def on_mouse_move(self, event: Any) -> bool:
        self._ensure_active()
        position = self._snap_position(event)
        if position is None:
            return False
        self._position = position
        self._preview_active = True
        return True

    def on_mouse_release(self, event: Any) -> bool:
        self._ensure_active()
        position = self._snap_position(event)
        if position is None:
            self._clear_state()
            return False
        self._position = position
        return False

    def on_mouse_double_click(self, event: Any) -> bool:
        return self.on_mouse_press(event)

    def on_key_press(self, event: Any) -> bool:
        self._ensure_active()
        if self._is_escape_event(event):
            return self.on_cancel()
        return False

    def on_cancel(self) -> bool:
        self._ensure_active()
        had_state = self._preview_active or self._position is not None
        self._clear_state()
        return had_state

    def on_reset(self) -> None:
        self._ensure_active()
        self._clear_state()

    def _snap_result(self, event: Any) -> Any:
        scene_position = self.event_position(event)
        snap = getattr(self.get_snap_system(), "snap", None)
        if not callable(snap):
            raise TypeError("SnapSystem must provide snap().")
        result = snap(scene_position, allow_grid=True, allow_object=True)
        if getattr(result, "position", None) is None:
            return None
        return result

    def _snap_position(self, event: Any) -> Optional[Tuple[float, float]]:
        result = self._snap_result(event)
        position = getattr(result, "position", None) if result is not None else None
        if position is None:
            return None
        return self._position_tuple(position)

    def _build_command(self) -> Any:
        command_class = self.COMMAND_CLASS
        if command_class is None:
            raise RuntimeError(f"{self.MODEL_NAME} tool has no Application command constructor.")
        if len(self.ENDPOINT_FIELDS) != len(self._endpoints):
            raise RuntimeError(f"{self.MODEL_NAME} placement is missing required endpoint references.")
        payload = dict(self.COMMAND_DEFAULTS)
        payload[self.ID_FIELD] = f"{self.TOOL_ID}-{uuid4().hex}"
        if self._position is None:
            raise RuntimeError(f"{self.MODEL_NAME} placement has no committed position.")
        payload["presentation_x"] = float(self._position[0])
        payload["presentation_y"] = float(self._position[1])
        if self.ENDPOINT_ROLE_MAP:
            payload.update(self._endpoint_by_field)
        else:
            payload.update(dict(zip(self.ENDPOINT_FIELDS, self._endpoints)))
        return command_class(**payload)

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
        self._position = None
        self._preview_active = False
        self._endpoints.clear()
        self._endpoint_by_field.clear()

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state.update({"position": self._position, "preview_active": self._preview_active})
        return state


__all__ = ["ModelPlacementTool"]
