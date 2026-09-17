# ============================================================
# File: ui/canvas/mouse_event_adapter.py
# GridForge V2 — Canvas Mouse Event Adapter
# ============================================================
"""Translate native Qt mouse input into semantic Canvas interaction events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ui.core.qt import QPointF


@dataclass(frozen=True, slots=True)
class CanvasMouseEvent:
    """Semantic mouse event consumed by Canvas tools.

    ``position`` is the viewport-local pointer position and
    ``scene_position`` is its mapped scene coordinate. Qt-specific enum/flag
    values are normalized to integers at the input boundary.
    """

    position: QPointF
    scene_position: QPointF
    object_id: Any = None
    button: Optional[int] = None
    buttons: int = 0
    modifiers: int = 0
    event_type: Optional[int] = None
    timestamp: Optional[int] = None


class MouseEventAdapter:
    """Convert a native QMouseEvent into a semantic CanvasMouseEvent."""

    def __init__(self, *, view: Any, scene: Any) -> None:
        if view is None:
            raise ValueError("view must not be None.")
        if scene is None:
            raise ValueError("scene must not be None.")
        self._view = view
        self._scene = scene

    @property
    def view(self) -> Any:
        return self._view

    @property
    def scene(self) -> Any:
        return self._scene

    def adapt(self, event: Any) -> CanvasMouseEvent:
        if event is None:
            raise ValueError("event must not be None.")
        viewport_position = self._event_position(event)
        scene_position = self._map_to_scene(viewport_position)
        viewport_point = self._point(viewport_position)
        scene_point = self._point(scene_position)
        return CanvasMouseEvent(
            position=viewport_point,
            scene_position=scene_point,
            object_id=self._hit_test(scene_point),
            button=self._event_flag(event, "button", allow_none=True),
            buttons=self._event_flag(event, "buttons", default=0),
            modifiers=self._event_flag(event, "modifiers", default=0),
            event_type=self._event_flag(event, "type", allow_none=True),
            timestamp=self._event_integer(event, "timestamp", allow_none=True),
        )

    @staticmethod
    def _point(value: Any) -> QPointF:
        if isinstance(value, QPointF):
            return QPointF(value)
        try:
            return QPointF(value)
        except (TypeError, ValueError):
            x = getattr(value, "x", None)
            y = getattr(value, "y", None)
            if callable(x) and callable(y):
                return QPointF(float(x()), float(y()))
            if isinstance(value, (tuple, list)) and len(value) >= 2:
                return QPointF(float(value[0]), float(value[1]))
            raise TypeError("mouse position must be QPointF-compatible.")

    def _map_to_scene(self, position: Any) -> Any:
        mapper = getattr(self._view, "mapToScene", None)
        if not callable(mapper):
            raise TypeError("view must provide mapToScene().")
        try:
            return mapper(position)
        except (TypeError, AttributeError):
            to_point = getattr(position, "toPoint", None)
            if not callable(to_point):
                raise
            return mapper(to_point())

    def _hit_test(self, scene_position: Any) -> Optional[Any]:
        items_method = getattr(self._scene, "items", None)
        if not callable(items_method):
            raise TypeError("scene must provide items().")
        for item in tuple(items_method(scene_position)):
            candidate = self._selectable_ancestor(item)
            if candidate is not None:
                return getattr(candidate, "object_id", None)
        return None

    @staticmethod
    def _is_selectable(item: Any) -> bool:
        if item is None:
            return False
        if getattr(item, "isVisible", lambda: True)() is False:
            return False
        if getattr(item, "isEnabled", lambda: True)() is False:
            return False
        if getattr(item, "object_id", None) is None:
            return False
        flags = getattr(item, "flags", None)
        if not callable(flags):
            return True
        try:
            value = flags()
            flag_type = getattr(item, "GraphicsItemFlag", None)
            selectable_flag = getattr(flag_type, "ItemIsSelectable", None)
            if selectable_flag is None:
                return True
            return bool(value & selectable_flag)
        except (TypeError, AttributeError):
            return True

    @classmethod
    def _selectable_ancestor(cls, item: Any) -> Optional[Any]:
        current = item
        while current is not None:
            if cls._is_selectable(current):
                return current
            parent_method = getattr(current, "parentItem", None)
            current = parent_method() if callable(parent_method) else None
        return None

    @staticmethod
    def _event_position(event: Any) -> Any:
        position = getattr(event, "position", None)
        if callable(position):
            return position()
        if position is not None:
            return position
        if isinstance(event, dict) and "position" in event:
            return event["position"]
        raise AttributeError("event does not expose position().")

    @staticmethod
    def _event_value(event: Any, name: str) -> Any:
        value = getattr(event, name, None)
        if callable(value):
            value = value()
        if isinstance(event, dict):
            value = event.get(name, value)
        return value

    @classmethod
    def _event_flag(
        cls,
        event: Any,
        name: str,
        *,
        default: Optional[int] = None,
        allow_none: bool = False,
    ) -> Optional[int]:
        value = cls._event_value(event, name)
        if value is None:
            if allow_none:
                return None
            if default is not None:
                return default
            raise TypeError(f"event {name} must provide an integer flag.")
        if isinstance(value, bool):
            raise TypeError(f"event {name} must be an integer flag, not bool.")
        if isinstance(value, int):
            return value
        raw_value = getattr(value, "value", None)
        if isinstance(raw_value, bool):
            raise TypeError(f"event {name} must be an integer flag, not bool.")
        if isinstance(raw_value, int):
            return raw_value
        raise TypeError(
            f"event {name} must be an integer or expose an integer .value."
        )

    @classmethod
    def _event_integer(
        cls,
        event: Any,
        name: str,
        *,
        default: Optional[int] = None,
        allow_none: bool = False,
    ) -> Optional[int]:
        value = cls._event_value(event, name)
        if value is None:
            if allow_none:
                return None
            return default
        if isinstance(value, bool):
            raise TypeError(f"event {name} must be an integer, not bool.")
        if isinstance(value, int):
            return value
        raw_value = getattr(value, "value", None)
        if isinstance(raw_value, bool):
            raise TypeError(f"event {name} must be an integer, not bool.")
        if isinstance(raw_value, int):
            return raw_value
        raise TypeError(f"event {name} must be an integer.")

    def dispose(self) -> None:
        self._view = None
        self._scene = None


__all__ = ["CanvasMouseEvent", "MouseEventAdapter"]
