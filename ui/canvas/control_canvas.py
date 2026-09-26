"""Control/Ladder canvas projection and presentation interaction helpers.

Author: Subhendu Mishra

The canvas consumes immutable Application read models. It contains no Core
logic evaluation and no direct Core mutation path.
"""

from __future__ import annotations

import math
from typing import Any

from .grid_scene import GridScene
from ui.core.qt import QGraphicsLineItem, QGraphicsObject, QPainter, QFont, QRectF, QPointF, QPen
from ui.control.ladder.ladder_geometry import LadderGeometryPolicy
from ui.control.ladder.control_port import ControlPortDirection, ControlPortPresentation
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


class _ControlConnectionItem(QGraphicsLineItem):
    """Selectable projection of one authoritative Control connection."""

    def __init__(self, connection_identity: tuple[str, str, str, str], *args: Any) -> None:
        super().__init__(*args)
        self._connection_identity = connection_identity
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)

    @property
    def connection_identity(self) -> tuple[str, str, str, str]:
        return self._connection_identity


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
        self._preview_item: ControlLogicItem | None = None
        self._connection_preview: QGraphicsLineItem | None = None

    @property
    def control_read_model(self):
        return self._control_read_model

    def project(self, read_model: Any) -> None:
        """Replace the graphical projection from an immutable read model."""
        if read_model is None:
            raise ValueError("read_model must not be None.")
        self.clear()
        self._control_read_model = read_model
        self._preview_item = None
        self._connection_preview = None

        for rung in read_model.rungs:
            y = LadderGeometryPolicy.rung_line_y(rung.order)
            self.addItem(QGraphicsLineItem(0.0, y, 900.0, y))
            label = _RungLabelItem(f"Rung {rung.order + 1:03d}")
            label.setPos(-80.0, y - 14.0)
            self.addItem(label)

        component_items: dict[str, ControlLogicItem] = {}
        port_positions: dict[tuple[str, str, str], tuple[float, float]] = {}

        # Connections are projected first so component symbols remain the
        # primary graphical hit targets during normal selection.
        for connection in read_model.connections:
            identity = (
                str(connection.source_component),
                str(connection.source_output),
                str(connection.target_component),
                str(connection.target_input),
            )
            item = _ControlConnectionItem(identity)
            item.setZValue(-10.0)
            item.setPen(QPen())
            self.addItem(item)

        for component in read_model.components:
            item_class = _ITEM_TYPES.get(component.component_type, ControlLogicItem)
            if item_class is ControlLogicItem:
                item = item_class(
                    component.component_id,
                    component.component_type,
                    state=bool(component.state.get("energized", component.state.get("q", False))),
                )
            else:
                item = item_class(
                    component.component_id,
                    state=bool(component.state.get("energized", component.state.get("q", False))),
                )

            rung = next((r for r in read_model.rungs if r.rung_id == component.rung_id), None)
            if rung is None and component.rung_id is not None:
                rung = next((r for r in read_model.rungs if component.component_id in r.component_ids), None)
            if rung is None:
                continue

            position = component.position
            if position is None:
                position = rung.positions.get(component.component_id)
            if position is None:
                continue

            item.set_scene_position(
                LadderGeometryPolicy.component_x(position),
                LadderGeometryPolicy.rung_y(rung.order),
            )
            item.set_ports(
                inputs=tuple(component.input_signal_types.get(name, "unknown") for name in component.inputs),
                outputs=tuple(component.output_signal_types.get(name, "unknown") for name in component.outputs),
            )
            # set_ports expects names as well; normalize the tuple here.
            item.set_ports(
                inputs=tuple((name, component.input_signal_types.get(name, "unknown")) for name in component.inputs),
                outputs=tuple((name, component.output_signal_types.get(name, "unknown")) for name in component.outputs),
            )
            item.setOpacity(1.0 if rung.enabled else 0.45)
            self.addItem(item)
            component_items[component.component_id] = item

            for port in item.port_presentations():
                port_positions[(port.component_id, port.direction.value, port.port_name)] = port.scene_position

        for connection in read_model.connections:
            source = port_positions.get(
                (str(connection.source_component), ControlPortDirection.OUTPUT.value, str(connection.source_output))
            )
            target = port_positions.get(
                (str(connection.target_component), ControlPortDirection.INPUT.value, str(connection.target_input))
            )
            if source is None or target is None:
                continue
            identity = (
                str(connection.source_component),
                str(connection.source_output),
                str(connection.target_component),
                str(connection.target_input),
            )
            item = next(
                (candidate for candidate in self.items() if getattr(candidate, "connection_identity", None) == identity),
                None,
            )
            if item is not None:
                item.setLine(source[0], source[1], target[0], target[1])

    def component_at(self, x: float, y: float) -> ControlLogicItem | None:
        point = QPointF(float(x), float(y))
        for item in self.items(point):
            if isinstance(item, ControlLogicItem):
                return item
        return None

    def connection_at(self, x: float, y: float) -> tuple[str, str, str, str] | None:
        point = QPointF(float(x), float(y))
        for item in self.items(point):
            identity = getattr(item, "connection_identity", None)
            if identity is not None:
                return identity
        return None

    def rung_at(self, y: float) -> Any | None:
        return LadderGeometryPolicy.snap_rung(float(y), getattr(self._control_read_model, "rungs", ()))

    def port_at(self, x: float, y: float, *, direction: ControlPortDirection | None = None) -> ControlPortPresentation | None:
        model = self._control_read_model
        if model is None:
            return None
        best: ControlPortPresentation | None = None
        best_distance = 11.0
        for component in model.components:
            item = self.find_item_by_object_id(component.component_id)
            if not isinstance(item, ControlLogicItem):
                continue
            for port in item.port_presentations():
                if direction is not None and port.direction is not direction:
                    continue
                distance = math.hypot(port.scene_position[0] - float(x), port.scene_position[1] - float(y))
                if distance <= best_distance:
                    best = port
                    best_distance = distance
        return best

    def create_semantic_preview(self, component_type: str) -> None:
        self.clear_transient_preview()
        item_class = _ITEM_TYPES.get(component_type, ControlLogicItem)
        if item_class is ControlLogicItem:
            item = item_class("__control_preview__", component_type)
        else:
            item = item_class("__control_preview__")
        item.setOpacity(0.45)
        item.setFlag(item.GraphicsItemFlag.ItemIsSelectable, False)
        self.addItem(item)
        self._preview_item = item

    def update_semantic_preview(self, *, order: int, position: int) -> None:
        if self._preview_item is None:
            return
        self._preview_item.set_scene_position(
            LadderGeometryPolicy.component_x(position),
            LadderGeometryPolicy.rung_y(order),
        )

    def show_connection_preview(self, start: tuple[float, float], end: tuple[float, float]) -> None:
        if self._connection_preview is None:
            self._connection_preview = QGraphicsLineItem()
            self._connection_preview.setOpacity(0.55)
            self.addItem(self._connection_preview)
        self._connection_preview.setLine(start[0], start[1], end[0], end[1])

    def clear_transient_preview(self) -> None:
        for item in (self._preview_item, self._connection_preview):
            if item is not None:
                self.removeItem(item)
        self._preview_item = None
        self._connection_preview = None

    def connection_identity_exists(self, identity: tuple[str, str, str, str]) -> bool:
        model = self._control_read_model
        if model is None:
            return False
        return any(
            (
                str(c.source_component),
                str(c.source_output),
                str(c.target_component),
                str(c.target_input),
            ) == identity
            for c in model.connections
        )


__all__ = ["ControlCanvas"]
