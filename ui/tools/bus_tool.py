# ============================================================
# GridForge V2
# Author: Subhendu Mishra
# ============================================================
# File:
#     ui/tools/bus_tool.py
#
# Purpose:
#     SLD bus-placement interaction tool.
# ============================================================

from __future__ import annotations

from typing import Any, Optional, Tuple
from uuid import uuid4

from ui.sld.bus_presentation import DEFAULT_SLD_BUS_PRESENTATION
from ui.creation.creation_context import CreationContext
from ui.creation.command_factory import CreationCommandFactory

from .tool_base import ToolBase


class BusTool(ToolBase):
    """SLD bus-placement interaction tool."""

    TOOL_ID = "bus"

    def __init__(
        self,
        controller: Any,
        application: Any,
        selection_manager: Any,
        snap_system: Any,
        preview_layer: Any = None,
    ) -> None:
        super().__init__(
            controller=controller,
            application=application,
            selection_manager=selection_manager,
            snap_system=snap_system,
        )
        self._position: Optional[Tuple[float, float]] = None
        self._preview_active = False
        self._preview_layer = preview_layer
        self._creation_context: CreationContext | None = None

    def bind_creation_context(self, creation_context: CreationContext) -> None:
        if not isinstance(creation_context, CreationContext):
            raise TypeError("creation_context must be a CreationContext.")
        self._creation_context = creation_context

    def _require_creation_context(self) -> CreationContext:
        if self._creation_context is None:
            raise RuntimeError("BusTool is not bound to CreationContext.")
        return self._creation_context

    @property
    def tool_id(self) -> str:
        return self.TOOL_ID

    @property
    def name(self) -> str:
        return "Bus"

    @property
    def description(self) -> str:
        return "Place a bus on the SLD canvas."

    def on_activate(self) -> None:
        self._clear_state()

    def on_deactivate(self) -> None:
        self._clear_state()

    def on_mouse_press(self, event: Any) -> bool:
        self._ensure_active()
        position = self._snap_position(event)
        if position is None:
            return False
        self._position = position
        self._preview_active = True
        self._show_preview(position)
        return True

    def on_mouse_move(self, event: Any) -> bool:
        self._ensure_active()
        position = self._snap_position(event)
        if position is None:
            return False
        self._position = position
        self._preview_active = True
        self._show_preview(position)
        return True

    def on_mouse_release(self, event: Any) -> bool:
        self._ensure_active()
        position = self._snap_position(event)
        if position is None:
            self._clear_state()
            return False
        self._position = position
        draft = self._require_creation_context().set_placement(position)
        self._preview_active = True
        self._show_preview(position)
        if not draft.validate_for_commit():
            return False
        draft.mark_committing()
        intent = CreationCommandFactory.build(
            draft,
            object_id=f"bus-{uuid4().hex}",
            position=position,
        )
        try:
            command = self.application.prepare_creation_command(intent)
        except Exception as exc:
            self._report_feedback(
                f"COMMAND_PREPARATION_FAILED: equipment=Bus id={intent.object_id} "
                f"command={intent.command_type} message={exc}"
            )
            return False
        try:
            result = self.execute_command(command)
        except Exception as exc:
            self._report_feedback(
                f"COMMAND_EXECUTION_FAILED: equipment=Bus id={intent.object_id} "
                f"command={command.command_type} message={exc}"
            )
            return False
        if not result.success:
            self._report_feedback(
                f"COMMAND_EXECUTION_FAILED: equipment=Bus id={intent.object_id} "
                f"command={command.command_type} message={result.message}"
            )
            return False
        created_id = intent.object_id
        self._require_creation_context().complete()
        self._clear_state()
        selector = getattr(self.selection_manager, "select_single", None)
        if callable(selector):
            selector(created_id)
        return True
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

    def _snap_position(self, event: Any) -> Optional[Tuple[float, float]]:
        scene_position = self.event_position(event)
        snap_system = self.get_snap_system()
        snap = getattr(snap_system, "snap", None)
        if not callable(snap):
            raise TypeError("SnapSystem must provide snap().")
        result = snap(scene_position, allow_grid=True, allow_object=True)
        position = getattr(result, "position", None)
        if position is None:
            return None
        return self._position_tuple(position)

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

    def _show_preview(self, position: Tuple[float, float]) -> None:
        if self._preview_layer is None:
            return
        show_bus = getattr(self._preview_layer, "show_bus", None)
        if callable(show_bus):
            show_bus(position, presentation=DEFAULT_SLD_BUS_PRESENTATION)

    def _report_feedback(self, message: str) -> None:
        for name in ("show_status_message", "set_status_message", "notify_user"):
            callback = getattr(self.controller, name, None)
            if callable(callback):
                callback(message)
                return
    def _clear_state(self) -> None:
        self._position = None
        self._preview_active = False
        if self._preview_layer is not None:
            clear_preview = getattr(self._preview_layer, "clear_preview", None)
            if callable(clear_preview):
                clear_preview()
            else:
                clear = getattr(self._preview_layer, "clear", None)
                if callable(clear):
                    clear()

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state.update({"position": self._position, "preview_active": self._preview_active})
        return state


__all__ = ["BusTool"]
