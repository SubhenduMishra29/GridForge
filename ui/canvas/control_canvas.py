"""Control/Ladder canvas projection.

Author: Subhendu Mishra

The canvas consumes immutable Application read models. It contains no Core
logic evaluation and no direct Core mutation path.
"""

from __future__ import annotations

from typing import Any

from .grid_scene import GridScene
from ui.core.qt import QGraphicsLineItem, QGraphicsObject, QPainter, QFont, QRectF
from ..items.control_items import (
    ANDGateItem, CoilItem, ControlLogicItem, InterlockItem, LatchItem,
    NCContactItem, NOContactItem, NOTGateItem, ORGateItem, ResetCoilItem,
    SetCoilItem, TimerItem, XORGateItem,
)


class _RungLabelItem(QGraphicsObject):
    def __init__(self, text: str) -> None:
        super().__init__()
        self._text = str(text)

    def boundingRect(self) -> QRectF:
        return QRectF(0.0, 0.0, 70.0, 24.0)

    def paint(self, painter: QPainter, option: Any, widget: Any = None) -> None:
        del option, widget
        painter.setFont(QFont("Sans", 9))
        painter.drawText(self.boundingRect(), 0x84, self._text)


_ITEM_TYPES = {
    "normally_open_contact": NOContactItem,
    "normally_closed_contact": NCContactItem,
    "and_gate": ANDGateItem,
    "or_gate": ORGateItem,
    "not_gate": NOTGateItem,
    "xor_gate": XORGateItem,
    "coil": CoilItem,
    "set_coil": SetCoilItem,
    "reset_coil": ResetCoilItem,
    "timer": TimerItem,
    "ton_timer": TimerItem,
    "tof_timer": TimerItem,
    "tp_timer": TimerItem,
    "latch": LatchItem,
    "sr_latch": LatchItem,
    "rs_latch": LatchItem,
    "interlock": InterlockItem,
}


class ControlCanvas(GridScene):
    """Passive graphical projection of an Application Control read model."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._control_read_model = None

    @property
    def control_read_model(self):
        return self._control_read_model

    def project(self, read_model: Any) -> None:
        """Replace the graphical projection from an immutable read model."""
        if read_model is None:
            raise ValueError("read_model must not be None.")
        self.clear()
        self._control_read_model = read_model

        # Rails and rung identifiers are presentation-only geometry.
        for rung in read_model.rungs:
            y = float(rung.order * 80.0 + 24.0)
            self.addItem(QGraphicsLineItem(0.0, y, 900.0, y))
            label = _RungLabelItem(f"Rung {rung.order + 1:03d}")
            label.setPos(-80.0, y - 14.0)
            self.addItem(label)

        positions: dict[str, tuple[float, float]] = {}
        enabled_by_component = {
            component_id: rung.enabled
            for rung in read_model.rungs
            for component_id in rung.component_ids
        }
        for component in read_model.components:
            item_class = _ITEM_TYPES.get(component.component_type, ControlLogicItem)
            if item_class is ControlLogicItem:
                item = item_class(component.component_id, component.component_type,
                                  state=bool(component.state.get("energized", component.state.get("q", False))))
            else:
                state_value = component.state.get("energized", component.state.get("q", False))
                item = item_class(component.component_id, state=bool(state_value))
            rung_order = next((r.order for r in read_model.rungs if component.component_id in r.component_ids), 0)
            position = next((e for r in read_model.rungs if component.component_id in r.component_ids
                             for e in [r.component_ids.index(component.component_id)]), 0)
            x = float(position * 120.0 + 8.0)
            y = float(rung_order * 80.0)
            item.set_scene_position(x, y)
            item.setOpacity(1.0 if enabled_by_component.get(component.component_id, True) else 0.45)
            self.addItem(item)
            positions[component.component_id] = (x + 45.0, y + 23.0)

        # Connections are derived from the read model, never from pixel proximity.
        for connection in read_model.connections:
            source = positions.get(connection.source_component)
            target = positions.get(connection.target_component)
            if source is None or target is None:
                continue
            self.addItem(QGraphicsLineItem(source[0], source[1], target[0], target[1]))


__all__ = ["ControlCanvas"]
