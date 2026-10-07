# ============================================================
# GridForge V2 — Tool Icon Presentation Adapter
# ============================================================
"""Resolve tool-shaft icons independently from equipment-palette icons."""

from __future__ import annotations

import logging

from ui.core.qt import QBrush, QIcon, QPainter, QPixmap, QRectF, Qt
from ui.equipment.symbol.palette_symbol_adapter import PaletteSymbolAdapter
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.tools.tool_definition import ToolDefinition


_LOG = logging.getLogger(__name__)


class ToolIconAdapter:
    """Presentation-only resolver for ToolDefinition -> QIcon.

    Tool identity remains owned by ToolDefinition/ToolManager. SymbolRegistry
    is consulted only as a reusable presentation catalogue; it is never used
    as the tool lifecycle authority.
    """

    _GENERIC_GLYPHS = {
        "select": "↖", "move": "✥", "pan": "✋", "wire": "⌁",
        "bus": "▰", "snap": "⊙", "delete": "×",
        "zoom_in": "+", "zoom_out": "−", "fit": "□",
        "line": "╱", "cable": "≋",
    }

    def __init__(self, symbol_registry: SymbolRegistry) -> None:
        if not isinstance(symbol_registry, SymbolRegistry):
            raise TypeError("symbol_registry must be a SymbolRegistry.")
        self._symbol_registry = symbol_registry
        self._palette_adapter = PaletteSymbolAdapter(symbol_registry)

    @property
    def symbol_registry(self) -> SymbolRegistry:
        return self._symbol_registry

    def icon_for(self, definition: ToolDefinition) -> QIcon:
        if not isinstance(definition, ToolDefinition):
            raise TypeError("definition must be a ToolDefinition.")

        # Generic interaction tools own their icon resolution and must not
        # accidentally depend on an equipment symbol with the same ID.
        generic = self._generic_icon(definition.tool_id)
        if generic is not None:
            return generic

        # Equipment tools may reuse canonical engineering artwork through the
        # palette adapter, but this remains a presentation-only fallback.
        explicit = definition.icon_id
        if explicit:
            icon = self._symbol_icon(explicit)
            if icon is not None:
                return icon

        canonical = self._symbol_icon(definition.tool_id)
        if canonical is not None:
            return canonical

        # Deterministic engineering fallback. This path is intentionally
        # non-empty so a missing symbol can never make the shaft blank.
        _LOG.warning(
            "TOOL_ICON_RESOLUTION_FAILED tool_id=%s icon_id=%s editor=%s",
            definition.tool_id,
            definition.icon_id,
            next(iter(definition.editor_types), "unknown"),
        )
        return self._fallback_icon(definition.tool_id)

    def _symbol_icon(self, symbol_id: str) -> QIcon | None:
        try:
            if not self._symbol_registry.contains(symbol_id):
                return None
            return self._palette_adapter.icon_for(symbol_id)
        except (KeyError, TypeError, ValueError):
            return None

    def _generic_icon(self, tool_id: str) -> QIcon | None:
        glyph = self._GENERIC_GLYPHS.get(str(tool_id).strip().lower())
        if glyph is None:
            return None
        return self._text_icon(glyph)

    def _fallback_icon(self, tool_id: str) -> QIcon:
        value = str(tool_id).strip().replace("_", " ")
        glyph = value[:2].upper() if value else "?"
        return self._text_icon(glyph)

    @staticmethod
    def _text_icon(text: str) -> QIcon:
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.GlobalColor.black)
            painter.setBrush(QBrush())
            painter.drawRoundedRect(QRectF(3, 3, 58, 58), 8, 8)
            painter.drawText(QRectF(5, 5, 54, 54), Qt.AlignmentFlag.AlignCenter, text)
        finally:
            painter.end()
        return QIcon(pixmap)


__all__ = ["ToolIconAdapter"]
