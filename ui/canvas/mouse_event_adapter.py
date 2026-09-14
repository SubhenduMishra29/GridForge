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
    """Framework-neutral mouse event consumed by Canvas tools."""

    position: QPointF
    scene_position: QPointF
    object_id: Any = None
    button: Any = None
    buttons: Any = None
    modifiers: int = 0


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
        return CanvasMouseEvent(
            position=QPointF(scene_position),
            scene_position=QPointF(scene_position),
            object_id=self._hit_test(scene_position),
            button=self._event_value(event, "button"),
            buttons=self._event_value(event, "buttons"),
            modifiers=self._event_modifiers(event),
        )

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

        # QGraphicsScene.items(point) returns items in stacking order. Walk
        # each candidate toward its selectable BaseItem so decorative child
        # graphics do not become independent selection targets.
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
    def _event_modifiers(cls, event: Any) -> int:
        value = cls._event_value(event, "modifiers")
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise TypeError("event modifiers must be integer-compatible.") from exc

    def dispose(self) -> None:
        self._view = None
        self._scene = None


__all__ = ["CanvasMouseEvent", "MouseEventAdapter"]
