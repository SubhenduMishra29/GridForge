# ============================================================
# File: ui/editors/protection/protection_editor.py
# GridForge V2 — Protection Editor
# Author: Subhendu Mishra
# ============================================================
"""Canonical Protection Area editor composed from explicit Regions."""

from __future__ import annotations
from ui.core.qt import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from ui.editors.common.editor_host import EditorRegionFrame
from ui.editors.common.tool_shelf import ToolShelf


class ProtectionEditor(QWidget):
    editor_type = "protection"

    def __init__(self, *, surface: QWidget, tool_shelf: QWidget | None = None, inspector: QWidget | None = None, tool_settings: QWidget | None = None, diagnostics: QWidget | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        canvas = EditorRegionFrame("Canvas", parent=self); canvas.set_widget(surface)
        shelf = EditorRegionFrame("Tool Shelf", parent=self); shelf.set_widget(tool_shelf or ToolShelf(parent=self))
        settings = EditorRegionFrame("Tool Settings", parent=self); settings.set_widget(tool_settings or QLabel("Tool Settings", self))
        inspector_region = EditorRegionFrame("Inspector", parent=self); inspector_region.set_widget(inspector or QLabel("Select a protection object.", self))
        center = QVBoxLayout(); center.addWidget(settings); center.addWidget(canvas, 1)
        body = QHBoxLayout(); body.addWidget(shelf); body.addLayout(center, 1); body.addWidget(inspector_region)
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.addWidget(QLabel("Protection Editor", self)); root.addLayout(body, 1)
        if diagnostics is not None:
            region = EditorRegionFrame("Diagnostics", parent=self); region.set_widget(diagnostics); root.addWidget(region)
        self.setObjectName("ProtectionEditor")


__all__ = ["ProtectionEditor"]
