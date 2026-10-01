# ============================================================
# File: ui/items/equipment_item.py
# GridForge V2 — Symbol-aware Equipment Graphics Projection
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QBrush, QFont, QGraphicsItem, QPainter, QPen, QRectF, QPointF, Qt, QColor, Signal
from ui.equipment.equipment_base import EquipmentBase
from ui.equipment.symbol.symbol_base import SymbolBase
from ui.equipment.symbol.symbol_definition import SymbolDefinition
from ui.styling.presentation_style import PresentationState, VisualState, visual_brush, visual_font, visual_pen, token_color

from .base_item import BaseItem


class EquipmentItem(BaseItem):
    """Presentation-only graphics projection for one canonical SLD symbol."""

    position_changed = Signal(object)

    def __init__(
        self,
        object_id: Any,
        element_type: str,
        *,
        position: object = None,
        symbol_definition: SymbolDefinition,
        equipment: EquipmentBase,
        symbol_instance: SymbolBase | None = None,
        parent: Optional[BaseItem] = None,
    ) -> None:
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
            raise ValueError("symbol_instance must resolve to the supplied SymbolDefinition.")
        if symbol_instance.representation_id != "symbol":
            raise ValueError(
                f"Unsupported SLD representation: {symbol_instance.representation_id!r}"
            )
        self._symbol_instance = SymbolBase.from_dict(symbol_instance.to_dict())
        self._visual_state = VisualState.NORMAL
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.set_presentation_state(PresentationState(visual_state=VisualState.NORMAL, readout=f"{self._element_type}: {self.object_id}"))
        self.setAcceptHoverEvents(True)
        mirror_x = bool(self._symbol_instance.get_property("mirror_x", False))
        mirror_y = bool(self._symbol_instance.get_property("mirror_y", False))
        self.setScale(self._symbol_instance.scale * (-1.0 if mirror_x else 1.0))
        self.setRotation(self._symbol_instance.rotation + (180.0 if mirror_x and mirror_y else 0.0))
        self.setVisible(self._symbol_instance.visible)
        if position is not None:
            self.setPos(position)

    def itemChange(self, change: Any, value: Any) -> Any:
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and value is not None:
            self.position_changed.emit(QPointF(float(value.x()), float(value.y())))
        return result

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
        return self._symbol_instance

    @property
    def visual_state(self) -> VisualState:
        return self._visual_state

    def set_visual_state(self, state: VisualState | str) -> None:
        normalized = state if isinstance(state, VisualState) else VisualState(str(state).lower())
        self._visual_state = normalized
        current = self.presentation_state
        self.set_presentation_state(PresentationState(visual_state=normalized, status=current.status, tool_state=current.tool_state, readout=current.readout or f"{self._element_type}: {self.object_id}"))

    def set_invalid(self, invalid: bool = True) -> None:
        self.set_visual_state(VisualState.INVALID if invalid else VisualState.NORMAL)

    def snap_points(self):
        points = []
        for terminal in self._equipment.terminals:
            local_anchor = self._symbol_definition.get_terminal_anchor(terminal.terminal_name)
            mirror_x = bool(self._symbol_instance.get_property("mirror_x", False))
            mirror_y = bool(self._symbol_instance.get_property("mirror_y", False))
            local_x = -float(local_anchor[0]) if mirror_x else float(local_anchor[0])
            local_y = -float(local_anchor[1]) if mirror_y else float(local_anchor[1])
            scene_point = self.mapToScene(QPointF(local_x, local_y))
            points.append({
                "position": scene_point,
                "object_id": self.object_id,
                "terminal_id": terminal.terminal_id,
                "terminal_name": terminal.terminal_name,
            })
        return tuple(points)

    def boundingRect(self) -> QRectF:
        return QRectF(
            -self._symbol_definition.width / 2,
            -self._symbol_definition.height / 2,
            self._symbol_definition.width,
            self._symbol_definition.height,
        )

    def _effective_state(self) -> VisualState:
        if self._visual_state not in {VisualState.NORMAL, VisualState.HOVER}:
            return self._visual_state
        if self.isSelected():
            return VisualState.SELECTED
        if self.isUnderMouse():
            return VisualState.HOVER
        return VisualState.NORMAL

    def paint(self, painter: QPainter, option: Any = None, widget: Any = None) -> None:
        del option, widget
        state = self._effective_state()
        role = "protection" if self._element_type.lower() == "relay" else "symbol"
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(visual_pen(role, state, width=1.8))
        painter.setBrush(visual_brush(role, state))
        painter.setFont(visual_font("engineering"))
        for primitive in self._symbol_definition.primitives:
            kind = primitive.get("kind")
            if kind == "line":
                painter.drawLine(
                    float(primitive["x1"]), float(primitive["y1"]),
                    float(primitive["x2"]), float(primitive["y2"]),
                )
            elif kind == "rect":
                painter.drawRect(
                    float(primitive["x"]), float(primitive["y"]),
                    float(primitive["width"]), float(primitive["height"]),
                )
            elif kind == "circle":
                radius = float(primitive["r"])
                painter.drawEllipse(
                    float(primitive["cx"]) - radius,
                    float(primitive["cy"]) - radius,
                    radius * 2.0,
                    radius * 2.0,
                )
            elif kind == "text":
                # SLD canvas is deliberately white; engineering annotations must
                # use the canonical dark-on-light text token rather than the
                # light symbol stroke used for geometry.
                painter.setPen(QPen(token_color("text_inverse")))
                painter.setFont(visual_font("engineering"))
                painter.drawText(
                    QRectF(
                        float(primitive["x"]), float(primitive["y"]),
                        float(primitive["width"]), float(primitive["height"]),
                    ),
                    Qt.AlignmentFlag.AlignCenter,
                    str(primitive["text"]),
                )

    def hoverEnterEvent(self, event: Any) -> None:
        if self._visual_state == VisualState.NORMAL:
            self.set_visual_state(VisualState.HOVER)
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: Any) -> None:
        if self._visual_state == VisualState.HOVER:
            self.set_visual_state(VisualState.NORMAL)
        self.update()
        super().hoverLeaveEvent(event)

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state.update({
            "element_type": self._element_type,
            "mirror_x": bool(self._symbol_instance.get_property("mirror_x", False)),
            "mirror_y": bool(self._symbol_instance.get_property("mirror_y", False)),
            "symbol_id": self._symbol_instance.symbol_id,
            "representation_id": self._symbol_instance.representation_id,
            "scale": self._symbol_instance.scale,
            "rotation": self._symbol_instance.rotation,
            "visible": self._symbol_instance.visible,
            "properties": dict(self._symbol_instance.properties),
            "visual_state": self._visual_state.value,
        })
        return state


__all__ = ["EquipmentItem"]
