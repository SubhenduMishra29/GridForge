# ============================================================
# File: ui/items/equipment_item.py
# GridForge V2 — Symbol-aware Equipment Graphics Projection
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QBrush, QPainter, QPen, QRectF, QPointF
from ui.equipment.equipment_base import EquipmentBase
from ui.equipment.symbol.symbol_base import SymbolBase
from ui.equipment.symbol.symbol_definition import SymbolDefinition

from .base_item import BaseItem


class EquipmentItem(BaseItem):
    """Presentation-only graphics projection for one resolved symbol."""

    HALF_SIZE = 24.0

    def __init__(self, object_id: Any, element_type: str, *, position: object = None,
                 symbol_definition: SymbolDefinition, equipment: EquipmentBase,
                 symbol_instance: SymbolBase | None = None,
                 parent: Optional[BaseItem] = None) -> None:
        if not isinstance(element_type, str) or not element_type.strip():
            raise ValueError("element_type must be a non-empty string")
        if not isinstance(symbol_definition, SymbolDefinition):
            raise TypeError("symbol_definition must be a SymbolDefinition")
        if not isinstance(equipment, EquipmentBase):
            raise TypeError("equipment must be an EquipmentBase")
        super().__init__(object_id, parent)
        self._element_type = element_type
        self._symbol_definition = symbol_definition
        self._equipment = equipment
        if symbol_instance is None:
            symbol_instance = SymbolBase(
                symbol_id=symbol_definition.symbol_id,
                definition_id=symbol_definition.symbol_id,
            )
        if symbol_instance.symbol_id != symbol_definition.symbol_id:
            raise ValueError(
                "symbol_instance must resolve to the supplied SymbolDefinition."
            )
        if symbol_instance.representation_id != "symbol":
            raise ValueError(
                f"Unsupported SLD symbol representation: {symbol_instance.representation_id!r}"
            )
        self._symbol_instance = SymbolBase.from_dict(symbol_instance.to_dict())
        self.setScale(self._symbol_instance.scale)
        self.setRotation(self._symbol_instance.rotation)
        self.setVisible(self._symbol_instance.visible)
        if position is not None:
            self.setPos(position)

    @property
    def element_type(self) -> str:
        return self._element_type

    @property
    def symbol_definition(self) -> SymbolDefinition:
        return self._symbol_definition


    @property
    def equipment(self) -> EquipmentBase:
        return self._equipment

    @property
    def symbol_instance(self) -> SymbolBase:
        """Return the renderer-neutral presentation state realized by this item."""
        return self._symbol_instance

    @property
    def terminals(self):
        return self._equipment.terminals

    def snap_points(self):
        """Expose terminal-aware scene-space snap candidates."""
        points = []
        for terminal in self._equipment.terminals:
            # SymbolDefinition is the sole graphical anchor authority. The
            # terminal registry identity is retained only as presentation identity.
            local_anchor = self._symbol_definition.get_terminal_anchor(terminal.terminal_name)
            scene_point = self.mapToScene(QPointF(local_anchor[0], local_anchor[1]))
            points.append({
                "position": scene_point,
                "object_id": self.object_id,
                "terminal_id": terminal.terminal_id,
                "terminal_name": terminal.terminal_name,
            })
        return tuple(points)

    def boundingRect(self) -> QRectF:
        return QRectF(-self._symbol_definition.width / 2, -self._symbol_definition.height / 2,
                      self._symbol_definition.width, self._symbol_definition.height)

    def paint(self, painter: QPainter, option: Any, widget: Any = None) -> None:
        del option, widget
        painter.setPen(QPen())
        painter.setBrush(QBrush())
        for primitive in self._symbol_definition.primitives:
            kind = primitive.get("kind")
            if kind == "line":
                painter.drawLine(primitive["x1"], primitive["y1"], primitive["x2"], primitive["y2"])
            elif kind == "rect":
                painter.drawRect(primitive["x"], primitive["y"], primitive["width"], primitive["height"])
            elif kind == "circle":
                painter.drawEllipse(primitive["cx"] - primitive["r"], primitive["cy"] - primitive["r"],
                                    primitive["r"] * 2, primitive["r"] * 2)

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state["element_type"] = self._element_type
        state["symbol_id"] = self._symbol_instance.symbol_id
        state["representation_id"] = self._symbol_instance.representation_id
        state["scale"] = self._symbol_instance.scale
        state["rotation"] = self._symbol_instance.rotation
        state["visible"] = self._symbol_instance.visible
        state["properties"] = dict(self._symbol_instance.properties)
        return state


__all__ = ["EquipmentItem"]
