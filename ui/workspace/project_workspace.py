# ============================================================
# GridForge V2 — Project Workspace Lifecycle
# Author: Subhendu Mishra
# ============================================================
"""UI-only lifecycle boundary between project identity and workspace state."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .document import Document
from .document_manager import DocumentManager
from .project import Project
from .view_manager import ViewManager, ViewRecord
from .workspace_controller import WorkspaceController
from .workspace_layout import WorkspaceLayout


@dataclass(frozen=True, slots=True)
class ProjectWorkspaceState:
    project: Project | None
    document: Document | None
    workspace_id: str | None
    view_id: str | None


@dataclass(frozen=True, slots=True)
class _WorkspaceTransitionSnapshot:
    project: Project | None
    documents: tuple[Document, ...]
    active_document_id: str | None
    views: tuple[ViewRecord, ...]
    active_view_id: str | None
    workspace_id: str | None
    workspace_state: object | None
    realized_layout: WorkspaceLayout | None


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
    def project(self) -> Project | None: return self._project
    @property
    def document(self) -> Document | None: return self._documents.active_document
    @property
    def active_view(self) -> ViewRecord | None: return self._views.active_view
    @property
    def documents(self) -> DocumentManager: return self._documents
    @property
    def views(self) -> ViewManager: return self._views
    @property
    def workspace_controller(self) -> WorkspaceController: return self._workspace_controller
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
        activate_workspace: bool = True,
    ) -> ProjectWorkspaceState:
        if not isinstance(project, Project): raise TypeError("project must be a Project.")
        if document is not None and not isinstance(document, Document): raise TypeError("document must be a Document or None.")
        if not document_type or not document_name: raise ValueError("document_type and document_name must not be empty.")
        if document is not None and document.project_id not in (None, project.project_id): raise ValueError("document belongs to a different project.")
        snapshot = self._capture_transition_snapshot()
        try:
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
            if activate_workspace:
                self._activate_workspace(workspace_id)
            return self.state
        except BaseException:
            self._restore_transition_snapshot(snapshot)
            raise

    def open_project(
        self,
        project: Project,
        *,
        document: Document | None = None,
        workspace_id: str | None = None,
        activate_workspace: bool = True,
    ) -> ProjectWorkspaceState:
        if not isinstance(project, Project): raise TypeError("project must be a Project.")
        if document is not None and not isinstance(document, Document): raise TypeError("document must be a Document or None.")
        if document is not None and document.project_id not in (None, project.project_id): raise ValueError("document belongs to a different project.")
        snapshot = self._capture_transition_snapshot()
        try:
            self._clear_active_presentation()
            self._project = project
            if document is not None:
                self._documents.register(document)
            if activate_workspace:
                self._activate_workspace(workspace_id)
            return self.state
        except BaseException:
            self._restore_transition_snapshot(snapshot)
            raise

    def close_project(self) -> ProjectWorkspaceState:
        snapshot = self._capture_transition_snapshot()
        try:
            self._clear_active_presentation()
            return self.state
        except BaseException:
            self._restore_transition_snapshot(snapshot)
            raise

    def close_document(self) -> ProjectWorkspaceState:
        document = self._documents.active_document
        if document is not None: self.remove_document(document.document_id)
        return self.state

    def activate_document(self, document: Document) -> ProjectWorkspaceState:
        if not isinstance(document, Document): raise TypeError("document must be a Document.")
        if self._project is None: raise RuntimeError("Cannot activate a document without an active project.")
        if document.project_id not in (None, self._project.project_id): raise ValueError("document belongs to a different project.")
        existing = self._documents.get(document.document_id)
        if existing is None: self._documents.register(document)
        else: self._documents.activate(document.document_id)
        return self.state

    def replace_document(self, document: Document) -> ProjectWorkspaceState:
        if not isinstance(document, Document): raise TypeError("document must be a Document.")
        if self._project is None: raise RuntimeError("Cannot replace a document without an active project.")
        if document.project_id not in (None, self._project.project_id): raise ValueError("document belongs to a different project.")
        active = self._documents.active_document
        if active is not None: self.remove_document(active.document_id)
        self._documents.register(document)
        return self.state

    def add_view(self, view: ViewRecord) -> ProjectWorkspaceState:
        if not isinstance(view, ViewRecord): raise TypeError("view must be a ViewRecord.")
        if self._documents.get(view.document_id) is None: raise KeyError(f"Document does not exist: {view.document_id}")
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

    def _capture_transition_snapshot(self) -> _WorkspaceTransitionSnapshot:
        return _WorkspaceTransitionSnapshot(
            project=self._project,
            documents=tuple(self._documents.documents()),
            active_document_id=self._documents.active_document_id,
            views=tuple(self._views.views()),
            active_view_id=self._views.active_view_id,
            workspace_id=self._workspace_controller.active_workspace_id,
            workspace_state=self._workspace_controller.state,
            realized_layout=self._workspace_controller.realized_layout,
        )

    def _restore_transition_snapshot(self, snapshot: _WorkspaceTransitionSnapshot) -> None:
        """Restore the exact previous logical presentation before the transition committed."""
        restore_error: BaseException | None = None
        try:
            self._workspace_controller.deactivate()
        except BaseException as exc:
            restore_error = exc

        if restore_error is not None:
            raise RuntimeError("Workspace rollback could not clear the failed realization.") from restore_error

        self._documents.clear()
        self._views.clear()
        self._project = snapshot.project

        for document in snapshot.documents:
            self._documents.register(document)
        if snapshot.active_document_id is not None:
            self._documents.activate(snapshot.active_document_id)

        for view in snapshot.views:
            self._views.register(view)
        if snapshot.active_view_id is not None:
            self._views.activate(snapshot.active_view_id)

        if snapshot.workspace_id is not None:
            restored = self._workspace_controller.activate(snapshot.workspace_id)
            if snapshot.workspace_state is not None and restored != snapshot.workspace_state:
                self._workspace_controller.apply_layout(snapshot.workspace_state.layout)
        elif snapshot.realized_layout is not None:
            raise RuntimeError("Workspace snapshot is internally inconsistent: realized layout without active workspace.")

    def restore_last_state(self, snapshot: _WorkspaceTransitionSnapshot) -> None:
        """Public Application-facing rollback primitive for coordinated transitions."""
        if not isinstance(snapshot, _WorkspaceTransitionSnapshot):
            raise TypeError("snapshot must be a workspace transition snapshot.")
        self._restore_transition_snapshot(snapshot)

    def capture_transition_state(self) -> object:
        """Capture presentation state for the Application lifecycle transaction."""
        return self._capture_transition_snapshot()

    def activate_project_transition(
        self,
        project: Project,
        *,
        document: Document,
        workspace_id: str | None = None,
        activate_workspace: bool = True,
        open_existing: bool = False,
    ) -> object:
        """Install a project presentation and return a rollback callback."""
        snapshot = self._capture_transition_snapshot()
        try:
            if open_existing:
                state = self.open_project(
                    project,
                    document=document,
                    workspace_id=workspace_id,
                    activate_workspace=activate_workspace,
                )
            else:
                state = self.new_project(
                    project,
                    document=document,
                    workspace_id=workspace_id,
                    activate_workspace=activate_workspace,
                )
            if state.document is not None and state.document.document_type == "sld" and self.active_view is None:
                self.add_view(
                    ViewRecord(
                        view_id=f"{state.document.document_id}:sld",
                        document_id=state.document.document_id,
                        view_type="sld",
                    )
                )
            return lambda: self._restore_transition_snapshot(snapshot)
        except BaseException:
            self._restore_transition_snapshot(snapshot)
            raise


__all__ = ["ProjectWorkspaceLifecycle", "ProjectWorkspaceState"]
