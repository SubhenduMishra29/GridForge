from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from core.application import Application
from core.application.project import ProjectContext

from ui.sld.sld_document import SLDDocument

from .document import Document
from .project import Project
from .project_workspace import ProjectWorkspaceLifecycle, ProjectWorkspaceState
from .view_manager import ViewRecord


@dataclass(frozen=True, slots=True)
class ProjectWorkspaceChanged:
    """Immutable UI update emitted after a successful lifecycle transition."""

    operation: str
    state: ProjectWorkspaceState
    project_id: str


WorkspaceUpdateHandler = Callable[[ProjectWorkspaceChanged], None]


class ProjectWorkspaceApplicationAdapter:
    """Bridge Application lifecycle success into one UI workspace update path."""

    def __init__(self, application: Application, lifecycle: ProjectWorkspaceLifecycle) -> None:
        if not isinstance(application, Application):
            raise TypeError("application must be an Application.")
        if not isinstance(lifecycle, ProjectWorkspaceLifecycle):
            raise TypeError("lifecycle must be a ProjectWorkspaceLifecycle.")
        self._application = application
        self._lifecycle = lifecycle
        self._handlers: list[WorkspaceUpdateHandler] = []

    @property
    def application(self) -> Application:
        return self._application

    @property
    def lifecycle(self) -> ProjectWorkspaceLifecycle:
        return self._lifecycle

    @property
    def state(self) -> ProjectWorkspaceState:
        return self._lifecycle.state

    def subscribe(self, handler: WorkspaceUpdateHandler) -> None:
        if not callable(handler):
            raise TypeError("handler must be callable.")
        if handler not in self._handlers:
            self._handlers.append(handler)

    def unsubscribe(self, handler: WorkspaceUpdateHandler) -> None:
        try:
            self._handlers.remove(handler)
        except ValueError:
            return

    def new_project(
        self,
        name: str = "Untitled Project",
        *,
        project_id: str | None = None,
        document: Document | None = None,
    ) -> ProjectContext:
        context = self._application.new_project(name, project_id=project_id)
        if document is not None and document.project_id not in (None, context.project_id):
            raise ValueError("document belongs to a different project.")
        if document is None:
            document = self._new_sld_document(context)
        self._attach_presentation(document)
        state = self._lifecycle.new_project(
            self._to_ui_project(context),
            document=document,
        )
        state = self._ensure_sld_view(state)
        self._publish("new", state, context.project_id)
        return context

    def open_project(self, path: str) -> ProjectContext:
        context = self._application.open_project(path)
        presentation = self._application.presentation
        document = presentation if isinstance(presentation, Document) else None
        if document is None:
            document = self._new_sld_document(context)
        self._attach_presentation(document)
        state = self._lifecycle.open_project(
            self._to_ui_project(context),
            document=document,
        )
        state = self._ensure_sld_view(state)
        self._publish("open", state, context.project_id)
        return context

    def close_project(self) -> ProjectContext | None:
        context = self._application.close_project()
        if context is None:
            return None
        state = self._lifecycle.close_project()
        self._publish("close", state, context.project_id)
        return context

    def _attach_presentation(self, document: Document) -> None:
        serializer = getattr(document, "to_dict", None)
        deserializer = getattr(type(document), "from_dict", None)
        if not callable(serializer) or not callable(deserializer):
            raise TypeError("presentation document must provide to_dict() and from_dict().")
        self._application.configure_project_presentation(
            presentation=document,
            serializer=serializer,
            deserializer=deserializer,
        )

    @staticmethod
    def _new_sld_document(context: ProjectContext) -> SLDDocument:
        """Create the canonical SLD presentation document for a project."""
        return SLDDocument(
            document_id=f"{context.project_id}:sld",
            name=f"{context.name} SLD",
            project_id=context.project_id,
        )

    def _ensure_sld_view(self, state: ProjectWorkspaceState) -> ProjectWorkspaceState:
        document = state.document
        if document is None or document.document_type != "sld":
            return state
        if self._lifecycle.active_view is None:
            self._lifecycle.add_view(
                ViewRecord(
                    view_id=f"{document.document_id}:sld",
                    document_id=document.document_id,
                    view_type="sld",
                )
            )
        return self._lifecycle.state

    def _publish(self, operation: str, state: ProjectWorkspaceState, project_id: str) -> None:
        event = ProjectWorkspaceChanged(operation=operation, state=state, project_id=project_id)
        for handler in tuple(self._handlers):
            handler(event)

    @staticmethod
    def _to_ui_project(context: ProjectContext) -> Project:
        return Project(
            project_id=context.project_id,
            name=context.name,
            metadata={"path": str(context.path) if context.path is not None else None},
        )


__all__ = ["ProjectWorkspaceApplicationAdapter", "ProjectWorkspaceChanged", "WorkspaceUpdateHandler"]
