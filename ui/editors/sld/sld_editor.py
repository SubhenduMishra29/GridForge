# ============================================================
# File: ui/editors/sld/sld_editor.py
# GridForge V2 — SLD Editor
# Author: Subhendu Mishra
# ============================================================

"""Canonical SLD Area editor composed from explicit presentation Regions."""

from __future__ import annotations

import logging

from ui.core.qt import QEvent, QLabel, QHBoxLayout, QSplitter, QToolButton, QVBoxLayout, QWidget, Qt
from ui.editors.common.editor_host import EditorRegionFrame
from ui.editors.common.tool_shelf import ToolShelf, ToolSettingsPanel
from ui.tools.tool_definition import ToolDefinition, contextual_tool_definitions
from ui.editors.sld.sld_document_tabs import SLDDocumentTabs

_LOG = logging.getLogger(__name__)


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
        document_tabs: SLDDocumentTabs | None = None,
        icon_provider=None,
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
            button.setAccessibleName(f"Toggle {label} panel")
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
        self._restore_button.setAccessibleName("Restore SLD workspace panels")
        self._restore_button.setAutoRaise(True)
        self._restore_button.setToolTip("Restore the SLD workspace panels.")
        self._restore_button.clicked.connect(lambda: self.set_presentation_maximized(False))
        self._restore_button.setVisible(False)
        header_layout.addWidget(self._restore_button)
        document_tabs_widget = document_tabs or SLDDocumentTabs(parent=self)
        document_tabs_region = EditorRegionFrame("SLD Documents", parent=self)
        document_tabs_region.set_widget(document_tabs_widget)

        header_content = QWidget(header)
        header_content.setLayout(header_layout)
        header.set_widget(header_content)

        if tool_shelf is None and icon_provider is None:
            _LOG.warning(
                "SLD_TOOL_SHELF_WITHOUT_ICON_PROVIDER: fallback shelf will use readable "
                "glyphs; inject the composition-root ToolIconAdapter.icon_for provider "
                "to resolve canonical equipment symbols."
            )
        # This standalone fallback is presentation-only: without a supplied
        # canonical router or activation callback, ToolShelf intentionally
        # disables every tool button rather than creating its own lifecycle.
        # The application composition path supplies a routed shelf through
        # ControlSurfaceHost; keep this fallback useful for layout/previews,
        # not as an alternate activation entry point.
        shelf = tool_shelf or ToolShelf(
            definitions=contextual_tool_definitions(
                ("select", "wire", "bus", "line", "cable", "transformer", "breaker", "disconnector", "generator", "load", "motor"),
                editor_type="sld",
            ),
            editor_type="sld",
            icon_provider=icon_provider,
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
        left.setSizes([0, 220])

        center = QSplitter(Qt.Orientation.Vertical, self)
        center.setChildrenCollapsible(True)
        center.addWidget(settings_region)
        center.addWidget(canvas_region)
        center.setStretchFactor(0, 0)
        center.setStretchFactor(1, 1)
        center.setSizes([0, 600])

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
        # 44 px compact shelf + 8 px region margins + 8 px allowance.
        # Keep the canvas as the dominant region; only the tool column grows.
        body.setSizes([60, 900, 0])

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
        root.addWidget(document_tabs_region, 0)
        root.addWidget(body, 1)
        root.addWidget(diagnostics_region, 0)
        root.addWidget(status_region, 0)

        self.setObjectName("SLDEditor")
        self._region_widgets = {
            "header": header,
            "document_tabs": document_tabs_region,
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
        self._document_tabs = document_tabs_widget
        self._tool_settings = settings
        self._editor_context = None
        self._region_splitters = {
            "body": body,
            "left": left,
            "center": center,
            "sidebar": sidebar,
        }
        for frame in (
            header, document_tabs_region, shelf_region, settings_region, canvas_region,
            explorer_region, inspector_region, overlay_region,
            diagnostics_region, status_region,
        ):
            frame.set_title_visible(False)

        self._region_user_visibility: dict[str, bool] = {}
        self._region_user_overrides: set[str] = set()
        self._definition_visibility: dict[str, bool] = {}
        self._region_preferred_sizes: dict[str, int] = {}
        self._editor_definition_applied = False
        self._initial_sizes_pending = True
        # Nested splitters can receive their first usable geometry after the
        # parent editor's show/resize events. Observe their resize events so
        # pending initialization always gets another geometry-ready attempt.
        for splitter in self._region_splitters.values():
            splitter.installEventFilter(self)
        self._presentation_maximized = False
        self._maximize_callback = None

        # Defaults: only the engineering surface, compact tool shelf and status
        # remain permanently visible. Secondary regions are contextual.
        for region_id in ("explorer", "sidebar", "diagnostics", "tool_settings"):
            self.set_region_visible(region_id, False, user=False)

    def set_document_lifecycle(self, document_manager: object, *, activate, new_document, close_document) -> None:
        """Bind the tab strip to the canonical document lifecycle."""
        self._document_tabs.bind(document_manager, activate=activate, new_document=new_document, close_document=close_document)

    def refresh_document_tabs(self) -> None:
        self._document_tabs.refresh()

    def set_maximize_callback(self, callback) -> None:
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable or None.")
        self._maximize_callback = callback

    def region_widget(self, region_id: str) -> QWidget | None:
        return self._region_widgets.get(region_id)

    def apply_editor_definition(self, definition: object) -> None:
        preferred: dict[str, int] = {}
        first_application = not self._editor_definition_applied
        old_preferred = self._region_preferred_sizes.copy()
        affected: set[str] = {
            "tool_shelf", "explorer", "sidebar", "overlay", "tool_settings"
        } if first_application else set()

        for region in getattr(definition, "regions", ()) or ():
            region_id = getattr(region, "region_id", "")
            frame = self._region_widgets.get(region_id)
            visible = bool(getattr(region, "visible", True))
            previous_definition_visibility = self._definition_visibility.get(region_id)
            self._definition_visibility[region_id] = visible
            if region_id not in self._region_user_overrides:
                self._region_user_visibility[region_id] = visible
            if region_id in {"header", "canvas", "status"}:
                self._region_user_visibility[region_id] = True
            if frame is not None:
                effective_visible = self._region_user_visibility.get(region_id, visible)
                actual_visible = not frame.isHidden()
                if region_id not in {"header", "canvas", "status"}:
                    if actual_visible != (False if self._presentation_maximized else effective_visible):
                        affected.add(region_id)
                    frame.setVisible(
                        False if self._presentation_maximized else effective_visible
                    )
                minimum = int(getattr(region, "minimum_size", 0) or 0)
                if region_id in {"tool_shelf", "explorer", "sidebar"}:
                    frame.setMinimumWidth(minimum)
                elif region_id in {"header", "canvas", "tool_settings", "overlay", "diagnostics", "status"}:
                    frame.setMinimumHeight(minimum)
                if previous_definition_visibility is not None and previous_definition_visibility != visible:
                    affected.add(region_id)
            value = getattr(region, "preferred_size", None)
            if value is not None:
                preferred[region_id] = int(value)

        changed_preferred = {
            region_id for region_id, value in preferred.items()
            if old_preferred.get(region_id) != value
        }
        affected.update(changed_preferred)
        self._region_preferred_sizes = preferred
        self._editor_definition_applied = True
        # Initial realization initializes all splitters. Later definition changes
        # touch only the splitter paths whose visibility/preferred size changed.
        if affected:
            self._apply_splitter_sizes(
                {region_id: preferred[region_id] for region_id in changed_preferred if region_id in preferred},
                affected=affected,
                preferred_regions=changed_preferred | (affected if first_application else set()),
            )
            if self._initial_sizes_pending:
                self._initial_sizes_pending = not self._splitters_have_geometry()
        self._sync_panel_buttons()

    def _splitters_have_geometry(self) -> bool:
        # The outer body and the visible canvas/tool paths are required for the
        # initial layout. A hidden sidebar/overlay may legitimately have no
        # geometry and must not hold initialization pending forever.
        required = [self._region_splitters["body"], self._region_splitters["left"],
                    self._region_splitters["center"]]
        if (
            not self._region_widgets["sidebar"].isHidden()
            or not self._region_widgets["overlay"].isHidden()
        ):
            required.append(self._region_splitters["sidebar"])
        return all(splitter.width() > 0 and splitter.height() > 0 for splitter in required)

    def _realize_pending_initial_sizes(self) -> None:
        # Qt can deliver early widget events during construction, before the
        # initial-layout state is established.
        if not getattr(self, "_initial_sizes_pending", False):
            return
        if not self._splitters_have_geometry():
            return
        # Clear before setSizes(), since Qt may synchronously deliver resize
        # events while splitter geometry is being recalculated.
        self._initial_sizes_pending = False
        self._apply_splitter_sizes(self._region_preferred_sizes)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # The parent layout may assign usable geometry after showEvent.
        self._realize_pending_initial_sizes()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Retry only while initial realization is pending; never reset a user's
        # splitter positions after the first successful realization.
        self._realize_pending_initial_sizes()

    def eventFilter(self, watched, event) -> bool:
        if (
            getattr(self, "_initial_sizes_pending", False)
            and watched in getattr(self, "_region_splitters", {}).values()
            and event.type() == QEvent.Type.Resize
        ):
            self._realize_pending_initial_sizes()
        return super().eventFilter(watched, event)

    def _apply_splitter_sizes(
        self,
        preferred: dict[str, int] | None = None,
        *,
        affected: set[str] | None = None,
        preferred_regions: set[str] | None = None,
    ) -> None:
        preferred = preferred or {}
        preferred_regions = set(preferred) if preferred_regions is None else preferred_regions
        all_regions = {"tool_shelf", "explorer", "sidebar", "overlay", "tool_settings"}
        affected = all_regions if affected is None else affected
        body = self._region_splitters["body"]
        if body.width() > 0 and affected.intersection({"tool_shelf", "explorer", "sidebar", "overlay"}):
            current = body.sizes()
            left_column_visible = any(
                not self._region_widgets[region_id].isHidden()
                for region_id in ("tool_shelf", "explorer")
            )
            shelf_default = preferred.get(
                "tool_shelf", self._region_preferred_sizes.get("tool_shelf", 52)
            )
            explorer_default = preferred.get(
                "explorer", self._region_preferred_sizes.get("explorer", 220)
            )
            sidebar_default = preferred.get(
                "sidebar", self._region_preferred_sizes.get("sidebar", 280)
            )
            explorer_visible = not self._region_widgets["explorer"].isHidden()
            left_default = max(shelf_default, explorer_default) if explorer_visible else shelf_default
            # Use definition sizes for initial/changed definitions. Visibility
            # updates preserve live splitter proportions wherever possible.
            shelf = (
                left_default if preferred_regions.intersection({"tool_shelf", "explorer"})
                else current[0] if left_column_visible and len(current) > 0 and current[0] > 0
                else left_default if left_column_visible else 0
            )
            sidebar_visible = (
                not self._region_widgets["sidebar"].isHidden()
                or not self._region_widgets["overlay"].isHidden()
            )
            sidebar = (
                sidebar_default if preferred_regions.intersection({"sidebar", "overlay"})
                else current[2] if sidebar_visible and len(current) > 2 and current[2] > 0
                else sidebar_default if sidebar_visible else 0
            )
            handles = body.handleWidth() * max(0, body.count() - 1)
            available = max(1, body.width() - handles)
            center = max(1, available - shelf - sidebar)
            body.setSizes([shelf, center, sidebar])

        left = self._region_splitters["left"]
        if left.height() > 0 and "explorer" in affected:
            current = left.sizes()
            explorer_visible = not self._region_widgets["explorer"].isHidden()
            explorer_default = preferred.get(
                "explorer", self._region_preferred_sizes.get("explorer", 220)
            )
            explorer = (
                explorer_default if "explorer" in preferred_regions
                else current[0] if explorer_visible and len(current) > 0 and current[0] > 0
                else explorer_default if explorer_visible else 0
            )
            left.setSizes([explorer, max(1, left.height() - explorer - left.handleWidth())])

        center = self._region_splitters["center"]
        if center.height() > 0 and "tool_settings" in affected:
            current = center.sizes()
            settings_visible = not self._region_widgets["tool_settings"].isHidden()
            settings_default = preferred.get(
                "tool_settings", self._region_preferred_sizes.get("tool_settings", 42)
            )
            settings = (
                settings_default if "tool_settings" in preferred_regions
                else current[0] if settings_visible and len(current) > 0 and current[0] > 0
                else settings_default if settings_visible else 0
            )
            center.setSizes([settings, max(1, center.height() - settings - center.handleWidth())])

        sidebar_splitter = self._region_splitters["sidebar"]
        if sidebar_splitter.height() > 0 and affected.intersection({"sidebar", "overlay"}):
            current = sidebar_splitter.sizes()
            inspector_visible = not self._region_widgets["sidebar"].isHidden()
            overlay_visible = not self._region_widgets["overlay"].isHidden()
            overlay_default = preferred.get(
                "overlay", self._region_preferred_sizes.get("overlay", 120)
            )
            if "overlay" in preferred_regions:
                overlay_size = overlay_default if overlay_visible else 0
            elif overlay_visible and len(current) > 1 and current[1] > 0:
                overlay_size = current[1]
            else:
                overlay_size = overlay_default if overlay_visible else 0
            inspector_size = (
                current[0]
                if "sidebar" not in preferred_regions and inspector_visible and len(current) > 0 and current[0] > 0
                else max(1, sidebar_splitter.height() - overlay_size - sidebar_splitter.handleWidth())
                if inspector_visible else 0
            )
            sidebar_splitter.setSizes([inspector_size, overlay_size])

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
        if self._presentation_maximized:
            # Option 2: allow choices while maximized, but keep panels hidden.
            # Contextual automation cannot overwrite the user's pending restore state.
            if user:
                self._restore_visibility[region_id] = visible
            self._sync_panel_buttons()
            return
        was_visible = not frame.isHidden()
        frame.setVisible(visible)
        # Repeated contextual refreshes must not reset a deliberate splitter drag.
        if was_visible != visible:
            self._apply_splitter_sizes(affected={region_id})
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
            visible = (
                self._restore_visibility.get(region_id, False)
                if self._presentation_maximized
                else not self._region_widgets[region_id].isHidden()
            )
            button.blockSignals(True)
            button.setChecked(visible)
            button.blockSignals(False)

    def set_presentation_maximized(self, maximized: bool) -> None:
        maximized = bool(maximized)
        if self._presentation_maximized == maximized:
            return
        self._presentation_maximized = maximized
        if maximized:
            self._restore_visibility = {
                # isHidden() reports explicit visibility even when an ancestor
                # editor is temporarily inactive.
                rid: not self._region_widgets[rid].isHidden()
                for rid in ("explorer", "tool_shelf", "tool_settings", "sidebar", "overlay", "diagnostics")
            }
            for rid in ("explorer", "tool_shelf", "tool_settings", "sidebar", "overlay", "diagnostics"):
                self._region_widgets[rid].setVisible(False)
            self._restore_button.setVisible(True)
        else:
            for rid, visible in getattr(self, "_restore_visibility", {}).items():
                self._region_widgets[rid].setVisible(visible)
            self._restore_button.setVisible(False)
        changed_regions = set(getattr(self, "_restore_visibility", {}))
        self._apply_splitter_sizes(affected=changed_regions)
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
