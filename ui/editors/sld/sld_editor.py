# ============================================================
# File: ui/editors/sld/sld_editor.py
# GridForge V2 — SLD Editor
# Author: Subhendu Mishra
# ============================================================

"""Canonical SLD Area editor composed from explicit presentation Regions."""

from __future__ import annotations

from ui.core.qt import QLabel, QHBoxLayout, QSplitter, QToolButton, QVBoxLayout, QWidget, Qt
from ui.editors.common.editor_host import EditorRegionFrame
from ui.editors.common.tool_shelf import ToolShelf, ToolSettingsPanel
from ui.tools.tool_definition import ToolDefinition, contextual_tool_definitions


class SLDEditor(QWidget):
    """Professional 2D SLD authoring surface with contextual secondary regions."""

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

        # Compact editor header: identity plus contextual presentation controls.
        header = EditorRegionFrame("SLD", parent=self)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(6, 2, 6, 2)
        title = QLabel("SLD", header)
        title.setObjectName("GridForgeSLDTitle")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        self._panel_buttons: dict[str, QToolButton] = {}
        for region_id, label in (
            ("explorer", "Explorer"),
            ("sidebar", "Inspector"),
            ("diagnostics", "Messages"),
        ):
            button = QToolButton(header)
            button.setText(label)
            button.setCheckable(True)
            button.setAutoRaise(True)
            button.setToolTip(f"Show/hide {label.lower()}.")
            button.clicked.connect(
                lambda checked, rid=region_id: self.set_region_visible(rid, checked, user=True)
            )
            self._panel_buttons[region_id] = button
            header_layout.addWidget(button)

        self._restore_button = QToolButton(header)
        self._restore_button.setText("Restore")
        self._restore_button.setAutoRaise(True)
        self._restore_button.setToolTip("Restore the SLD workspace panels.")
        self._restore_button.clicked.connect(lambda: self.set_presentation_maximized(False))
        self._restore_button.setVisible(False)
        header_layout.addWidget(self._restore_button)
        header_content = QWidget(header)
        header_content.setLayout(header_layout)
        header.set_widget(header_content)

        shelf = tool_shelf or ToolShelf(
            definitions=contextual_tool_definitions(
                ("select", "move", "pan", "wire", "bus", "transformer", "breaker", "disconnector", "generator", "load", "motor"),
                editor_type="sld",
            ),
            editor_type="sld",
            parent=self,
        )
        shelf_region = EditorRegionFrame("Tools", parent=self)
        shelf_region.set_widget(shelf)

        settings = tool_settings or ToolSettingsPanel(parent=self)
        settings_region = EditorRegionFrame("Tool Settings", parent=self)
        settings_region.set_widget(settings)

        canvas_region = EditorRegionFrame("Canvas", parent=self)
        canvas_region.set_widget(canvas)

        explorer_region = EditorRegionFrame("Explorer", parent=self)
        explorer_region.set_widget(explorer or QWidget(self))

        inspector_region = EditorRegionFrame("Inspector", parent=self)
        inspector_region.set_widget(inspector or QWidget(self))

        left = QSplitter(Qt.Orientation.Vertical, self)
        left.setChildrenCollapsible(True)
        left.addWidget(explorer_region)
        left.addWidget(shelf_region)
        left.setStretchFactor(0, 1)
        left.setStretchFactor(1, 0)
        left.setSizes([0, 52])

        center = QSplitter(Qt.Orientation.Vertical, self)
        center.setChildrenCollapsible(True)
        center.addWidget(settings_region)
        center.addWidget(canvas_region)
        center.setStretchFactor(0, 0)
        center.setStretchFactor(1, 1)
        center.setSizes([0, 1])

        sidebar = QSplitter(Qt.Orientation.Vertical, self)
        sidebar.setChildrenCollapsible(True)
        sidebar.addWidget(inspector_region)
        overlay_region = EditorRegionFrame("Overlay", parent=self)
        overlay_region.set_widget(overlay or QWidget(self))
        overlay_region.setVisible(False)
        sidebar.addWidget(overlay_region)
        sidebar.setStretchFactor(0, 1)
        sidebar.setStretchFactor(1, 0)
        sidebar.setSizes([0, 0])

        body = QSplitter(Qt.Orientation.Horizontal, self)
        body.setChildrenCollapsible(True)
        body.addWidget(left)
        body.addWidget(center)
        body.addWidget(sidebar)
        body.setStretchFactor(0, 0)
        body.setStretchFactor(1, 1)
        body.setStretchFactor(2, 0)
        body.setSizes([52, 1, 0])

        diagnostics_region = EditorRegionFrame("Messages", parent=self)
        diagnostics_region.set_widget(diagnostics or QWidget(self))
        diagnostics_region.setVisible(False)

        status_region = EditorRegionFrame("Status", parent=self)
        self._status_label = status or QLabel("SLD | Select | Snap ON | Grid ON", status_region)
        status_region.set_widget(self._status_label)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(header, 0)
        root.addWidget(body, 1)
        root.addWidget(diagnostics_region, 0)
        root.addWidget(status_region, 0)

        self.setObjectName("SLDEditor")
        self._region_widgets = {
            "header": header,
            "explorer": explorer_region,
            "tool_shelf": shelf_region,
            "tool_settings": settings_region,
            "canvas": canvas_region,
            "sidebar": inspector_region,
            "overlay": overlay_region,
            "diagnostics": diagnostics_region,
            "status": status_region,
        }
        self._tool_shelf = shelf
        self._tool_settings = settings
        self._editor_context = None
        self._region_splitters = {
            "body": body,
            "left": left,
            "center": center,
            "sidebar": sidebar,
        }
        for frame in (
            header, shelf_region, settings_region, canvas_region,
            explorer_region, inspector_region, overlay_region,
            diagnostics_region, status_region,
        ):
            frame.set_title_visible(False)

        self._region_user_visibility: dict[str, bool] = {}
        self._region_user_overrides: set[str] = set()
        self._definition_visibility: dict[str, bool] = {}
        self._presentation_maximized = False
        self._maximize_callback = None

        # Defaults: only the engineering surface, compact tool shelf and status
        # remain permanently visible. Secondary regions are contextual.
        for region_id in ("explorer", "sidebar", "diagnostics", "tool_settings"):
            self.set_region_visible(region_id, False, user=False)

    def set_maximize_callback(self, callback) -> None:
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable or None.")
        self._maximize_callback = callback

    def region_widget(self, region_id: str) -> QWidget | None:
        return self._region_widgets.get(region_id)

    def apply_editor_definition(self, definition: object) -> None:
        preferred: dict[str, int] = {}
        for region in getattr(definition, "regions", ()) or ():
            region_id = getattr(region, "region_id", "")
            frame = self._region_widgets.get(region_id)
            visible = bool(getattr(region, "visible", True))
            self._definition_visibility[region_id] = visible
            if region_id not in self._region_user_overrides:
                self._region_user_visibility[region_id] = visible
            if region_id in {"header", "canvas", "status"}:
                self._region_user_visibility[region_id] = True
            if frame is not None:
                minimum = int(getattr(region, "minimum_size", 0) or 0)
                if region_id in {"tool_shelf", "explorer", "sidebar"}:
                    frame.setMinimumWidth(minimum)
                elif region_id in {"header", "tool_settings", "diagnostics", "status"}:
                    frame.setMinimumHeight(minimum)
                if region_id not in {"header", "canvas", "status"}:
                    frame.setVisible(self._region_user_visibility[region_id])
            value = getattr(region, "preferred_size", None)
            if value is not None:
                preferred[region_id] = int(value)

        self._apply_splitter_sizes(preferred)
        self._sync_panel_buttons()

    def _apply_splitter_sizes(self, preferred: dict[str, int] | None = None) -> None:
        preferred = preferred or {}
        body = self._region_splitters["body"]
        if body.width() > 0:
            shelf = max(44, preferred.get("tool_shelf", 52))
            sidebar = preferred.get("sidebar", 280)
            sidebar = sidebar if self._region_widgets["sidebar"].isVisible() else 0
            body.setSizes([shelf, max(1, body.width() - shelf - sidebar), sidebar])

        left = self._region_splitters["left"]
        if left.height() > 0:
            explorer = preferred.get("explorer", 220)
            explorer = explorer if self._region_widgets["explorer"].isVisible() else 0
            left.setSizes([explorer, max(1, left.height() - explorer)])

        center = self._region_splitters["center"]
        if center.height() > 0:
            settings = preferred.get("tool_settings", 42)
            settings = settings if self._region_widgets["tool_settings"].isVisible() else 0
            center.setSizes([settings, max(1, center.height() - settings)])

    def set_region_visible(self, region_id: str, visible: bool, *, user: bool = True) -> None:
        if region_id not in self._region_widgets:
            raise KeyError(f"Unknown SLD region: {region_id!r}")
        if region_id in {"header", "canvas", "status"}:
            return
        visible = bool(visible)
        if user:
            self._region_user_overrides.add(region_id)
            self._region_user_visibility[region_id] = visible
        frame = self._region_widgets[region_id]
        frame.setVisible(visible)
        self._apply_splitter_sizes()
        self._sync_panel_buttons()

    def update_contextual_regions(self) -> None:
        selected = getattr(getattr(self._editor_context, "engineering", None), "selected_ids", ()) or ()
        # Selection is a useful reason to surface the inspector. An explicit
        # user visibility choice always wins over contextual automation.
        if "sidebar" not in self._region_user_overrides:
            self.set_region_visible("sidebar", bool(selected), user=False)
        self._sync_panel_buttons()

    def _sync_panel_buttons(self) -> None:
        for region_id, button in self._panel_buttons.items():
            button.setChecked(self._region_widgets[region_id].isVisible())

    def set_presentation_maximized(self, maximized: bool) -> None:
        maximized = bool(maximized)
        if self._presentation_maximized == maximized:
            return
        self._presentation_maximized = maximized
        if maximized:
            self._restore_visibility = {
                rid: self._region_widgets[rid].isVisible()
                for rid in ("explorer", "tool_shelf", "tool_settings", "sidebar", "diagnostics")
            }
            for rid in ("explorer", "tool_shelf", "tool_settings", "sidebar", "diagnostics"):
                self._region_widgets[rid].setVisible(False)
            self._restore_button.setVisible(True)
        else:
            for rid, visible in getattr(self, "_restore_visibility", {}).items():
                self._region_widgets[rid].setVisible(visible)
            self._restore_button.setVisible(False)
        self._apply_splitter_sizes()
        self._sync_panel_buttons()
        if callable(self._maximize_callback):
            self._maximize_callback(maximized)

    def set_editor_context(self, context: object | None) -> None:
        self._editor_context = context
        setter = getattr(self._tool_shelf, "refresh_runtime_state", None)
        if callable(setter):
            setter()
        settings = getattr(self._tool_settings, "set_context", None)
        if callable(settings):
            settings(context)
        active = getattr(context, "active_tool", None) if context is not None else None
        self._tool_shelf.set_active_tool(active)
        tool_settings = getattr(context, "tool_settings", None) if context is not None else None
        has_tool_settings = bool(tool_settings is not None and getattr(tool_settings, "values", {}))
        self.set_region_visible("tool_settings", has_tool_settings, user=False)
        self.update_contextual_regions()
        selected = getattr(getattr(context, "engineering", None), "selected_ids", ()) or ()
        snap = getattr(getattr(context, "engineering", None), "snap_enabled", True)
        grid = getattr(getattr(context, "engineering", None), "grid_visible", True)
        self._status_label.setText(
            f"SLD | {active or 'Select'} | Snap {'ON' if snap else 'OFF'} | "
            f"Grid {'ON' if grid else 'OFF'} | Selected: {len(selected)}"
        )


__all__ = ["SLDEditor", "ToolDefinition"]

__all__ = ["SLDEditor", "ToolDefinition"]
