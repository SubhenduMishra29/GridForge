# ============================================================
# File: ui/control/control_surface_host.py
# GridForge V2 — Engineering Editor Host Compatibility Adapter
# Author: Subhendu Mishra
# ============================================================

"""Canonical Area/Editor composition host for engineering surfaces.

The historical class name is retained as a compatibility adapter for
existing bootstrap/action-router callers. The implementation is no longer
tab-based: each surface is an Editor registered in the shared
EngineeringEditorHost. Domain truth and command routing remain unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ui.core.qt import QWidget
from ui.editors.common.editor_host import EngineeringEditorHost
from ui.editors.common.tool_shelf import ToolShelf
from ui.tools.tool_definition import ToolDefinition
from ui.editors.control.control_editor import ControlEditor
from ui.editors.protection.protection_editor import ProtectionEditor
from ui.editors.sld.sld_editor import SLDEditor
from ui.editors.study.study_editor import StudyEditor
from ui.workspace.engineering_workspace_tabs import MapWorkspaceView, ReportsWorkspaceView, TopologyWorkspaceView


class ControlSurfaceHost(QWidget):
    """Compatibility facade over the canonical Area → Editor host."""

    def __init__(
        self,
        *,
        surfaces: Mapping[str, QWidget],
        application: Any | None = None,
        tool_definitions: tuple[ToolDefinition, ...] = (),
        tool_activator: Any | None = None,
        tool_activators: Mapping[str, Any] | None = None,
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
        def make_tool_shelf(parent: QWidget, editor_type: str) -> ToolShelf:
            return ToolShelf(definitions=tool_definitions, activate=activators.get(editor_type), editor_type=editor_type, parent=parent)

        self._application = application
        self._host = EngineeringEditorHost(parent=self)
        self._sld_document: Any | None = None

        if "sld" in normalized:
            self._host.register_editor(
                "sld",
                SLDEditor(canvas=normalized["sld"], tool_shelf=make_tool_shelf(self._host, "sld"), parent=self._host),
            )
        if "control" in normalized:
            self._host.register_editor(
                "control",
                ControlEditor(surface=normalized["control"], tool_shelf=make_tool_shelf(self._host, "control"), parent=self._host),
            )
        if "protection" in normalized:
            self._host.register_editor(
                "protection",
                ProtectionEditor(surface=normalized["protection"], tool_shelf=make_tool_shelf(self._host, "protection"), parent=self._host),
            )

        # Study/secondary surfaces are read-oriented editors. They do not
        # create a second study/result authority.
        self._host.register_editor(
            "topology",
            TopologyWorkspaceView(application, parent=self._host),
        )
        self._host.register_editor(
            "map",
            MapWorkspaceView(parent=self._host),
        )
        self._host.register_editor(
            "reports",
            StudyEditor(surface=ReportsWorkspaceView(application, parent=self._host), tool_shelf=make_tool_shelf(self._host, "study"), parent=self._host),
        )

        from ui.core.qt import QVBoxLayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._host)

    @property
    def surface_ids(self) -> tuple[str, ...]:
        return self._host.editor_ids

    def activate(self, surface_id: str) -> None:
        self._host.activate(surface_id)
        if surface_id == "topology":
            widget = self._host.widget("topology")
            if isinstance(widget, TopologyWorkspaceView):
                widget.refresh()
        elif surface_id == "reports":
            editor = self._host.widget("reports")
            if editor is not None:
                # ReportsWorkspaceView is owned by the StudyEditor region.
                reports = editor.findChild(ReportsWorkspaceView)
                if reports is not None:
                    reports.refresh()
        elif surface_id == "map":
            widget = self._host.widget("map")
            if isinstance(widget, MapWorkspaceView):
                document = self._sld_document
                widget.set_document(document)

    def set_sld_document(self, document: Any | None) -> None:
        self._sld_document = document
        map_widget = self._host.widget("map")
        if isinstance(map_widget, MapWorkspaceView):
            map_widget.setText("SLD geometry map" if document is None else "SLD geometry map — active document loaded")


__all__ = ["ControlSurfaceHost"]
