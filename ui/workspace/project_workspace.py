# ============================================================
# GridForge V2 — Project Workspace Lifecycle
# Author: Subhendu Mishra
# ============================================================
"""UI-only lifecycle boundary between project identity and workspace state.

ProjectWorkspaceLifecycle is the canonical presentation composition boundary
for Project -> Document -> View -> Workspace state. Core engineering state
remains owned by the Application/Core lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .document import Document
from .document_manager import DocumentManager
from .project import Project
from .view_manager import ViewManager, ViewRecord
from .workspace_controller import WorkspaceController


@dataclass(frozen=True, slots=True)
class ProjectWorkspaceState:
    """Immutable snapshot of the active presentation lifecycle."""

    project: Project | None
    document: Document | None
    workspace_id: str | None
    view_id: str | None


class ProjectWorkspaceLifecycle:
    """Coordinate canonical UI project/document/view/workspace transitions."""

    def __init__(self, workspace_controller: WorkspaceController) -> None:
        if not isinstance(workspace_controller, WorkspaceController):
            raise TypeError("workspace_controller must be a WorkspaceController.")
        self._workspace_controller = workspace_controller
        self._documents = DocumentManager()
        self._views = ViewManager()
        self._project: Project | None = None

    @property
    def project(self) -> Project | None:
        return self._project

    @property
    def document(self) -> Document | None:
        return self._documents.active_document

    @property
    def active_view(self) -> ViewRecord | None:
        return self._views.active_view

    @property
    def documents(self) -> DocumentManager:
        return self._documents

    @property
    def views(self) -> ViewManager:
        return self._views

    @property
    def workspace_controller(self) -> WorkspaceController:
        return self._workspace_controller

    @property
    def state(self) -> ProjectWorkspaceState:
        document = self._documents.active_document
        view = self._views.active_view
        return ProjectWorkspaceState(
            project=self._project,
            document=document,
            workspace_id=self._workspace_controller.active_workspace_id,
            view_id=view.view_id if view is not None else None,
        )

    def new_project(
        self,
        project: Project,
        *,
        document: Document | None = None,
        document_type: str = "sld",
        document_name: str = "Untitled",
        workspace_id: str | None = None,
    ) -> ProjectWorkspaceState:
        if not isinstance(project, Project):
            raise TypeError("project must be a Project.")
        if document is not None and not isinstance(document, Document):
            raise TypeError("document must be a Document or None.")
        if not document_type or not document_name:
            raise ValueError("document_type and document_name must not be empty.")
        if document is not None and document.project_id not in (None, project.project_id):
            raise ValueError("document belongs to a different project.")

        self._clear_active_presentation()
        self._project = project
        if document is None:
            document = Document(
                document_id=str(uuid4()),
                project_id=project.project_id,
                document_type=document_type,
                name=document_name,
            )
        self._documents.register(document)
        self._activate_workspace(workspace_id)
        return self.state

    def open_project(
        self,
        project: Project,
        *,
        document: Document | None = None,
        workspace_id: str | None = None,
    ) -> ProjectWorkspaceState:
        if not isinstance(project, Project):
            raise TypeError("project must be a Project.")
        if document is not None and not isinstance(document, Document):
            raise TypeError("document must be a Document or None.")
        if document is not None and document.project_id not in (None, project.project_id):
            raise ValueError("document belongs to a different project.")

        self._clear_active_presentation()
        self._project = project
        if document is not None:
            self._documents.register(document)
        self._activate_workspace(workspace_id)
        return self.state

    def close_project(self) -> ProjectWorkspaceState:
        self._clear_active_presentation()
        return self.state

    def close_document(self) -> ProjectWorkspaceState:
        document = self._documents.active_document
        if document is not None:
            self.remove_document(document.document_id)
        return self.state

    def activate_document(self, document: Document) -> ProjectWorkspaceState:
        if not isinstance(document, Document):
            raise TypeError("document must be a Document.")
        if self._project is None:
            raise RuntimeError("Cannot activate a document without an active project.")
        if document.project_id not in (None, self._project.project_id):
            raise ValueError("document belongs to a different project.")
        existing = self._documents.get(document.document_id)
        if existing is None:
            self._documents.register(document)
        else:
            self._documents.activate(document.document_id)
        return self.state

    def replace_document(self, document: Document) -> ProjectWorkspaceState:
        if not isinstance(document, Document):
            raise TypeError("document must be a Document.")
        if self._project is None:
            raise RuntimeError("Cannot replace a document without an active project.")
        if document.project_id not in (None, self._project.project_id):
            raise ValueError("document belongs to a different project.")
        active = self._documents.active_document
        if active is not None:
            self.remove_document(active.document_id)
        self._documents.register(document)
        return self.state

    def add_view(self, view: ViewRecord) -> ProjectWorkspaceState:
        if not isinstance(view, ViewRecord):
            raise TypeError("view must be a ViewRecord.")
        if self._documents.get(view.document_id) is None:
            raise KeyError(f"Document does not exist: {view.document_id}")
        self._views.register(view)
        return self.state

    def remove_document(self, document_id: str) -> Document:
        for view in self._views.views_for_document(document_id):
            self._views.unregister(view.view_id)
        return self._documents.unregister(document_id)

    def _activate_workspace(self, workspace_id: str | None) -> None:
        if workspace_id is None:
            self._workspace_controller.activate_default()
        else:
            self._workspace_controller.activate(workspace_id)

    def _clear_active_presentation(self) -> None:
        self._views.clear()
        self._documents.clear()
        self._workspace_controller.deactivate()
        self._project = None


__all__ = ["ProjectWorkspaceLifecycle", "ProjectWorkspaceState"]
