"""Projection-only QGraphics items for Logic Control / Ladder.

Author: Subhendu Mishra

These items render Application read-model identity/state only. They do not
instantiate Core logic objects, evaluate logic, or mutate Application/Core.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QFont, QPainter, QPen, QRectF
from .base_item import BaseItem


class ControlLogicItem(BaseItem):
    """Generic presentation item for one Control read-model component."""

    WIDTH = 90.0
    HEIGHT = 46.0

    def __init__(self, object_id: str, component_type: str, *, state: bool = False, parent=None) -> None:
        super().__init__(object_id, parent)
        self._component_type = str(component_type)
        self._state = bool(state)

    @property
    def component_type(self) -> str:
        return self._component_type

    @property
    def state(self) -> bool:
        return self._state

    def update_read_model(self, *, component_type: str | None = None, state: bool | None = None) -> None:
        if component_type is not None:
            self._component_type = str(component_type)
        if state is not None:
            self._state = bool(state)
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(0.0, 0.0, self.WIDTH, self.HEIGHT)

    def paint(self, painter: QPainter, option: Any, widget: Optional[Any] = None) -> None:
        del option, widget
        painter.setPen(QPen())
        painter.drawRect(self.boundingRect())
        painter.setFont(QFont("Sans", 9))
        painter.drawText(self.boundingRect(), 0x84, self._component_type)
        painter.drawText(QRectF(4.0, 4.0, self.WIDTH - 8.0, 16.0), 0x82, str(self.object_id))


class NOContactItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "normally_open_contact", **kwargs)


class NCContactItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "normally_closed_contact", **kwargs)


class ANDGateItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "and_gate", **kwargs)


class ORGateItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "or_gate", **kwargs)


class NOTGateItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "not_gate", **kwargs)


class XORGateItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "xor_gate", **kwargs)


class CoilItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "coil", **kwargs)


class SetCoilItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "set_coil", **kwargs)


class ResetCoilItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "reset_coil", **kwargs)


class TimerItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "timer", **kwargs)


class LatchItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "latch", **kwargs)


class InterlockItem(ControlLogicItem):
    def __init__(self, object_id: str, **kwargs):
        super().__init__(object_id, "interlock", **kwargs)


__all__ = [
    "ControlLogicItem", "NOContactItem", "NCContactItem", "ANDGateItem", "ORGateItem",
    "NOTGateItem", "XORGateItem", "CoilItem", "SetCoilItem", "ResetCoilItem",
    "TimerItem", "LatchItem", "InterlockItem",
]
