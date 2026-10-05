# ============================================================
# File: ui/editors/sld/sld_editor.py
# GridForge V2 — SLD Editor
# Author: Subhendu Mishra
# ============================================================

"""Canonical SLD Area editor composed from explicit presentation Regions."""

from __future__ import annotations

from ui.core.qt import QLabel, QHBoxLayout, QSplitter, QVBoxLayout, QWidget, Qt
from ui.editors.common.editor_host import EditorRegionFrame
from ui.editors.common.tool_shelf import ToolShelf, ToolSettingsPanel
from ui.tools.tool_definition import ToolDefinition, contextual_tool_definitions


class SLDEditor(QWidget):
    """Compose the SLD editor from the canonical Region contract."""

    editor_type = "sld"
    DEFAULT_REGION_ID = "canvas"

    def __init__(
        self,
        *,
        canvas: QWidget,
        tool_shelf: QWidget | None = None,
        inspector: QWidget | None = None,
        diagnostics: QWidget | None = None,
        tool_settings: QWidget | None = None,
        overlay: QWidget | None = None,
        explorer: QWidget | None = None,
        status: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if not isinstance(canvas, QWidget):
            raise TypeError("canvas must be QWidget.")

        header = EditorRegionFrame("SLD Header", parent=self)
        header.set_widget(QLabel("SLD Editor", header))

        shelf = tool_shelf or ToolShelf(definitions=contextual_tool_definitions(("select", "move", "wire", "bus", "transformer", "breaker", "disconnector", "generator", "load", "motor"), editor_type="sld"), editor_type="sld", parent=self)
        shelf_region = EditorRegionFrame("Tool Shelf", parent=self)
        shelf_region.set_widget(shelf)

        settings = tool_settings or ToolSettingsPanel(parent=self)
        settings_region = EditorRegionFrame("Tool Settings", parent=self)
        settings_region.set_widget(settings)

        canvas_region = EditorRegionFrame("Canvas", parent=self)
        canvas_region.set_widget(canvas)

        explorer_region = EditorRegionFrame("Explorer", parent=self)
        explorer_region.set_widget(explorer or QLabel("Project Explorer", self))
        inspector_region = EditorRegionFrame("Inspector", parent=self)
        inspector_region.set_widget(inspector or QLabel("Select an object to inspect.", self))

        left = QSplitter(Qt.Orientation.Vertical, self)
        left.addWidget(explorer_region)
        left.addWidget(shelf_region)
        left.setStretchFactor(0, 1)
        left.setStretchFactor(1, 2)

        center = QSplitter(Qt.Orientation.Vertical, self)
        center.addWidget(settings_region)
        center.addWidget(canvas_region)
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

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(header)
        root.addWidget(body, 1)
        if bottom.count():
            root.addWidget(bottom, 0)
        self.setObjectName("SLDEditor")
        self._region_widgets = {
            "header": header, "explorer": explorer_region, "tool_shelf": shelf_region,
            "tool_settings": settings_region, "canvas": canvas_region, "sidebar": inspector_region,
            "overlay": sidebar.itemAt(1).widget() if overlay is not None else None,
            "diagnostics": diagnostics_region if diagnostics is not None else None,
            "status": status_region if status is not None else None,
        }
        self._tool_shelf = shelf
        self._tool_settings = settings
        self._editor_context = None


    def region_widget(self, region_id: str) -> QWidget | None:
        return self._region_widgets.get(region_id)

    def apply_editor_definition(self, definition: object) -> None:
        """Apply canonical RegionDefinition sizing metadata to realized surfaces."""
        for region in getattr(definition, "regions", ()) or ():
            frame = self._region_widgets.get(getattr(region, "region_id", ""))
            if frame is None:
                continue
            minimum = int(getattr(region, "minimum_size", 0) or 0)
            if getattr(region, "region_id", "") in {"tool_shelf", "sidebar"}:
                frame.setMinimumWidth(minimum)
            elif getattr(region, "region_id", "") in {"header", "tool_settings", "diagnostics", "status"}:
                frame.setMinimumHeight(minimum)

    def set_editor_context(self, context: object | None) -> None:
        self._editor_context = context
        setter = getattr(self._tool_shelf, "refresh_runtime_state", None)
        if callable(setter): setter()
        settings = getattr(self._tool_settings, "set_context", None)
        if callable(settings): settings(context)
        active = getattr(context, "active_tool", None) if context is not None else None
        self._tool_shelf.set_active_tool(active)


__all__ = ["SLDEditor", "ToolDefinition"]
