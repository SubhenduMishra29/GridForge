# ============================================================
# File: ui/editors/study/study_editor.py
# GridForge V2 — Study Editor
# Author: Subhendu Mishra
# ============================================================
"""Canonical Study/Results Area editor."""

from __future__ import annotations
from ui.core.qt import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from ui.editors.common.editor_host import EditorRegionFrame
from ui.editors.common.tool_shelf import ToolShelf


class StudyEditor(QWidget):
    editor_type = "study"

    def __init__(self, *, surface: QWidget | None = None, tool_shelf: QWidget | None = None, inspector: QWidget | None = None, tool_settings: QWidget | None = None, diagnostics: QWidget | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        canvas = EditorRegionFrame("Study Canvas", parent=self); canvas.set_widget(surface or QLabel("Study / Simulation results", self))
        shelf = EditorRegionFrame("Tool Shelf", parent=self); shelf.set_widget(tool_shelf or ToolShelf(parent=self))
        settings = EditorRegionFrame("Tool Settings", parent=self); settings.set_widget(tool_settings or QLabel("Study Tool Settings", self))
        inspector_region = EditorRegionFrame("Inspector", parent=self); inspector_region.set_widget(inspector or QLabel("Select a study result.", self))
        center = QVBoxLayout(); center.addWidget(settings); center.addWidget(canvas, 1)
        body = QHBoxLayout(); body.addWidget(shelf); body.addLayout(center, 1); body.addWidget(inspector_region)
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.addWidget(QLabel("Study Editor", self)); root.addLayout(body, 1)
        if diagnostics is not None:
            region = EditorRegionFrame("Diagnostics", parent=self); region.set_widget(diagnostics); root.addWidget(region)
        self.setObjectName("StudyEditor")


__all__ = ["StudyEditor"]
