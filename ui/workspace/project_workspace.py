# ============================================================
# GridForge V2 — Project Workspace Lifecycle
# Author: Subhendu Mishra
# ============================================================
"""UI-only lifecycle boundary between project identity and workspace state.

This coordinator deliberately owns presentation lifecycle only. Core
engineering state remains owned by the Application/Core lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .document import Document
from .project import Project
from .workspace_controller import WorkspaceController


@dataclass(frozen=True, slots=True)
class ProjectWorkspaceState:
    """Immutable snapshot of the active presentation lifecycle."""

    project: Project | None
    document: Document | None
    workspace_id: str | None


class ProjectWorkspaceLifecycle:
    """Coordinate UI project/document/workspace transitions."""

    def __init__(self, workspace_controller: WorkspaceController) -> None:
        if not isinstance(workspace_controller, WorkspaceController):
            raise TypeError("workspace_controller must be a WorkspaceController.")
        self._workspace_controller = workspace_controller
        self._project: Project | None = None
        self._document: Document | None = None

    @property
    def project(self) -> Project | None:
        return self._project

    @property
    def document(self) -> Document | None:
        return self._document

    @property
    def workspace_controller(self) -> WorkspaceController:
        return self._workspace_controller

    @property
    def state(self) -> ProjectWorkspaceState:
        return ProjectWorkspaceState(
            project=self._project,
            document=self._document,
            workspace_id=self._workspace_controller.active_workspace_id,
        )

    def new_project(
        self,
        project: Project,
        *,
        document_type: str = "sld",
        document_name: str = "Untitled",
        workspace_id: str | None = None,
    ) -> ProjectWorkspaceState:
        if not isinstance(project, Project):
            raise TypeError("project must be a Project.")
        if not document_type or not document_name:
            raise ValueError("document_type and document_name must not be empty.")

        self._clear_active_presentation()
        self._project = project
        self._document = Document(
            document_id=str(uuid4()),
            project_id=project.project_id,
            document_type=document_type,
            name=document_name,
        )
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
        self._document = document
        self._activate_workspace(workspace_id)
        return self.state

    def close_project(self) -> ProjectWorkspaceState:
        self._clear_active_presentation()
        return self.state

    def close_document(self) -> ProjectWorkspaceState:
        self._document = None
        return self.state

    def activate_document(self, document: Document) -> ProjectWorkspaceState:
        if not isinstance(document, Document):
            raise TypeError("document must be a Document.")
        if self._project is None:
            raise RuntimeError("Cannot activate a document without an active project.")
        if document.project_id not in (None, self._project.project_id):
            raise ValueError("document belongs to a different project.")
        self._document = document
        return self.state

    def _activate_workspace(self, workspace_id: str | None) -> None:
        if workspace_id is None:
            self._workspace_controller.activate_default()
        else:
            self._workspace_controller.activate(workspace_id)

    def _clear_active_presentation(self) -> None:
        self._document = None
        self._workspace_controller.deactivate()


__all__ = ["ProjectWorkspaceLifecycle", "ProjectWorkspaceState"]
