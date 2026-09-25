# ============================================================
# File: ui/workspace/project_workspace_adapter.py
# GridForge V2 — Project Workspace Application Adapter
# ============================================================

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from core.application import Application
from core.application.project import ProjectContext
from core.application.project_transition import ProjectTransitionDecision
from ui.sld.sld_document import SLDDocument
from .document import Document
from .project import Project
from .project_workspace import ProjectWorkspaceLifecycle, ProjectWorkspaceState


@dataclass(frozen=True, slots=True)
class ProjectWorkspaceChanged:
    """Immutable UI update emitted after a successful engineer-visible transition."""

    operation: str
    state: ProjectWorkspaceState
    project_id: str


WorkspaceUpdateHandler = Callable[[ProjectWorkspaceChanged], None]


class ProjectWorkspaceApplicationAdapter:
    """Bridge Application lifecycle success into the coordinated UI workspace transaction."""

    def __init__(self, application: Application, lifecycle: ProjectWorkspaceLifecycle) -> None:
        if not isinstance(application, Application): raise TypeError("application must be an Application.")
        if not isinstance(lifecycle, ProjectWorkspaceLifecycle): raise TypeError("lifecycle must be a ProjectWorkspaceLifecycle.")
        self._application = application
        self._lifecycle = lifecycle
        self._handlers: list[WorkspaceUpdateHandler] = []

    @property
    def application(self) -> Application: return self._application
    @property
    def lifecycle(self) -> ProjectWorkspaceLifecycle: return self._lifecycle
    @property
    def project_lifecycle(self): return self._application.project_lifecycle
    @property
    def is_dirty(self) -> bool: return self._application.is_dirty
    @property
    def state(self) -> ProjectWorkspaceState: return self._lifecycle.state

    def subscribe(self, handler: WorkspaceUpdateHandler) -> None:
        if not callable(handler): raise TypeError("handler must be callable.")
        if handler not in self._handlers: self._handlers.append(handler)

    def unsubscribe(self, handler: WorkspaceUpdateHandler) -> None:
        try: self._handlers.remove(handler)
        except ValueError: return

    def _configure_presentation_transaction(
        self,
        document: Document | None = None,
        *,
        open_existing: bool,
        activate_workspace: bool,
    ) -> None:
        def factory(context: ProjectContext) -> Document:
            if document is not None:
                if document.project_id not in (None, context.project_id):
                    raise ValueError("presentation document belongs to a different project.")
                return document
            return SLDDocument(
                document_id=f"{context.project_id}:sld",
                name=f"{context.name} SLD",
                project_id=context.project_id,
            )

        def serializer(value: Document):
            to_dict = getattr(value, "to_dict", None)
            if not callable(to_dict):
                raise TypeError("presentation document must provide to_dict().")
            return to_dict()

        def activate(context: ProjectContext | None, presentation: object | None):
            return self._activate_workspace_presentation(
                context,
                presentation,
                open_existing=open_existing,
                activate_workspace=activate_workspace,
            )

        self._application.configure_project_presentation_contract(
            factory=factory,
            serializer=serializer,
            deserializer=SLDDocument.from_dict,
        )
        self._application.configure_presentation_activator(activate)

    def _activate_workspace_presentation(
        self,
        context: ProjectContext | None,
        presentation: object | None,
        *,
        open_existing: bool,
        activate_workspace: bool,
    ):
        snapshot = self._lifecycle.capture_transition_state()
        try:
            if context is None:
                self._lifecycle.close_project()
            else:
                if not isinstance(presentation, Document):
                    raise RuntimeError("Application transition did not provide a workspace Document.")
                self._lifecycle.activate_project_transition(
                    self._to_ui_project(context),
                    document=presentation,
                    activate_workspace=activate_workspace,
                    open_existing=open_existing,
                )
            return lambda: self._lifecycle.restore_last_state(snapshot)
        except BaseException:
            self._lifecycle.restore_last_state(snapshot)
            raise

    @staticmethod
    def _is_cancel(decision: ProjectTransitionDecision | str | None) -> bool:
        return (
            decision is ProjectTransitionDecision.CANCEL
            or (
                isinstance(decision, str)
                and decision.strip().lower() == ProjectTransitionDecision.CANCEL.value
            )
        )

    def _run_transition(
        self,
        *,
        operation: str,
        configure: Callable[[], None],
        transition: Callable[[], ProjectContext | None],
        decision: ProjectTransitionDecision | str | None,
    ) -> ProjectContext | None:
        # CANCEL is resolved before any lifecycle configuration is touched.
        if self._is_cancel(decision):
            current = self._application.project_lifecycle.context
            if current is None:
                raise RuntimeError("Cancel cannot leave the Application without an active project.")
            return current

        configuration = self._application.project_lifecycle.capture_presentation_configuration()
        try:
            configure()
            context = transition()
            # Application owns the authoritative transition result. The adapter
            # publishes only after Application success, so SAVE/DISCARD produce
            # one presentation transition and failures publish nothing.
            if self._is_cancel(decision):
                return context
            if context is not None:
                self._publish(operation, self._lifecycle.state, context.project_id)
            return context
        except BaseException:
            # A failed Application/UI activation must restore the exact prior
            # presentation contract as well as the workspace rollback performed
            # by the lifecycle activator.
            self._application.project_lifecycle.restore_presentation_configuration(configuration)
            raise

    def new_project(
        self,
        name: str = "Untitled Project",
        *,
        project_id: str | None = None,
        document: Document | None = None,
        activate_workspace: bool = True,
        decision: ProjectTransitionDecision | str | None = None,
    ) -> ProjectContext:
        if self._application.is_dirty and self._is_cancel(decision):
            current = self._application.project_lifecycle.context
            if current is None:
                raise RuntimeError("Cancel cannot leave the Application without an active project.")
            return current
        context = self._run_transition(
            operation="new",
            configure=lambda: self._configure_presentation_transaction(
                document,
                open_existing=False,
                activate_workspace=activate_workspace,
            ),
            transition=lambda: self._application.new_project(name, project_id=project_id, decision=decision),
            decision=decision,
        )
        if context is None:
            raise RuntimeError("New project transition did not return a project context.")
        return context

    def open_project(
        self,
        path: str,
        *,
        activate_workspace: bool = True,
        decision: ProjectTransitionDecision | str | None = None,
    ) -> ProjectContext:
        if self._application.is_dirty and self._is_cancel(decision):
            current = self._application.project_lifecycle.context
            if current is None:
                raise RuntimeError("Cancel cannot leave the Application without an active project.")
            return current
        context = self._run_transition(
            operation="open",
            configure=lambda: self._configure_presentation_transaction(
                open_existing=True,
                activate_workspace=activate_workspace,
            ),
            transition=lambda: self._application.open_project(path, decision=decision),
            decision=decision,
        )
        if context is None:
            raise RuntimeError("Open project transition did not return a project context.")
        return context

    def close_project(
        self,
        *,
        decision: ProjectTransitionDecision | str | None = None,
    ) -> ProjectContext | None:
        if self._application.is_dirty and self._is_cancel(decision):
            return self._application.project_lifecycle.context
        return self._run_transition(
            operation="close",
            configure=lambda: self._configure_presentation_transaction(
                open_existing=False,
                activate_workspace=False,
            ),
            transition=lambda: self._application.close_project(decision=decision),
            decision=decision,
        )

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
