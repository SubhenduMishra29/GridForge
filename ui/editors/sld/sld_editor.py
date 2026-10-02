# ============================================================
# File: ui/editors/sld/sld_editor.py
# GridForge V2 — SLD Editor
# Author: Subhendu Mishra
# ============================================================

"""Canonical SLD Area editor composed from explicit presentation Regions."""

from __future__ import annotations

from ui.core.qt import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from ui.editors.common.editor_host import EditorRegionFrame
from ui.editors.common.tool_shelf import ToolShelf
from ui.tools.tool_definition import ToolDefinition


class SLDEditor(QWidget):
    """Compose Header, Tool Shelf, Tool Settings, Canvas and Inspector regions."""

    editor_type = "sld"

    def __init__(
        self,
        *,
        canvas: QWidget,
        tool_shelf: QWidget | None = None,
        inspector: QWidget | None = None,
        diagnostics: QWidget | None = None,
        tool_settings: QWidget | None = None,
        overlay: QWidget | None = None,
        status: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if not isinstance(canvas, QWidget):
            raise TypeError("canvas must be QWidget.")

        header = EditorRegionFrame("SLD Header", parent=self)
        header.set_widget(QLabel("SLD Editor", header))

        shelf = tool_shelf or ToolShelf(parent=self)
        shelf_region = EditorRegionFrame("Tool Shelf", parent=self)
        shelf_region.set_widget(shelf)

        settings = tool_settings or QLabel("Tool Settings", self)
        settings_region = EditorRegionFrame("Tool Settings", parent=self)
        settings_region.set_widget(settings)

        canvas_region = EditorRegionFrame("Canvas", parent=self)
        canvas_region.set_widget(canvas)

        inspector_region = EditorRegionFrame("Inspector", parent=self)
        inspector_region.set_widget(inspector or QLabel("Select an object to inspect.", self))

        body = QHBoxLayout()
        body.addWidget(shelf_region)
        center = QVBoxLayout()
        center.addWidget(settings_region)
        center.addWidget(canvas_region, 1)
        body.addLayout(center, 1)
        sidebar = QVBoxLayout()
        sidebar.addWidget(inspector_region, 1)
        if overlay is not None:
            overlay_region = EditorRegionFrame("Overlay", parent=self)
            overlay_region.set_widget(overlay)
            sidebar.addWidget(overlay_region)
        body.addLayout(sidebar)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(header)
        root.addLayout(body, 1)
        if diagnostics is not None:
            diagnostics_region = EditorRegionFrame("Diagnostics", parent=self)
            diagnostics_region.set_widget(diagnostics)
            root.addWidget(diagnostics_region)
        if status is not None:
            status_region = EditorRegionFrame("Status", parent=self)
            status_region.set_widget(status)
            root.addWidget(status_region)
        self.setObjectName("SLDEditor")


__all__ = ["SLDEditor", "ToolDefinition"]
