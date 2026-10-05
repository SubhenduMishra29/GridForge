# ============================================================
# File: ui/editors/protection/protection_editor.py
# GridForge V2 — Protection Editor
# Author: Subhendu Mishra
# ============================================================
"""Canonical Protection Area editor composed from explicit Regions."""

from __future__ import annotations
from ui.core.qt import QLabel, QHBoxLayout, QSplitter, QVBoxLayout, QWidget, Qt
from ui.editors.common.editor_host import EditorRegionFrame
from ui.editors.common.tool_shelf import ToolShelf, ToolSettingsPanel
from ui.tools.tool_definition import contextual_tool_definitions


class ProtectionEditor(QWidget):
    editor_type = "protection"
    DEFAULT_REGION_ID = "canvas"

    def __init__(
        self,
        *,
        surface: QWidget,
        explorer: QWidget | None = None,
        tool_shelf: QWidget | None = None,
        inspector: QWidget | None = None,
        tool_settings: QWidget | None = None,
        diagnostics: QWidget | None = None,
        status: QWidget | None = None,
        overlay: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        header = EditorRegionFrame("Protection Header", parent=self); header.set_widget(QLabel("Protection Editor", header))
        canvas = EditorRegionFrame("Canvas", parent=self); canvas.set_widget(surface)
        shelf = EditorRegionFrame("Tool Shelf", parent=self); shelf.set_widget(tool_shelf or ToolShelf(definitions=contextual_tool_definitions(("select", "connect_measurement", "inspect", "fit", "diagnostics"), editor_type="protection"), editor_type="protection", parent=self))
        tool_settings_widget = tool_settings or ToolSettingsPanel(parent=self)
        settings = EditorRegionFrame("Tool Settings", parent=self); settings.set_widget(tool_settings_widget)
        explorer_region = EditorRegionFrame("Explorer", parent=self); explorer_region.set_widget(explorer or QLabel("Protection Explorer", self))
        inspector_region = EditorRegionFrame("Inspector", parent=self); inspector_region.set_widget(inspector or QLabel("Select a protection object.", self))

        left = QSplitter(Qt.Orientation.Vertical, self)
        left.addWidget(explorer_region)
        left.addWidget(shelf)
        left.setStretchFactor(0, 1)
        left.setStretchFactor(1, 2)

        center = QSplitter(Qt.Orientation.Vertical, self)
        center.addWidget(settings)
        center.addWidget(canvas)
        center.setStretchFactor(0, 0)
        center.setStretchFactor(1, 1)

        sidebar = QSplitter(Qt.Orientation.Vertical, self)
        sidebar.addWidget(inspector_region)
        overlay_region = None
        if overlay is not None:
            overlay_region = EditorRegionFrame("Overlay", parent=self)
            overlay_region.set_widget(overlay)
            sidebar.addWidget(overlay_region)
            sidebar.setStretchFactor(0, 3)
            sidebar.setStretchFactor(1, 1)

        body = QSplitter(Qt.Orientation.Horizontal, self)
        body.addWidget(left)
        body.addWidget(center)
        body.addWidget(sidebar)
        body.setStretchFactor(0, 0)
        body.setStretchFactor(1, 1)
        body.setStretchFactor(2, 0)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(header)
        root.addWidget(body, 1)

        bottom = QSplitter(Qt.Orientation.Vertical, self)
        diagnostics_region = None
        status_region = None
        if diagnostics is not None:
            diagnostics_region = EditorRegionFrame("Diagnostics", parent=self)
            diagnostics_region.set_widget(diagnostics)
            bottom.addWidget(diagnostics_region)
        if status is not None:
            status_region = EditorRegionFrame("Status", parent=self)
            status_region.set_widget(status)
            bottom.addWidget(status_region)
        if bottom.count():
            bottom.setStretchFactor(0, 1)
            if bottom.count() > 1:
                bottom.setStretchFactor(1, 0)
            root.addWidget(bottom, 0)

        self.setObjectName("ProtectionEditor")
        self._region_widgets = {"header": header, "explorer": explorer_region, "tool_shelf": shelf, "tool_settings": settings, "canvas": canvas, "sidebar": inspector_region, "overlay": overlay_region, "diagnostics": diagnostics_region, "status": status_region}
        self._tool_shelf = shelf
        self._tool_settings = tool_settings_widget
        self._editor_context = None
        self._region_splitters = {"body": body, "left": left, "center": center, "sidebar": sidebar, "bottom": bottom}

    def region_widget(self, region_id: str) -> QWidget | None:
        return self._region_widgets.get(region_id)

    def apply_editor_definition(self, definition: object) -> None:
        """Apply canonical RegionDefinition minimum/preferred sizing hints."""
        preferred: dict[str, int] = {}
        for region in getattr(definition, "regions", ()) or ():
            region_id = getattr(region, "region_id", "")
            frame = self._region_widgets.get(region_id)
            minimum = int(getattr(region, "minimum_size", 0) or 0)
            if frame is not None:
                if region_id in {"tool_shelf", "sidebar"}:
                    frame.setMinimumWidth(minimum)
                elif region_id in {"header", "tool_settings", "diagnostics", "status"}:
                    frame.setMinimumHeight(minimum)
            value = getattr(region, "preferred_size", None)
            if value is not None:
                preferred[region_id] = int(value)

        body = self._region_splitters["body"]
        shelf = preferred.get("tool_shelf")
        sidebar = preferred.get("sidebar")
        if body.width() > 0 and shelf is not None and sidebar is not None:
            center_size = max(1, body.width() - shelf - sidebar)
            body.setSizes([shelf, center_size, sidebar])

        left = self._region_splitters["left"]
        shelf_height = preferred.get("tool_shelf")
        if left.height() > 0 and shelf_height is not None:
            left.setSizes([max(1, left.height() - shelf_height), shelf_height])

        center = self._region_splitters["center"]
        settings_height = preferred.get("tool_settings")
        if center.height() > 0 and settings_height is not None:
            center.setSizes([settings_height, max(1, center.height() - settings_height)])

        bottom = self._region_splitters["bottom"]
        diagnostics_height = preferred.get("diagnostics")
        status_height = preferred.get("status")
        if bottom.height() > 0 and diagnostics_height is not None and status_height is not None:
            bottom.setSizes([diagnostics_height, status_height])

    def set_editor_context(self, context: object | None) -> None:
        self._editor_context = context
        self._tool_shelf.refresh_runtime_state()
        settings = getattr(self._tool_settings, "set_context", None)
        if callable(settings): settings(context)
        self._tool_shelf.set_active_tool(getattr(context, "active_tool", None) if context is not None else None)


__all__ = ["ProtectionEditor"]
