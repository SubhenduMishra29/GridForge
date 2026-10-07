# ============================================================
# GridForge V2 — Electrical Insertion Interaction Tool
# ============================================================

"""Transient UI interaction for dropping insertion-capable equipment onto a Simple Wire."""

from __future__ import annotations

import math
from typing import Any, Mapping

from core.application.commands.insertion_commands import InsertEquipmentIntoConnectionCommand
from core.application.services.insertion_contract import INSERTION_CONTRACTS
from ui.canvas.symbol_preview_item import SymbolPreviewItem
from ui.core.qt import QGraphicsLineItem, QLineF, QPointF
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
        preview_layer: Any = None,
        symbol_registry: Any = None,
    ) -> None:
        super().__init__(
            controller=controller,
            application=application,
            selection_manager=selection_manager,
            snap_system=snap_system,
        )
        self._preview_layer = preview_layer
        self._symbol_registry = symbol_registry
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

    def begin(self, equipment_type: str, *, equipment_id: str | None = None,
              creation_parameters: Mapping[str, Any] | None = None,
              orientation: float = 0.0) -> None:
        equipment_type = str(equipment_type).strip().lower()
        if equipment_type not in INSERTION_CONTRACTS:
            raise ValueError(f"Equipment type {equipment_type!r} is not insertion-capable.")
        self._equipment_type = equipment_type
        self._equipment_id = equipment_id
        self._creation_parameters = dict(creation_parameters or {})
        self._orientation = float(orientation)
        self._clear_target()

    def insertion_target(self, event: Any) -> dict[str, Any] | None:
        return self._resolve_target(event)

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
        anchors = self._terminal_anchors()
        required_roles = INSERTION_CONTRACTS[self._equipment_type].terminal_mapping
        missing_anchors = tuple(role for role in required_roles if role not in anchors)
        if missing_anchors:
            self._report_feedback(
                "Insertion symbol definition is missing terminal anchors: "
                + ", ".join(missing_anchors)
            )
            return False
        command = InsertEquipmentIntoConnectionCommand(
            connection_id=str(target["connection_id"]),
            equipment_type=self._equipment_type,
            equipment_id=self._equipment_id,
            insertion_position=tuple(target["closest_point"]),
            orientation=self._orientation,
            terminal_mapping=INSERTION_CONTRACTS[self._equipment_type].terminal_mapping,
            creation_parameters=self._creation_parameters,
            segment_index=int(target["segment_index"]),
            terminal_anchors=anchors,
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
        return dict(target)

    def _set_target(self, target: dict[str, Any]) -> None:
        if self._target == target:
            self._show_preview(target)
            return
        self._clear_target_visual()
        self._target = target
        self._show_preview(target)
        if self._target_item is not None:
            setter = getattr(self._target_item, "set_visual_state", None)
            if callable(setter):
                setter("preview")

    def _show_preview(self, target: dict[str, Any]) -> None:
        if self._preview_layer is None or self._equipment_type is None:
            return
        clear = getattr(self._preview_layer, "clear", None)
        if callable(clear):
            clear()
        position = tuple(target["closest_point"])
        anchors = self._terminal_anchors()
        mapping = INSERTION_CONTRACTS[self._equipment_type].terminal_mapping
        input_anchor = self._rotated_anchor(anchors.get(mapping[0]), position)
        output_anchor = self._rotated_anchor(anchors.get(mapping[1]), position)
        source = tuple(target.get("source", position))
        destination = tuple(target.get("target", position))
        route = [tuple(point) for point in target.get("route", ())]
        segment = int(target.get("segment_index", 0))
        polyline = [source, *route, destination]
        if segment >= len(polyline) - 1:
            return
        first = [*polyline[:segment + 1], position, input_anchor]
        second = [output_anchor, position, *polyline[segment + 1:]]
        items = []
        for points in (first, second):
            for a, b in zip(points, points[1:]):
                items.append(QGraphicsLineItem(QLineF(QPointF(*a), QPointF(*b))))
        definition = self._symbol_definition()
        if definition is not None:
            items.append(SymbolPreviewItem(
                definition,
                position=position,
                rotation=self._orientation,
                terminal_names=mapping,
                element_type=self._equipment_type,
            ))
        add_items = getattr(self._preview_layer, "add_items", None)
        if callable(add_items):
            add_items(items)

    def _terminal_anchors(self) -> dict[str, tuple[float, float]]:
        definition = self._symbol_definition()
        if definition is None or self._equipment_type is None:
            return {}
        return {
            str(role): tuple(definition.get_terminal_anchor(role))
            for role in INSERTION_CONTRACTS[self._equipment_type].terminal_mapping
            if definition.has_terminal_anchor(role)
        }

    def _symbol_definition(self) -> Any | None:
        registry = self._symbol_registry
        if registry is None or self._equipment_type is None:
            return None
        require = getattr(registry, "require", None)
        if not callable(require):
            return None
        try:
            return require(self._equipment_type)
        except KeyError:
            return None

    def _rotated_anchor(self, anchor: tuple[float, float] | None,
                        position: tuple[float, float]) -> tuple[float, float]:
        if anchor is None:
            return position
        lx, ly = float(anchor[0]), float(anchor[1])
        radians = math.radians(self._orientation)
        return (
            position[0] + lx * math.cos(radians) - ly * math.sin(radians),
            position[1] + lx * math.sin(radians) + ly * math.cos(radians),
        )

    def _clear_target_visual(self) -> None:
        if self._target_item is not None:
            setter = getattr(self._target_item, "set_visual_state", None)
            if callable(setter):
                setter("normal")
        if self._preview_layer is not None:
            clear = getattr(self._preview_layer, "clear", None)
            if callable(clear):
                clear()

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
