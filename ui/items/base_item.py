# ============================================================
# File: ui/items/base_item.py
# GridForge V2 — Base Graphics Item
# Author: Subhendu Mishra
# ============================================================

"""GridForge V2 Base Graphics Item.

BaseItem is a presentation-only QGraphicsObject foundation. It deliberately
avoids ABCMeta because Qt's QGraphicsObject uses the Shiboken metaclass.
Concrete items provide boundingRect() and paint() implementations.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QGraphicsObject, QRectF


class BaseItem(QGraphicsObject):
    """Common presentation-layer base class for GridForge graphics items."""

    def __init__(self, object_id: Any, parent: Optional[QGraphicsObject] = None) -> None:
        if object_id is None:
            raise ValueError("object_id must not be None.")
        super().__init__(parent)
        self._object_id = object_id
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsFocusable, False)

    @property
    def object_id(self) -> Any:
        return self._object_id

    def get_object_id(self) -> Any:
        return self._object_id

    def is_selected(self) -> bool:
        return bool(self.isSelected())

    def set_graphical_selected(self, selected: bool) -> None:
        if not isinstance(selected, bool):
            raise TypeError("selected must be a bool.")
        self.setSelected(selected)

    def clear_graphical_selection(self) -> None:
        self.setSelected(False)

    def get_scene_position(self) -> tuple[float, float]:
        position = self.scenePos()
        return float(position.x()), float(position.y())

    def set_scene_position(self, x: float, y: float) -> None:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError("x must be a numeric value.")
        if isinstance(y, bool) or not isinstance(y, (int, float)):
            raise TypeError("y must be a numeric value.")
        self.setPos(float(x), float(y))

    def boundingRect(self) -> QRectF:
        """Return a neutral geometry; concrete items override this."""
        return QRectF()

    def scene_bounding_rect(self) -> QRectF:
        return self.mapRectToScene(self.boundingRect())

    def paint(self, painter: Any, option: Any, widget: Optional[Any] = None) -> None:
        """Concrete items override painting; the base item paints nothing."""
        return None

    def is_visible(self) -> bool:
        return bool(self.isVisible())

    def set_graphical_visible(self, visible: bool) -> None:
        if not isinstance(visible, bool):
            raise TypeError("visible must be a bool.")
        self.setVisible(visible)

    def is_enabled(self) -> bool:
        return bool(self.isEnabled())

    def set_graphical_enabled(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be a bool.")
        self.setEnabled(enabled)

    def get_state(self) -> dict[str, Any]:
        position = self.scenePos()
        return {
            "object_id": self._object_id,
            "selected": bool(self.isSelected()),
            "visible": bool(self.isVisible()),
            "enabled": bool(self.isEnabled()),
            "x": float(position.x()),
            "y": float(position.y()),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(object_id={self._object_id!r}, selected={self.isSelected()})"


__all__ = ["BaseItem"]
