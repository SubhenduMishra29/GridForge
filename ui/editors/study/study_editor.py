# ============================================================
# File: ui/editors/study/study_editor.py
# GridForge V2 — Study Editor
# Author: Subhendu Mishra
# ============================================================
"""Canonical Study/Results Area editor."""

from __future__ import annotations
from ui.core.qt import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from ui.editors.common.editor_host import EditorRegionFrame
from ui.editors.common.tool_shelf import ToolShelf, ToolSettingsPanel


class StudyEditor(QWidget):
    editor_type = "study"
    DEFAULT_REGION_ID = "canvas"

    def __init__(self, *, surface: QWidget | None = None, tool_shelf: QWidget | None = None, inspector: QWidget | None = None, tool_settings: QWidget | None = None, diagnostics: QWidget | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        header = EditorRegionFrame("Study Header", parent=self); header.set_widget(QLabel("Study Editor", header))
        canvas = EditorRegionFrame("Study Canvas", parent=self); canvas.set_widget(surface or QLabel("Study / Simulation results", self))
        shelf = EditorRegionFrame("Tool Shelf", parent=self); shelf.set_widget(tool_shelf or ToolShelf(parent=self))
        tool_settings_widget = tool_settings or ToolSettingsPanel(parent=self)
        settings = EditorRegionFrame("Tool Settings", parent=self); settings.set_widget(tool_settings_widget)
        explorer_region = EditorRegionFrame("Explorer", parent=self); explorer_region.set_widget(explorer or QLabel("Study Cases", self))
        inspector_region = EditorRegionFrame("Inspector", parent=self); inspector_region.set_widget(inspector or QLabel("Select a study result.", self))
        center = QVBoxLayout(); center.addWidget(settings); center.addWidget(canvas, 1)
        body = QHBoxLayout(); body.addWidget(explorer_region); body.addWidget(shelf); body.addLayout(center, 1); body.addWidget(inspector_region)
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.addWidget(header); root.addLayout(body, 1)
        if diagnostics is not None:
            region = EditorRegionFrame("Diagnostics", parent=self); region.set_widget(diagnostics); root.addWidget(region)
        if status is not None:
            status_region = EditorRegionFrame("Status", parent=self); status_region.set_widget(status); root.addWidget(status_region)
        self.setObjectName("StudyEditor")
        self._region_widgets = {"header": header, "explorer": explorer_region, "tool_shelf": shelf, "tool_settings": settings, "canvas": canvas, "sidebar": inspector_region, "diagnostics": region if diagnostics is not None else None, "status": status_region if status is not None else None}
        self._tool_shelf = shelf
        self._tool_settings = tool_settings_widget
        self._editor_context = None


    def region_widget(self, region_id: str) -> QWidget | None:
        return self._region_widgets.get(region_id)

    def set_editor_context(self, context: object | None) -> None:
        self._editor_context = context
        self._tool_shelf.refresh_runtime_state()
        settings = getattr(self._tool_settings, "set_context", None)
        if callable(settings): settings(context)
        self._tool_shelf.set_active_tool(getattr(context, "active_tool", None) if context is not None else None)


__all__ = ["StudyEditor"]
