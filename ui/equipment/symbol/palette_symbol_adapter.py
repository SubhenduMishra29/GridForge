# ============================================================
# File: ui/equipment/symbol/palette_symbol_adapter.py
# GridForge V2 — Palette Symbol Presentation Adapter
# Author: Subhendu Mishra
# ============================================================
"""Presentation-only adapter from canonical symbols to palette QIcons."""

from __future__ import annotations

from typing import Any

from ui.core.qt import QBrush, QIcon, QPainter, QPen, QPixmap, QSize, Qt
from ui.equipment.symbol.symbol_definition import SymbolDefinition
from ui.equipment.symbol.symbol_registry import SymbolRegistry


class PaletteSymbolAdapter:
    """Render canonical SymbolDefinitions as high-DPI palette icons.

    This adapter owns no symbol catalogue and creates no equipment/tool state.
    It is deliberately a presentation boundary over the canonical registry.
    """

    def __init__(self, symbol_registry: SymbolRegistry) -> None:
        if not isinstance(symbol_registry, SymbolRegistry):
            raise TypeError("symbol_registry must be a SymbolRegistry.")
        self._symbol_registry = symbol_registry

    @property
    def symbol_registry(self) -> SymbolRegistry:
        return self._symbol_registry

    def icon_for(self, symbol_id: str) -> QIcon:
        definition = self._symbol_registry.require(symbol_id)
        icon = QIcon()
        icon.addPixmap(self._render(definition, state="normal"), QIcon.Mode.Normal)
        icon.addPixmap(self._render(definition, state="active"), QIcon.Mode.Active)
        icon.addPixmap(self._render(definition, state="selected"), QIcon.Mode.Selected)
        icon.addPixmap(self._render(definition, state="disabled"), QIcon.Mode.Disabled)
        return icon

    def _render(self, definition: SymbolDefinition, *, state: str) -> QPixmap:
        if not isinstance(definition, SymbolDefinition):
            raise TypeError("definition must be a SymbolDefinition.")
        logical_width = 72
        logical_height = 52
        scale = self._device_scale()
        pixmap = QPixmap(
            int(logical_width * scale),
            int(logical_height * scale),
        )
        pixmap.fill(Qt.GlobalColor.transparent)
        pixmap.setDevicePixelRatio(scale)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setOpacity({"disabled": 0.38, "normal": 0.95, "active": 1.0, "selected": 1.0}[state])

        pen = QPen()
        pen.setWidthF({"disabled": 1.0, "normal": 1.5, "active": 1.8, "selected": 2.2}[state])
        painter.setPen(pen)
        painter.setBrush(QBrush())

        scale_x = (logical_width - 8.0) / definition.width
        scale_y = (logical_height - 8.0) / definition.height
        transform_scale = min(scale_x, scale_y)
        painter.translate(logical_width / 2.0, logical_height / 2.0)
        painter.scale(transform_scale, transform_scale)

        for primitive in definition.primitives:
            self._draw_primitive(painter, primitive)

        painter.end()
        return pixmap

    @staticmethod
    def _draw_primitive(painter: QPainter, primitive: Any) -> None:
        kind = primitive.get("kind")
        if kind == "line":
            painter.drawLine(
                float(primitive["x1"]),
                float(primitive["y1"]),
                float(primitive["x2"]),
                float(primitive["y2"]),
            )
        elif kind == "rect":
            painter.drawRect(
                float(primitive["x"]),
                float(primitive["y"]),
                float(primitive["width"]),
                float(primitive["height"]),
            )
        elif kind == "circle":
            radius = float(primitive["r"])
            painter.drawEllipse(
                float(primitive["cx"]) - radius,
                float(primitive["cy"]) - radius,
                radius * 2.0,
                radius * 2.0,
            )

    @staticmethod
    def _device_scale() -> float:
        from ui.core.qt import QApplication

        application = QApplication.instance()
        if application is None:
            return 2.0
        value = float(application.devicePixelRatio())
        return max(1.0, min(value, 4.0))


__all__ = ["PaletteSymbolAdapter"]
