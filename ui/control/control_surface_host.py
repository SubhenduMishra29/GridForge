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

from ui.core.qt import QLabel, QWidget
from ui.editors.common.editor_host import EngineeringEditorHost
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

        self._application = application
        self._host = EngineeringEditorHost(parent=self)
        self._sld_document: Any | None = None

        if "sld" in normalized:
            self._host.register_editor(
                "sld",
                SLDEditor(canvas=normalized["sld"], parent=self._host),
            )
        if "control" in normalized:
            self._host.register_editor(
                "control",
                ControlEditor(surface=normalized["control"], parent=self._host),
            )
        if "protection" in normalized:
            self._host.register_editor(
                "protection",
                ProtectionEditor(surface=normalized["protection"], parent=self._host),
            )

        # Study/secondary surfaces are read-oriented editors. They do not
        # create a second study/result authority.
        self._host.register_editor(
            "topology",
            TopologyWorkspaceView(application, parent=self._host),
        )
        self._host.register_editor(
            "map",
            QLabel("SLD geometry map", self._host),
        )
        self._host.register_editor(
            "reports",
            StudyEditor(surface=ReportsWorkspaceView(application, parent=self._host), parent=self._host),
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
            if isinstance(widget, QLabel):
                document = self._sld_document
                widget.setText("SLD geometry map" if document is None else "SLD geometry map — active document loaded")

    def set_sld_document(self, document: Any | None) -> None:
        self._sld_document = document
        map_widget = self._host.widget("map")
        if isinstance(map_widget, QLabel):
            map_widget.setText("SLD geometry map" if document is None else "SLD geometry map — active document loaded")


__all__ = ["ControlSurfaceHost"]
