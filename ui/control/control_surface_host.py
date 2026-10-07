# ============================================================
# File: ui/control/control_surface_host.py
# GridForge V2 — Engineering Editor Host Compatibility Adapter
# Author: Subhendu Mishra
# ============================================================

"""Compatibility facade over the canonical Area → Editor → Region host."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ui.core.qt import QWidget, QVBoxLayout
from ui.core.action_router import UIActionRouter
from ui.editors.common.editor_host import EngineeringEditorHost
from ui.editors.common.tool_shelf import ToolShelf
from ui.tools.tool_definition import ToolDefinition
from ui.tools.tool_mode import ToolMode
from ui.tools.tool_settings import ToolSettings
from ui.editors.control.control_editor import ControlEditor
from ui.editors.protection.protection_editor import ProtectionEditor
from ui.editors.sld.sld_editor import SLDEditor
from ui.editors.study.study_editor import StudyEditor
from ui.workspace.engineering_workspace_tabs import MapWorkspaceView, ReportsWorkspaceView, TopologyWorkspaceView


class ControlSurfaceHost(QWidget):
    """Compatibility facade whose actual composition is the canonical editor host."""

    def __init__(
        self,
        *,
        surfaces: Mapping[str, QWidget],
        application: Any | None = None,
        tool_definitions: tuple[ToolDefinition, ...] = (),
        tool_activator: Any | None = None,
        action_router: UIActionRouter | None = None,
        tool_activators: Mapping[str, Any] | None = None,
        tool_active_providers: Mapping[str, Any] | None = None,
        icon_provider: Any | None = None,
        study_runtime: Any | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if not surfaces:
            raise ValueError("At least one workspace surface is required.")
        if application is None:
            raise ValueError("application is required.")
        normalized = dict(surfaces)
        if any(not isinstance(key, str) or not key.strip() for key in normalized):
            raise TypeError("Workspace surface IDs must be non-empty strings.")
        if any(not isinstance(widget, QWidget) for widget in normalized.values()):
            raise TypeError("All workspace surfaces must be QWidget instances.")
        if any(not isinstance(item, ToolDefinition) for item in tool_definitions):
            raise TypeError("tool_definitions must contain ToolDefinition objects.")

        activators = dict(tool_activators or {})
        if tool_activator is not None:
            activators.setdefault("sld", tool_activator)
        providers = dict(tool_active_providers or {})
        self._application = application
        self._host = EngineeringEditorHost(parent=self)
        self._shelves: dict[str, ToolShelf] = {}
        self._sld_document: Any | None = None

        def make_tool_shelf(editor_type: str, parent: QWidget) -> ToolShelf:
            shelf = ToolShelf(
                definitions=tool_definitions,
                activate=activators.get(editor_type),
                action_router=action_router,
                editor_type=editor_type,
                icon_provider=icon_provider,
                active_tool_provider=providers.get(editor_type),
                parent=parent,
            )
            self._shelves[editor_type] = shelf
            return shelf

        if "sld" in normalized:
            self._host.register_editor(
                "sld-editor",
                SLDEditor(
                    canvas=normalized["sld"],
                    tool_shelf=make_tool_shelf("sld", self._host),
                    parent=self._host,
                ),
            )
        if "control" in normalized:
            self._host.register_editor(
                "control-editor",
                ControlEditor(
                    surface=normalized["control"],
                    tool_shelf=make_tool_shelf("control", self._host),
                    parent=self._host,
                ),
            )
        if "protection" in normalized:
            self._host.register_editor(
                "protection-editor",
                ProtectionEditor(
                    surface=normalized["protection"],
                    tool_shelf=make_tool_shelf("protection", self._host),
                    parent=self._host,
                ),
            )

        study_surface = ReportsWorkspaceView(application, parent=self._host)
        self._host.register_editor(
            "study-editor",
            StudyEditor(
                surface=study_surface,
                tool_shelf=make_tool_shelf("study", self._host),
                parent=self._host,
            ),
        )

        # Secondary historical views remain compatibility-only aliases; they
        # do not define WorkspaceDefinition/EditorDefinition policy.
        self._host.register_editor("topology", TopologyWorkspaceView(application, parent=self._host))
        self._host.register_editor("map", MapWorkspaceView(parent=self._host))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._host)

    @property
    def surface_ids(self) -> tuple[str, ...]:
        return self._host.editor_ids

    @property
    def editor_host(self) -> EngineeringEditorHost:
        return self._host

    def set_action_router(self, router: UIActionRouter | None) -> None:
        if router is not None and not isinstance(router, UIActionRouter):
            raise TypeError("router must be a UIActionRouter or None.")
        for shelf in self._shelves.values():
            shelf.set_action_router(router)

    def active_tool_id_for(self, editor_type: str) -> str | None:
        provider = getattr(self._shelves.get(editor_type), "_active_tool_provider", None)
        return provider() if callable(provider) else None

    def tool_definition_for(self, editor_type: str, tool_id: str | None) -> ToolDefinition | None:
        if tool_id is None:
            return None
        shelf = self._shelves.get(editor_type)
        if shelf is None:
            return None
        return next((item for item in shelf.definitions if item.tool_id == tool_id), None)

    def activate(
        self,
        surface_id: str,
        *,
        area: Any | None = None,
        region_id: str | None = None,
        context: Any | None = None,
    ) -> None:
        aliases = {
            "sld": "sld-editor",
            "control": "control-editor",
            "protection": "protection-editor",
            "study": "study-editor",
            "reports": "study-editor",
        }
        canonical_id = aliases.get(surface_id, surface_id)
        self._host.activate(canonical_id, area=area, region_id=region_id, context=context)
        if canonical_id == "topology":
            widget = self._host.widget("topology")
            if isinstance(widget, TopologyWorkspaceView):
                widget.refresh()
        elif canonical_id == "study-editor":
            editor = self._host.widget("study-editor")
            if editor is not None:
                reports = editor.findChild(ReportsWorkspaceView)
                if reports is not None:
                    reports.refresh()
        elif canonical_id == "map":
            widget = self._host.widget("map")
            if isinstance(widget, MapWorkspaceView):
                widget.set_document(self._sld_document)

    def set_editor_context(self, context: object | None) -> None:
        self._host.set_editor_context(context)

    def refresh_selection_context(self, selected_ids: object) -> None:
        context = self._host.editor_context
        if context is None:
            return
        values = tuple(str(value) for value in (selected_ids or ()))
        engineering = context.engineering.with_updates(selected_ids=values)
        self._host.set_editor_context(
            context.with_updates(
                selection_context={"selected_ids": values},
                engineering=engineering,
            )
        )

    def refresh_tool_shelves(self) -> None:
        for shelf in self._shelves.values():
            shelf.refresh_runtime_state()
        context = self._host.editor_context
        editor = getattr(context, "editor", None) if context is not None else None
        if context is None or editor is None:
            return
        editor_type = str(getattr(editor, "editor_type", ""))
        active_tool = self.active_tool_id_for(editor_type)
        definition = self.tool_definition_for(editor_type, active_tool)
        mode = ToolMode.IDLE
        settings = None
        if definition is not None:
            if definition.default_mode:
                try:
                    mode = ToolMode(definition.default_mode)
                except ValueError:
                    mode = ToolMode.IDLE
            settings = ToolSettings(definition.tool_id, values=definition.settings)
        engineering = getattr(context, "engineering", None)
        if engineering is not None:
            engineering = engineering.with_updates(active_tool=active_tool)
        self._host.set_editor_context(
            context.with_updates(
                active_tool=active_tool,
                tool_mode=mode,
                tool_settings=settings,
                engineering=engineering,
            )
        )

    def set_region_widgets(
        self,
        editor_type: str,
        *,
        explorer: QWidget | None = None,
        inspector: QWidget | None = None,
        diagnostics: QWidget | None = None,
        status: QWidget | None = None,
        tool_settings: QWidget | None = None,
    ) -> None:
        editor_id = {
            "sld": "sld-editor",
            "control": "control-editor",
            "protection": "protection-editor",
            "study": "study-editor",
        }.get(editor_type, editor_type)
        editor = self._host.widget(editor_id)
        if editor is None:
            raise KeyError(f"Unknown editor type: {editor_type!r}")
        widgets = {
            "explorer": explorer,
            "sidebar": inspector,
            "diagnostics": diagnostics,
            "status": status,
            "tool_settings": tool_settings,
        }
        for region_id, widget in widgets.items():
            if widget is None:
                continue
            region = getattr(editor, "region_widget", lambda _id: None)(region_id)
            if region is None:
                raise KeyError(f"Editor {editor_id!r} does not realize Region {region_id!r}.")
            region.set_widget(widget)
        if tool_settings is not None:
            # The settings widget is also used by EditorContext propagation.
            setattr(editor, "_tool_settings", tool_settings)

    def set_sld_document(self, document: Any | None) -> None:
        self._sld_document = document
        map_widget = self._host.widget("map")
        if isinstance(map_widget, MapWorkspaceView):
            map_widget.set_document(document)


__all__ = ["ControlSurfaceHost"]
