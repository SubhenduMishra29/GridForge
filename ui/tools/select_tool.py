# ============================================================
# GridForge V2
# File: ui/tools/select_tool.py
# Purpose: Canonical SLD selection, box-selection, and drag-move.
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from typing import Any, Optional, Tuple

from core.application.commands.sld_commands import SetSLDNodePositionCommand
from core.application.services.insertion_contract import INSERTION_CONTRACTS
from .electrical_insertion_tool import ElectricalInsertionTool
from ui.core.qt import QPointF
from .tool_base import ToolBase


class SelectTool(ToolBase):
    """Canonical transient SLD selection and presentation-move tool."""

    TOOL_ID = "select"
    SHIFT_MODIFIER = 0x02000000
    CTRL_MODIFIER = 0x04000000
    META_MODIFIER = 0x10000000
    DRAG_TOLERANCE = 3.0

    def __init__(self, controller: Any, application: Any, selection_manager: Any, snap_system: Any) -> None:
        super().__init__(controller=controller, application=application,
                         selection_manager=selection_manager, snap_system=snap_system)
        self._pressed_object_id: Any = None
        self._pressed_scene_position: Optional[Tuple[float, float]] = None
        self._dragging = False
        self._insertion_active = False
        self._insertion_tool: ElectricalInsertionTool | None = None
        self._insertion_target: dict[str, Any] | None = None
        self._original_drag_position: Tuple[float, float] | None = None

    @property
    def tool_id(self) -> str:
        return self.TOOL_ID

    @property
    def name(self) -> str:
        return "Select"

    @property
    def description(self) -> str:
        return "Select, box-select, and drag-move SLD objects."

    def on_activate(self) -> None:
        self._clear_pointer_state()

    def on_deactivate(self) -> None:
        self._cancel_transient_insertion()
        self._clear_pointer_state()

    def on_mouse_press(self, event: Any) -> bool:
        self._ensure_active()
        self._pressed_object_id = self._event_object_id(event)
        self._pressed_scene_position = self._xy(self._event_scene_position(event))
        self._dragging = False
        modifiers = self._event_modifiers(event)
        if self._pressed_object_id is None:
            if not self._has_additive_modifier(modifiers) and not self._has_toggle_modifier(modifiers):
                self.get_selection_manager().clear()
        else:
            self._handle_object_click(self._pressed_object_id, modifiers)
        return True

    def on_mouse_move(self, event: Any) -> bool:
        self._ensure_active()
        if self._pressed_scene_position is None:
            return False
        current = self._xy(self._event_scene_position(event))
        self._dragging = self._dragging or (
            self._distance(self._pressed_scene_position, current) >= self.DRAG_TOLERANCE
        )
        if not self._dragging or self._pressed_object_id is None:
            return self._dragging
        equipment_type = self._equipment_type_for(self._pressed_object_id)
        if equipment_type not in INSERTION_CONTRACTS:
            return True
        target = self._resolve_insertion_target(current)
        if target is not None:
            if not self._insertion_active:
                self._begin_transient_insertion(equipment_type)
            if self._insertion_tool is not None:
                self._insertion_target = dict(target)
                self._insertion_tool.on_mouse_move(self._insertion_event(current, target))
            return True
        if self._insertion_active:
            self._cancel_transient_insertion()
        return True

    def on_mouse_release(self, event: Any) -> bool:
        self._ensure_active()
        if self._pressed_scene_position is None:
            self._clear_pointer_state()
            return False
        end = self._xy(self._event_scene_position(event))
        if self._dragging:
            if self._pressed_object_id is None:
                self._box_select(self._pressed_scene_position, end, self._event_modifiers(event))
            elif self._is_selected(self._pressed_object_id):
                if self._insertion_active and self._insertion_tool is not None:
                    target = self._resolve_insertion_target(end)
                    if target is not None:
                        self._insertion_target = dict(target)
                        accepted = self._insertion_tool.on_mouse_release(self._insertion_event(end, target))
                        self._finish_transient_insertion()
                        self._clear_pointer_state()
                        return bool(accepted)
                self._commit_drag_move(self._pressed_object_id, end)
        self._cancel_transient_insertion()
        self._clear_pointer_state()
        return True

    def on_key_press(self, event: Any) -> bool:
        self._ensure_active()
        key = self._event_key(event)
        if key in {16777223, 127}:  # Qt.Key_Delete
            dispatch = getattr(self.get_controller(), "delete_selection", None)
            if callable(dispatch):
                dispatch()
            return True
        if key == 16777216:  # Qt.Key_Escape
            return self.on_cancel()
        return False

    def on_cancel(self) -> bool:
        had_state = self._pressed_scene_position is not None or self._dragging or self._insertion_active
        self._cancel_transient_insertion()
        self._clear_pointer_state()
        return had_state

    def _box_select(self, start: Tuple[float, float], end: Tuple[float, float], modifiers: int) -> None:
        scene = self._scene()
        if scene is None:
            return
        left, right = sorted((start[0], end[0]))
        top, bottom = sorted((start[1], end[1]))
        selected: list[Any] = []
        items_method = getattr(scene, "items", None)
        if not callable(items_method):
            return
        for item in tuple(items_method()):
            object_id = getattr(item, "object_id", None)
            if object_id is None:
                continue
            rect_method = getattr(item, "sceneBoundingRect", None)
            if not callable(rect_method):
                continue
            rect = rect_method()
            rx = rect.x() if callable(getattr(rect, "x", None)) else 0.0
            ry = rect.y() if callable(getattr(rect, "y", None)) else 0.0
            rw = rect.width() if callable(getattr(rect, "width", None)) else 0.0
            rh = rect.height() if callable(getattr(rect, "height", None)) else 0.0
            if not (rx + rw < left or rx > right or ry + rh < top or ry > bottom):
                selected.append(object_id)
        manager = self.get_selection_manager()
        additive = self._has_additive_modifier(modifiers)
        toggle = self._has_toggle_modifier(modifiers)
        if not additive and not toggle:
            manager.clear()
        for object_id in selected:
            if toggle:
                manager.toggle_selection(object_id)
            else:
                manager.add_to_selection(object_id)

    def _commit_drag_move(self, object_id: Any, end: Tuple[float, float]) -> None:
        application = self.application
        presentation = getattr(application, "presentation", None)
        model = getattr(presentation, "model", None)
        if model is None:
            return

        start = self._pressed_scene_position
        if start is None:
            return
        snap = getattr(self.get_snap_system(), "snap", None)
        if callable(snap):
            snapped = snap(end, allow_grid=True, allow_object=False, intent="MOVE")
            position = getattr(snapped, "position", None)
            if position is not None:
                end = (float(position.x()), float(position.y()))
        delta_x = end[0] - start[0]
        delta_y = end[1] - start[1]

        selected_ids = tuple(self.get_selection_manager().get_selected_ids())
        if object_id not in selected_ids:
            selected_ids = (object_id,)

        for selected_id in selected_ids:
            node = None
            getter = getattr(model, "get_node_by_equipment_id_optional", None)
            if callable(getter):
                node = getter(str(selected_id))
            if node is None:
                getter = getattr(model, "get_node_optional", None)
                if callable(getter):
                    node = getter(str(selected_id))
            if node is None:
                continue

            result = application.execute(
                SetSLDNodePositionCommand(
                    node_id=str(node.node_id),
                    x=float(node.x) + delta_x,
                    y=float(node.y) + delta_y,
                )
            )
            if not getattr(result, "success", False):
                raise RuntimeError(
                    getattr(result, "message", "Failed to move SLD node.")
                )

    def _equipment_type_for(self, object_id: Any) -> str | None:
        presentation = getattr(self.application, "presentation", None)
        model = getattr(presentation, "model", None)
        if model is None:
            return None
        node = None
        getter = getattr(model, "get_node_by_equipment_id_optional", None)
        if callable(getter):
            node = getter(str(object_id))
        if node is None:
            getter = getattr(model, "get_node_optional", None)
            if callable(getter):
                node = getter(str(object_id))
        if node is None:
            return None
        raw = getattr(node, "element_type", None)
        if raw is None:
            raw = (getattr(node, "properties", {}) or {}).get("element_type")
        return None if raw is None else str(getattr(raw, "value", raw)).strip().lower()

    def _begin_transient_insertion(self, equipment_type: str) -> None:
        tool = self._insertion_tool or self._resolve_insertion_tool()
        if tool is None:
            return
        presentation = getattr(self.application, "presentation", None)
        model = getattr(presentation, "model", None)
        node = None
        if model is not None:
            getter = getattr(model, "get_node_by_equipment_id_optional", None)
            if callable(getter):
                node = getter(str(self._pressed_object_id))
        orientation = float((getattr(node, "properties", {}) or {}).get("rotation", 0.0)) if node is not None else 0.0
        tool.begin(equipment_type, equipment_id=str(self._pressed_object_id), creation_parameters={}, orientation=orientation)
        if not tool.is_active:
            tool.activate()
        self._insertion_tool = tool
        self._insertion_active = True
        self._original_drag_position = self._pressed_scene_position

    def _resolve_insertion_tool(self) -> ElectricalInsertionTool | None:
        manager_getter = getattr(self.controller, "get_tool_manager", None)
        manager = manager_getter() if callable(manager_getter) else getattr(self.controller, "_tool_manager", None)
        if manager is not None:
            for name in ("get_tool", "get", "tool", "find_tool"):
                getter = getattr(manager, name, None)
                if callable(getter):
                    try:
                        candidate = getter(ElectricalInsertionTool.TOOL_ID)
                    except (KeyError, TypeError, ValueError):
                        candidate = None
                    if isinstance(candidate, ElectricalInsertionTool):
                        return candidate
        preview_layer = None
        symbol_registry = None
        for owner in (self.controller, getattr(self.application, "presentation", None)):
            if owner is None:
                continue
            preview_layer = preview_layer or getattr(owner, "preview_layer", None) or getattr(owner, "_preview_layer", None)
            symbol_registry = symbol_registry or getattr(owner, "symbol_registry", None)
        try:
            return ElectricalInsertionTool(controller=self.controller, application=self.application, selection_manager=self.get_selection_manager(), snap_system=self.get_snap_system(), preview_layer=preview_layer, symbol_registry=symbol_registry)
        except (TypeError, ValueError):
            return None

    def _resolve_insertion_target(self, position: Tuple[float, float]) -> dict[str, Any] | None:
        item = self._connection_item_at(position)
        if item is None:
            return None
        resolver = getattr(item, "insertion_target", None)
        if not callable(resolver):
            return None
        try:
            target = resolver(position)
        except (TypeError, ValueError):
            return None
        if not isinstance(target, dict) or not target.get("connection_id"):
            return None
        if str(getattr(item, "connection_kind", "")).upper() != "SIMPLE_WIRE":
            return None
        return dict(target, connection_item=item)

    def _connection_item_at(self, position: Tuple[float, float]) -> Any | None:
        for name in ("connection_item_at", "sld_connection_item_at", "canvas_item_at"):
            resolver = getattr(self.controller, name, None)
            if callable(resolver):
                try:
                    item = resolver(position)
                except (TypeError, ValueError):
                    item = None
                if item is not None and callable(getattr(item, "insertion_target", None)):
                    return item
        scene = self._scene()
        items_method = getattr(scene, "items", None) if scene is not None else None
        if not callable(items_method):
            return None
        try:
            items = tuple(items_method(QPointF(float(position[0]), float(position[1]))))
        except (TypeError, ValueError):
            try:
                items = tuple(items_method())
            except TypeError:
                return None
        for item in items:
            if callable(getattr(item, "insertion_target", None)) and str(getattr(item, "connection_kind", "")).upper() == "SIMPLE_WIRE":
                return item
        return None

    @staticmethod
    def _insertion_event(position: Tuple[float, float], target: dict[str, Any]) -> dict[str, Any]:
        return {"scene_position": position, "connection_item": target.get("connection_item")}

    def _finish_transient_insertion(self) -> None:
        tool = self._insertion_tool
        self._insertion_active = False
        self._insertion_target = None
        self._original_drag_position = None
        if tool is not None and tool.is_active:
            tool.deactivate()
        self._insertion_tool = None

    def _cancel_transient_insertion(self) -> None:
        tool = self._insertion_tool
        if tool is not None:
            try:
                if tool.is_active:
                    tool.on_cancel()
            finally:
                if tool.is_active:
                    tool.deactivate()
        self._insertion_active = False
        self._insertion_target = None
        self._original_drag_position = None

    def _scene(self) -> Any:
        return getattr(self.get_selection_manager(), "scene", None)

    def _is_selected(self, object_id: Any) -> bool:
        return bool(self.get_selection_manager().is_selected(object_id))

    def _handle_object_click(self, object_id: Any, modifiers: int) -> None:
        manager = self.get_selection_manager()
        if self._has_toggle_modifier(modifiers):
            manager.toggle_selection(object_id)
        elif self._has_additive_modifier(modifiers):
            manager.add_to_selection(object_id)
        else:
            manager.select_single(object_id)

    @classmethod
    def _has_additive_modifier(cls, modifiers: int) -> bool:
        return bool(modifiers & (cls.SHIFT_MODIFIER | cls.META_MODIFIER))

    @classmethod
    def _has_toggle_modifier(cls, modifiers: int) -> bool:
        return bool(modifiers & (cls.CTRL_MODIFIER | cls.META_MODIFIER))

    @staticmethod
    def _event_object_id(event: Any) -> Any:
        value = getattr(event, "object_id", None)
        return event.get("object_id", value) if isinstance(event, dict) else value

    @staticmethod
    def _event_scene_position(event: Any) -> Any:
        value = getattr(event, "scene_position", None)
        if isinstance(event, dict):
            value = event.get("scene_position", value)
        return value if value is not None else getattr(event, "position", None)

    @staticmethod
    def _event_modifiers(event: Any) -> int:
        value = getattr(event, "modifiers", 0)
        if callable(value):
            value = value()
        if isinstance(event, dict):
            value = event.get("modifiers", value)
        return int(value or 0)

    @staticmethod
    def _event_key(event: Any) -> Any:
        value = getattr(event, "key", None)
        if callable(value):
            value = value()
        return event.get("key", value) if isinstance(event, dict) else value

    @staticmethod
    def _xy(value: Any) -> Tuple[float, float]:
        if value is None:
            raise ValueError("Canvas event position is required.")
        x = value.x() if callable(getattr(value, "x", None)) else value[0]
        y = value.y() if callable(getattr(value, "y", None)) else value[1]
        return float(x), float(y)

    @staticmethod
    def _distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        dx, dy = b[0] - a[0], b[1] - a[1]
        return (dx * dx + dy * dy) ** 0.5

    def _clear_pointer_state(self) -> None:
        self._pressed_object_id = None
        self._pressed_scene_position = None
        self._dragging = False

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state.update({
            "pressed_object_id": self._pressed_object_id,
            "pressed_scene_position": self._pressed_scene_position,
            "dragging": self._dragging,
            "insertion_active": self._insertion_active,
            "insertion_target": dict(self._insertion_target or {}),
            "original_drag_position": self._original_drag_position,
        })
        return state


__all__ = ["SelectTool"]
