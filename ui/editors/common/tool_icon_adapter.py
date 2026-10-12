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
from ui.styling.presentation_style import VisualState, palette_visual_pen


_LOG = logging.getLogger(__name__)


class ToolIconAdapter:
    """Presentation-only resolver for ToolDefinition -> QIcon.

    Tool identity remains owned by ToolDefinition/ToolManager. SymbolRegistry
    is consulted only as a reusable presentation catalogue; it is never used
    as the tool lifecycle authority.
    """

    _GENERIC_GLYPHS = {
        "select": "↖", "move": "✥", "pan": "✋", "wire": "⌁",
        "snap": "⊙", "delete": "×",
        "zoom_in": "+", "zoom_out": "−", "fit": "□",
        "electrical-insertion": "EI", "connect_measurement": "CM",
        "inspect": "I", "diagnostics": "!", "run": "▶", "cancel": "×",
        "run_study": "▶", "inspect_result": "IR", "compare_results": "⇄",
        "compare": "⇄", "plot": "∿", "filter": "▽", "export": "↓",
        "navigation": "↔", "navigate": "↔",
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

        explicit = definition.icon_id
        if explicit is None:
            _LOG.warning(
                "TOOL_ICON_METADATA_MISSING tool_id=%s editor=%s; using neutral glyph",
                definition.tool_id,
                next(iter(definition.editor_types), "unknown"),
            )
            return self._fallback_icon(definition.tool_id)

        # Resolve only the explicitly declared symbol. Never guess by tool ID:
        # a typo or absent symbol must not silently display unrelated artwork.
        icon = self._symbol_icon(explicit)
        if icon is not None:
            return icon

        _LOG.warning(
            "TOOL_ICON_RESOLUTION_FAILED tool_id=%s icon_id=%s editor=%s; using neutral glyph",
            definition.tool_id,
            explicit,
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
        icon = QIcon()
        states = (
            (QIcon.Mode.Normal, QIcon.State.Off, VisualState.NORMAL),
            (QIcon.Mode.Active, QIcon.State.Off, VisualState.HOVER),
            (QIcon.Mode.Normal, QIcon.State.On, VisualState.SELECTED),
            (QIcon.Mode.Active, QIcon.State.On, VisualState.SELECTED),
            (QIcon.Mode.Disabled, QIcon.State.Off, VisualState.DISABLED),
            (QIcon.Mode.Disabled, QIcon.State.On, VisualState.DISABLED),
        )
        for mode, icon_state, visual_state in states:
            icon.addPixmap(
                ToolIconAdapter._text_pixmap(text, visual_state),
                mode,
                icon_state,
            )
        return icon

    @staticmethod
    def _text_pixmap(text: str, state: VisualState) -> QPixmap:
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            # Palette glyphs and their outline share the canonical palette pen.
            # Engineering symbol colors remain owned by visual_pen()/symbol adapters.
            painter.setPen(palette_visual_pen(state))
            painter.setBrush(QBrush())
            painter.drawRoundedRect(QRectF(3, 3, 58, 58), 8, 8)
            painter.drawText(QRectF(5, 5, 54, 54), Qt.AlignmentFlag.AlignCenter, text)
        finally:
            painter.end()
        return pixmap


__all__ = ["ToolIconAdapter"]
