# ============================================================
# GridForge V2 — Electrical Insertion Interaction Tool
# ============================================================

"""Transient UI interaction for dropping insertion-capable equipment onto a Simple Wire."""

from __future__ import annotations

from typing import Any, Mapping

from core.application.commands.insertion_commands import InsertEquipmentIntoConnectionCommand
from core.application.services.insertion_contract import INSERTION_CONTRACTS
from .tool_base import ToolBase


class ElectricalInsertionTool(ToolBase):
    """UI-only gesture coordinator; it never mutates Core or persistent SLD state."""

    TOOL_ID = "electrical-insertion"

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
        self._equipment_type: str | None = None
        self._equipment_id: str | None = None
        self._creation_parameters: dict[str, Any] = {}
        self._orientation = 0.0
        self._target: dict[str, Any] | None = None
        self._target_item: Any | None = None

    @property
    def tool_id(self) -> str:
        return self.TOOL_ID

    @property
    def name(self) -> str:
        return "Insert Equipment"

    def begin(
        self,
        equipment_type: str,
        *,
        equipment_id: str | None = None,
        creation_parameters: Mapping[str, Any] | None = None,
        orientation: float = 0.0,
    ) -> None:
        equipment_type = str(equipment_type).strip().lower()
        if equipment_type not in INSERTION_CONTRACTS:
            raise ValueError(f"Equipment type {equipment_type!r} is not insertion-capable.")
        self._equipment_type = equipment_type
        self._equipment_id = equipment_id
        self._creation_parameters = dict(creation_parameters or {})
        self._orientation = float(orientation)
        self._target = None
        self._target_item = None

    def on_activate(self) -> None:
        self._clear_target()

    def on_deactivate(self) -> None:
        self._clear_target()

    def on_mouse_move(self, event: Any) -> bool:
        self._ensure_active()
        target = self._resolve_target(event)
        if target is None:
            self._clear_target()
            return False
        self._set_target(target)
        return True

    def on_mouse_release(self, event: Any) -> bool:
        self._ensure_active()
        if self._equipment_type is None:
            return False
        target = self._resolve_target(event) or self._target
        if target is None:
            return False
        contract = INSERTION_CONTRACTS[self._equipment_type]
        missing = tuple(
            field for field in contract.required_parameters
            if self._creation_parameters.get(field) is None
        )
        if missing:
            self._report_feedback(
                "Missing engineering parameters: " + ", ".join(missing)
            )
            return False
        command = InsertEquipmentIntoConnectionCommand(
            connection_id=str(target["connection_id"]),
            equipment_type=self._equipment_type,
            equipment_id=self._equipment_id,
            insertion_position=tuple(target["closest_point"]),
            orientation=self._orientation,
            terminal_mapping=None,
            creation_parameters=self._creation_parameters,
            segment_index=int(target["segment_index"]),
        )
        result = self.execute_command(command)
        if not getattr(result, "success", False):
            self._report_feedback(getattr(result, "message", "Electrical insertion failed."))
            return False
        equipment_id = str(result.metadata.get("equipment_id"))
        self.get_selection_manager().select_single(equipment_id)
        self._report_feedback(f"{self._equipment_type} inserted into existing wire.")
        self._clear_target()
        return True

    def on_key_press(self, event: Any) -> bool:
        if self._is_escape_event(event):
            self._clear_target()
            return True
        return False

    def on_cancel(self) -> bool:
        had_target = self._target is not None
        self._clear_target()
        return had_target

    def _resolve_target(self, event: Any) -> dict[str, Any] | None:
        position = self._position_tuple(self.event_position(event))
        item = event.get("connection_item") if isinstance(event, dict) else None
        if item is None:
            for name in ("connection_item_at", "sld_connection_item_at", "canvas_item_at"):
                resolver = getattr(self.controller, name, None)
                if callable(resolver):
                    item = resolver(position)
                    if item is not None:
                        break
        if item is None:
            return None
        resolver = getattr(item, "insertion_target", None)
        if not callable(resolver):
            return None
        target = resolver(position)
        if not isinstance(target, dict) or not target.get("connection_id"):
            return None
        self._target_item = item
        return target

    def _set_target(self, target: dict[str, Any]) -> None:
        if self._target == target:
            return
        self._clear_target_visual()
        self._target = target
        if self._target_item is not None:
            setter = getattr(self._target_item, "set_visual_state", None)
            if callable(setter):
                setter("selected")

    def _clear_target_visual(self) -> None:
        if self._target_item is not None:
            setter = getattr(self._target_item, "set_visual_state", None)
            if callable(setter):
                setter("normal")

    def _clear_target(self) -> None:
        self._clear_target_visual()
        self._target = None
        self._target_item = None

    def _report_feedback(self, message: str) -> None:
        for name in ("show_status_message", "set_status_message", "notify_user"):
            callback = getattr(self.controller, name, None)
            if callable(callback):
                callback(message)
                return

    @staticmethod
    def _position_tuple(position: Any) -> tuple[float, float]:
        if hasattr(position, "x") and hasattr(position, "y"):
            return float(position.x()), float(position.y())
        if isinstance(position, (tuple, list)) and len(position) >= 2:
            return float(position[0]), float(position[1])
        raise TypeError("Scene position must expose x/y coordinates.")


__all__ = ["ElectricalInsertionTool"]
