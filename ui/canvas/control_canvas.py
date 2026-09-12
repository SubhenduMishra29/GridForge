"""Control/Ladder canvas projection.

Author: Subhendu Mishra

The canvas consumes immutable Application read models. It contains no Core
logic evaluation and no direct Core mutation path.
"""

from __future__ import annotations

from typing import Any

from .grid_scene import GridScene
from ..items.control_items import (
    ANDGateItem, CoilItem, ControlLogicItem, InterlockItem, LatchItem,
    NCContactItem, NOContactItem, NOTGateItem, ORGateItem, ResetCoilItem,
    SetCoilItem, TimerItem, XORGateItem,
)


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
            item.set_graphical_position(float(position * 120.0), float(rung_order * 80.0))
            self.addItem(item)


__all__ = ["ControlCanvas"]
