# ============================================================
# GridForge V2 — Project Hierarchy Projection
# ============================================================
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from core.application.events import ProjectClosed, ProjectLoaded


class ProjectHierarchyProjection:
    """Project Application workspace state into the Project Explorer panel."""

    event_types = (ProjectLoaded, ProjectClosed)

    def __init__(self, *, adapter, panel, application=None) -> None:
        if adapter is None or not callable(getattr(adapter, "subscribe", None)):
            raise TypeError("adapter must provide subscribe().")
        if not callable(getattr(adapter, "unsubscribe", None)):
            raise TypeError("adapter must provide unsubscribe().")
        if panel is None or not callable(getattr(panel, "set_hierarchy", None)):
            raise TypeError("panel must provide set_hierarchy().")
        self._adapter = adapter
        self._panel = panel
        self._application = application
        self._disposed = False
        adapter.subscribe(self._on_workspace_changed)
        self.refresh_from_state()

    def refresh(self, event) -> None:
        if self._disposed:
            return
        if isinstance(event, ProjectClosed):
            self._panel.clear_hierarchy()
        else:
            self.refresh_from_state()

    def refresh_from_state(self) -> None:
        if self._disposed:
            return
        self._panel.set_hierarchy(self._hierarchy(self._adapter.state))

    def _on_workspace_changed(self, change) -> None:
        if not self._disposed:
            self._panel.set_hierarchy(self._hierarchy(change.state))

    def _hierarchy(self, state):
        project = getattr(state, "project", None)
        document = getattr(state, "document", None)
        if project is None:
            return None
        documents = () if document is None else ({
            "id": str(document.document_id),
            "name": str(document.name),
            "type": str(document.document_type),
        },)
        network_elements = ()
        if self._application is not None and callable(getattr(self._application, "read_network", None)):
            try:
                network = self._application.read_network()
                network_elements = tuple({
                    "id": str(element.object_id),
                    "name": str(element.labels.get("name") or element.object_id),
                    "type": str(element.element_type),
                } for element in network.elements)
            except RuntimeError:
                network_elements = ()
        return {
            "project": {
                "id": str(project.project_id),
                "name": str(project.name),
                "documents": documents,
            },
            "workspace_id": state.workspace_id,
            "view_id": state.view_id,
            "network_elements": network_elements,
        }

    def dispose(self) -> None:
        if self._disposed:
            return
        self._adapter.unsubscribe(self._on_workspace_changed)
        self._panel.clear_hierarchy()
        self._disposed = True


__all__ = ["ProjectHierarchyProjection"]
