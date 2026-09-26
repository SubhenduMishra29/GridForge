"""Projection-only QGraphics items for Logic Control / Ladder.

Author: Subhendu Mishra

These items render Application read-model identity/state only. They do not
instantiate Core logic objects, evaluate logic, or mutate Application/Core.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from ui.core.qt import QFont, QPainter, QPen, QRectF
from .base_item import BaseItem


class ControlPortDirection(str, Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


@dataclass(frozen=True, slots=True)
class ControlPortPresentation:
    component_id: str
    port_name: str
    direction: ControlPortDirection
    signal_type: str
    scene_position: tuple[float, float]


class ControlLogicItem(BaseItem):
    """Generic presentation item for one Control read-model component."""

    WIDTH = 90.0
    HEIGHT = 46.0

    def __init__(self, object_id: str, component_type: str, *, state: bool = False, parent=None) -> None:
        super().__init__(object_id, parent)
        self._component_type = str(component_type)
        self._state = bool(state)
        self._inputs: tuple[tuple[str, str], ...] = ()
        self._outputs: tuple[tuple[str, str], ...] = ()

    def set_ports(self, *, inputs: tuple[tuple[str, str], ...], outputs: tuple[tuple[str, str], ...]) -> None:
        self._inputs = tuple(inputs)
        self._outputs = tuple(outputs)
        self.update()

    @staticmethod
    def _port_local_y(index: int, count: int) -> float:
        if count <= 0:
            return ControlLogicItem.HEIGHT / 2.0
        return ControlLogicItem.HEIGHT * (index + 1) / (count + 1)

    def port_presentations(self) -> tuple[ControlPortPresentation, ...]:
        scene = self.scenePos()
        result: list[ControlPortPresentation] = []
        for index, (name, signal_type) in enumerate(self._inputs):
            result.append(ControlPortPresentation(
                component_id=str(self.object_id), port_name=name,
                direction=ControlPortDirection.INPUT, signal_type=signal_type,
                scene_position=(float(scene.x()), float(scene.y() + self._port_local_y(index, len(self._inputs)))),
            ))
        for index, (name, signal_type) in enumerate(self._outputs):
            result.append(ControlPortPresentation(
                component_id=str(self.object_id), port_name=name,
                direction=ControlPortDirection.OUTPUT, signal_type=signal_type,
                scene_position=(float(scene.x() + self.WIDTH), float(scene.y() + self._port_local_y(index, len(self._outputs)))),
            ))
        return tuple(result)

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
        for index, _port in enumerate(self._inputs):
            y = self._port_local_y(index, len(self._inputs))
            painter.drawEllipse(0.0 - 3.0, y - 3.0, 6.0, 6.0)
        for index, _port in enumerate(self._outputs):
            y = self._port_local_y(index, len(self._outputs))
            painter.drawEllipse(self.WIDTH - 3.0, y - 3.0, 6.0, 6.0)


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
    "TimerItem", "LatchItem", "InterlockItem", "ControlPortDirection", "ControlPortPresentation",
]
