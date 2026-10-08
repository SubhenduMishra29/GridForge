# ============================================================
# File: ui/canvas/mouse_event_adapter.py
# GridForge V2 — Canvas Mouse Event Adapter
# ============================================================
"""Translate native Qt mouse input into semantic Canvas interaction events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ui.core.qt import QGraphicsItem, QPointF
from ui.canvas.canvas_hit import CanvasHitTarget


@dataclass(frozen=True, slots=True)
class CanvasMouseEvent:
    """Semantic mouse event consumed by Canvas tools.

    ``position`` is the viewport-local pointer position and
    ``scene_position`` is its mapped scene coordinate. Qt-specific enum/flag
    values are normalized to integers at the input boundary.
    ``presentation_hit`` contains immutable presentation-only hit metadata.
    ``object_id`` remains the legacy semantic selection key.
    """

    position: QPointF
    scene_position: QPointF
    object_id: Any = None
    presentation_hit: CanvasHitTarget = field(default_factory=CanvasHitTarget.none)
    button: Optional[int] = None
    buttons: int = 0
    modifiers: int = 0
    event_type: Optional[int] = None
    timestamp: Optional[int] = None

    @property
    def hit_target(self) -> CanvasHitTarget:
        """Compatibility/readability alias for presentation hit metadata."""
        return self.presentation_hit


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
        hit = self._hit_test(scene_point)
        return CanvasMouseEvent(
            position=viewport_point,
            scene_position=scene_point,
            object_id=hit.object_id,
            presentation_hit=hit,
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
        to_point = getattr(position, "toPoint", None)
        if callable(to_point):
            return mapper(to_point())
        return mapper(position)

    def _hit_test(self, scene_position: Any) -> CanvasHitTarget:
        item_at = getattr(self._scene, "itemAt", None)
        if not callable(item_at):
            raise TypeError("scene must provide itemAt().")

        x = float(scene_position.x())
        y = float(scene_position.y())
        transform = self._view.viewportTransform()
        try:
            item = item_at(x, y, transform)
        except (TypeError, ValueError, AttributeError):
            return CanvasHitTarget.none()

        while item is not None:
            if self._is_selectable(item):
                return self._presentation_hit_for_item(item, (x, y))
            parent = getattr(item, "parentItem", None)
            item = parent() if callable(parent) else None
        return CanvasHitTarget.none()

    @classmethod
    def _presentation_hit_for_item(cls, item: Any, position: tuple[float, float]) -> CanvasHitTarget:
        object_id = getattr(item, "object_id", None)
        connection_kind = str(getattr(item, "connection_kind", "") or "").upper()
        resolver = getattr(item, "insertion_target", None)
        if connection_kind == "SIMPLE_WIRE" and callable(resolver):
            try:
                raw_hit = resolver(position)
            except (TypeError, ValueError):
                return CanvasHitTarget.none()
            if not isinstance(raw_hit, dict):
                return CanvasHitTarget.none()
            return CanvasHitTarget.from_connection_item(item, raw_hit)
        if connection_kind:
            return CanvasHitTarget.connection(
                object_id=object_id,
                presentation_id=getattr(item, "presentation_id", None),
                core_connection_id=getattr(item, "core_connection_id", None),
            )
        return CanvasHitTarget.node(object_id)

    @staticmethod
    def _is_selectable(item: Any) -> bool:
        if item is None or getattr(item, "object_id", None) is None:
            return False

        is_visible = getattr(item, "isVisible", None)
        is_enabled = getattr(item, "isEnabled", None)
        flags = getattr(item, "flags", None)
        if not callable(is_visible) or not callable(is_enabled) or not callable(flags):
            return False

        try:
            return bool(
                is_visible()
                and is_enabled()
                and flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            )
        except (TypeError, AttributeError):
            return False

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
    def _event_flag(cls, event: Any, name: str, *, default: Optional[int] = None, allow_none: bool = False) -> Optional[int]:
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
        raise TypeError(f"event {name} must be an integer or expose an integer .value.")

    @classmethod
    def _event_integer(cls, event: Any, name: str, *, default: Optional[int] = None, allow_none: bool = False) -> Optional[int]:
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
