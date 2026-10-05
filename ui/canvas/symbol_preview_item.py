# ============================================================
# File: ui/canvas/symbol_preview_item.py
# GridForge V2 — Transient Symbol Preview Item
# Author: Subhendu Mishra
# ============================================================
"""Transient Qt realization of canonical renderer-neutral SLD symbols."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from ui.core.qt import QBrush, QGraphicsItem, QPainter, QPen, QRectF, Qt
from ui.equipment.symbol.symbol_definition import SymbolDefinition
from ui.styling.presentation_style import VisualState, visual_brush, visual_pen, visual_font


class SymbolPreviewItem(QGraphicsItem):
    """Temporary canvas realization driven exclusively by SymbolDefinition."""

    def __init__(
        self,
        definition: SymbolDefinition,
        *,
        position: Any,
        rotation: float = 0.0,
        presentation_state: Mapping[str, Any] | None = None,
        draft_id: str | None = None,
        terminal_names: tuple[str, ...] = (),
        element_type: str = "",
    ) -> None:
        if not isinstance(definition, SymbolDefinition):
            raise TypeError("definition must be a SymbolDefinition.")
        super().__init__()
        self._definition = definition
        self._draft_id = draft_id
        self._terminal_names = tuple(terminal_names)
        self._element_type = str(element_type)
        self._presentation_state = MappingProxyType(dict(presentation_state or {}))
        self._visual_state = VisualState.PREVIEW
        self.setPos(self._point(position))
        self.setRotation(float(rotation))
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    @property
    def object_id(self) -> str | None:
        return self._draft_id

    @property
    def is_draft_presentation(self) -> bool:
        return self._draft_id is not None

    def commit_draft(self, draft_id: str, terminal_names: tuple[str, ...], element_type: str) -> None:
        if not isinstance(draft_id, str) or not draft_id.strip():
            raise ValueError("draft_id must be non-empty.")
        self._draft_id = draft_id
        self._terminal_names = tuple(terminal_names)
        self._element_type = str(element_type)

    def snap_points(self):
        if self._draft_id is None:
            return ()
        points = []
        for role in self._terminal_names:
            anchor = self._definition.get_terminal_anchor(role)
            from ui.core.qt import QPointF
            point = self.mapToScene(QPointF(float(anchor[0]), float(anchor[1])))
            points.append({
                "position": point,
                "object_id": self._draft_id,
                "draft_id": self._draft_id,
                "terminal_id": f"{self._draft_id}:{role}",
                "terminal_name": role,
                "draft_terminal_role": role,
                "draft_equipment_type": self._element_type,
            })
        return tuple(points)

    def boundingRect(self) -> QRectF:
        return QRectF(
            -self._definition.width / 2.0,
            -self._definition.height / 2.0,
            self._definition.width,
            self._definition.height,
        )

    def paint(self, painter: QPainter, option: Any, widget: Any = None) -> None:
        del option, widget
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(visual_pen("symbol", self._visual_state, width=1.8))
        painter.setBrush(visual_brush("symbol", self._visual_state))
        painter.setFont(visual_font("engineering"))
        for primitive in self._definition.primitives:
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
                painter.drawText(
                    QRectF(float(primitive["x"]), float(primitive["y"]), float(primitive["width"]), float(primitive["height"])),
                    Qt.AlignmentFlag.AlignCenter,
                    str(primitive["text"]),
                )

    @staticmethod
    def _point(value: Any):
        if hasattr(value, "x") and hasattr(value, "y"):
            x = value.x() if callable(value.x) else value.x
            y = value.y() if callable(value.y) else value.y
            from ui.core.qt import QPointF
            return QPointF(float(x), float(y))
        if isinstance(value, (tuple, list)) and len(value) >= 2:
            from ui.core.qt import QPointF
            return QPointF(float(value[0]), float(value[1]))
        raise TypeError("Preview position must expose x/y coordinates.")


__all__ = ["SymbolPreviewItem"]
