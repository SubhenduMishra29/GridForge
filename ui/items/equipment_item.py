# ============================================================
# File: ui/items/equipment_item.py
# GridForge V2 — Generic Equipment Graphics Projection
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QBrush, QGraphicsScene, QPainter, QPen, QRectF

from .base_item import BaseItem


class EquipmentItem(BaseItem):
    """Presentation-only fallback graphic for a supported SLD equipment type."""

    HALF_SIZE = 14.0

    def __init__(self, object_id: Any, element_type: str, *, position: object = None, parent: Optional[BaseItem] = None) -> None:
        if not isinstance(element_type, str) or not element_type.strip():
            raise ValueError("element_type must be a non-empty string.")
        super().__init__(object_id, parent)
        self._element_type = element_type
        if position is not None:
            self.setPos(position)

    @property
    def element_type(self) -> str:
        return self._element_type

    def boundingRect(self) -> QRectF:
        size = self.HALF_SIZE
        return QRectF(-size, -size, 2 * size, 2 * size)

    def paint(self, painter: QPainter, option: Any, widget: Any = None) -> None:
        del option, widget
        painter.setPen(QPen())
        painter.setBrush(QBrush())
        painter.drawRect(self.boundingRect())

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state["element_type"] = self._element_type
        return state


__all__ = ["EquipmentItem"]
