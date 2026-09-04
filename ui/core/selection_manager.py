# ============================================================
# File: ui/core/selection_manager.py
# GridForge V2 — Selection Manager
# ============================================================
"""Central UI-Core selection authority and graphics projection."""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import QGraphicsScene


class SelectionManager:
    """Own transient UI selection state and project it to graphics.

    Selection is UI-Core interaction state. This manager is the sole
    authority for that state; the electrical Core is not involved.
    """

    def __init__(self, scene: Optional[QGraphicsScene] = None) -> None:
        self._selected_ids: list[Any] = []
        self.scene = scene

    def get_selected_ids(self) -> tuple[Any, ...]:
        return tuple(self._selected_ids)

    @property
    def selected_ids(self) -> tuple[Any, ...]:
        return self.get_selected_ids()

    def has_selection(self) -> bool:
        return bool(self._selected_ids)

    def is_selected(self, object_id: Any) -> bool:
        if object_id is None:
            return False
        return any(selected_id == object_id for selected_id in self._selected_ids)

    def select(self, object_id: Any, multi: bool = False) -> None:
        if object_id is None:
            raise ValueError("object_id must not be None.")
        if not isinstance(multi, bool):
            raise TypeError("multi must be a bool.")

        if multi:
            if not self.is_selected(object_id):
                self._selected_ids.append(object_id)
            return

        if self._selected_ids == [object_id]:
            return
        self._selected_ids = [object_id]

    def select_single(self, object_id: Any) -> None:
        self.select(object_id, multi=False)

    def add_to_selection(self, object_id: Any) -> None:
        self.select(object_id, multi=True)

    def toggle_selection(self, object_id: Any) -> None:
        if object_id is None:
            raise ValueError("object_id must not be None.")
        if self.is_selected(object_id):
            self._selected_ids = [
                selected_id
                for selected_id in self._selected_ids
                if selected_id != object_id
            ]
            return
        self._selected_ids.append(object_id)

    def clear(self) -> None:
        self._selected_ids.clear()

    def sync_graphics(self, scene: Optional[QGraphicsScene] = None) -> None:
        target_scene = scene if scene is not None else self.scene
        if target_scene is None:
            return

        items_method = getattr(target_scene, "items", None)
        if not callable(items_method):
            raise TypeError("scene must provide items().")

        selected_ids = self.get_selected_ids()
        for item in tuple(items_method()):
            set_selected = getattr(item, "setSelected", None)
            if not callable(set_selected):
                continue

            object_id = getattr(item, "object_id", None)
            if object_id is None:
                set_selected(False)
                continue

            set_selected(any(selected_id == object_id for selected_id in selected_ids))

    def reconcile(self, scene: Optional[QGraphicsScene] = None) -> None:
        self.sync_graphics(scene=scene)

    def get_item_for_id(
        self,
        object_id: Any,
        scene: Optional[QGraphicsScene] = None,
    ) -> Optional[Any]:
        if object_id is None:
            return None

        target_scene = scene if scene is not None else self.scene
        if target_scene is None:
            return None

        items_method = getattr(target_scene, "items", None)
        if not callable(items_method):
            raise TypeError("scene must provide items().")

        for item in tuple(items_method()):
            if getattr(item, "object_id", None) == object_id:
                return item
        return None

    def get_items_for_ids(
        self,
        object_ids: Iterable[Any],
        scene: Optional[QGraphicsScene] = None,
    ) -> tuple[Any, ...]:
        if object_ids is None:
            raise ValueError("object_ids must not be None.")

        requested_ids = tuple(object_ids)
        if not requested_ids:
            return ()

        target_scene = scene if scene is not None else self.scene
        if target_scene is None:
            return ()

        items_method = getattr(target_scene, "items", None)
        if not callable(items_method):
            raise TypeError("scene must provide items().")

        result: list[Any] = []
        for item in tuple(items_method()):
            object_id = getattr(item, "object_id", None)
            if any(requested_id == object_id for requested_id in requested_ids):
                result.append(item)
        return tuple(result)

    def get_selected_items(self, scene: Optional[QGraphicsScene] = None) -> tuple[Any, ...]:
        return self.get_items_for_ids(self.get_selected_ids(), scene=scene)

    def set_scene(self, scene: Optional[QGraphicsScene]) -> None:
        self.scene = scene

    def get_scene(self) -> Optional[QGraphicsScene]:
        return self.scene

    def reset_graphics(self, scene: Optional[QGraphicsScene] = None) -> None:
        target_scene = scene if scene is not None else self.scene
        if target_scene is None:
            return

        items_method = getattr(target_scene, "items", None)
        if not callable(items_method):
            raise TypeError("scene must provide items().")

        for item in tuple(items_method()):
            set_selected = getattr(item, "setSelected", None)
            if callable(set_selected):
                set_selected(False)

    def get_state(self) -> dict[str, Any]:
        selected_ids = self.get_selected_ids()
        return {
            "selected_count": len(selected_ids),
            "selected_ids": selected_ids,
            "has_selection": bool(selected_ids),
            "has_scene": self.scene is not None,
        }

    def __repr__(self) -> str:
        return f"SelectionManager(selected={len(self._selected_ids)}, scene={self.scene is not None})"


__all__ = ["SelectionManager"]
