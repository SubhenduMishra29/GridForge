"""Presentation-only host for GridForge engineering workspace surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ui.core.qt import QVBoxLayout, QWidget
from ui.workspace.engineering_workspace_tabs import EngineeringWorkspaceTabs


class ControlSurfaceHost(QWidget):
    """Host shared project-state engineering surfaces in one tabbed presentation."""

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
        normalized = dict(surfaces)
        if any(not isinstance(key, str) or not key.strip() for key in normalized):
            raise TypeError("Workspace surface IDs must be non-empty strings.")
        if any(not isinstance(widget, QWidget) for widget in normalized.values()):
            raise TypeError("All workspace surfaces must be QWidget instances.")
        if application is None:
            raise ValueError("application is required for shared read-model workspace projections.")
        self._surfaces = normalized
        self._tabs = EngineeringWorkspaceTabs(
            application=application,
            surfaces=normalized,
            parent=self,
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)

    @property
    def surface_ids(self) -> tuple[str, ...]:
        return self._tabs.surface_ids

    def activate(self, surface_id: str) -> None:
        self._tabs.activate(surface_id)

    def set_sld_document(self, document: Any | None) -> None:
        self._tabs.set_sld_document(document)


__all__ = ["ControlSurfaceHost"]
