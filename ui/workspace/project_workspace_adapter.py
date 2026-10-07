# ============================================================
# File: ui/workspace/project_workspace_adapter.py
# GridForge V2 — Project Workspace Application Adapter
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from core.application import Application
from core.application.project import ProjectContext
from core.application.project_transition import ProjectTransitionDecision
from core.application.project_presentation import ProjectPresentationCollection
from ui.sld.sld_document import SLDDocument
from .document import Document
from .project import Project
from .project_workspace import ProjectWorkspaceLifecycle, ProjectWorkspaceState
from .view_manager import ViewRecord


@dataclass(frozen=True, slots=True)
class ProjectWorkspaceChanged:
    """Immutable UI update emitted after a successful engineer-visible transition."""

    operation: str
    state: ProjectWorkspaceState
    project_id: str


WorkspaceUpdateHandler = Callable[[ProjectWorkspaceChanged], None]
PresentationActivationBridge = Callable[[Document | None], None]


class ProjectWorkspaceApplicationAdapter:
    """Bridge Application lifecycle success into the coordinated UI workspace transaction."""

    def __init__(self, application: Application, lifecycle: ProjectWorkspaceLifecycle) -> None:
        if not isinstance(application, Application): raise TypeError("application must be an Application.")
        if not isinstance(lifecycle, ProjectWorkspaceLifecycle): raise TypeError("lifecycle must be a ProjectWorkspaceLifecycle.")
        self._application = application
        self._lifecycle = lifecycle
        self._handlers: list[WorkspaceUpdateHandler] = []
        self._presentation_activation_bridge: PresentationActivationBridge | None = None
        self._document_transition_guard: Callable[[], None] | None = None
        self._pending_presentation_collection: ProjectPresentationCollection | None = None

    @property
    def application(self) -> Application: return self._application
    @property
    def lifecycle(self) -> ProjectWorkspaceLifecycle: return self._lifecycle
    @property
    def project_lifecycle(self): return self._application.project_lifecycle
    @property
    def is_dirty(self) -> bool:
        return bool(self._application.is_dirty or self._lifecycle.documents.dirty_document_ids)

    @property
    def active_document_id(self) -> str | None:
        return self._lifecycle.documents.active_document_id

    @property
    def documents(self):
        return self._lifecycle.documents
    @property
    def state(self) -> ProjectWorkspaceState: return self._lifecycle.state

    def configure_presentation_activation_bridge(self, bridge: PresentationActivationBridge) -> None:
        """Bind the UI-level presentation bridge used during project activation."""
        if not callable(bridge):
            raise TypeError("bridge must be callable.")
        self._presentation_activation_bridge = bridge

    def configure_document_transition_guard(self, guard: Callable[[], None]) -> None:
        if not callable(guard):
            raise TypeError("guard must be callable.")
        self._document_transition_guard = guard

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

        def collection_serializer(collection: ProjectPresentationCollection):
            documents = []
            for item in collection.documents:
                to_dict = getattr(item, "to_dict", None)
                if not callable(to_dict):
                    raise TypeError("project document must provide to_dict().")
                documents.append(to_dict())
            return {
                "schema": 1,
                "documents": documents,
                "active_document_id": collection.active_document_id,
            }

        def collection_deserializer(data):
            if not isinstance(data, dict):
                raise TypeError("presentation collection payload must be a mapping.")
            documents = []
            for item in data.get("documents", ()):
                documents.append(SLDDocument.from_dict(item))
            return ProjectPresentationCollection.ordered(
                documents,
                data.get("active_document_id"),
            )

        def collection_activator(context, collection):
            previous = self._pending_presentation_collection
            self._pending_presentation_collection = collection
            return lambda: setattr(self, "_pending_presentation_collection", previous)

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
        self._application.project_lifecycle.configure_presentation_collection_contract(
            serializer=collection_serializer,
            deserializer=collection_deserializer,
            activator=collection_activator,
        )
        self._application.project_lifecycle.configure_presentation_collection_snapshot_provider(
            self.snapshot_presentation_collection
        )
        self._application.configure_presentation_activator(activate)

    def snapshot_presentation_collection(self) -> ProjectPresentationCollection:
        """Return an immutable snapshot of the complete live DocumentManager collection."""
        documents = tuple(self._lifecycle.documents.documents())
        return ProjectPresentationCollection.ordered(
            documents,
            self._lifecycle.documents.active_document_id,
        )

    def _activate_workspace_presentation(
        self,
        context: ProjectContext | None,
        presentation: object | None,
        *,
        open_existing: bool,
        activate_workspace: bool,
    ):
        snapshot = self._lifecycle.capture_transition_state()
        previous_document = next(
            (
                document
                for document in snapshot.documents
                if document.document_id == snapshot.active_document_id
            ),
            None,
        )
        try:
            if context is None:
                self._lifecycle.close_project()
                active_document: Document | None = None
            else:
                if not isinstance(presentation, Document):
                    raise RuntimeError("Application transition did not provide a workspace Document.")
                collection = self._pending_presentation_collection
                self._pending_presentation_collection = None
                self._lifecycle.activate_project_transition(
                    self._to_ui_project(context),
                    document=presentation,
                    activate_workspace=activate_workspace,
                    open_existing=open_existing,
                )
                if collection is not None:
                    ordered = tuple(collection.documents)
                    for document_item in ordered:
                        if document_item.document_id != presentation.document_id:
                            self._lifecycle.documents.register(document_item)
                    for index, document_item in enumerate(ordered):
                        self._lifecycle.documents.move(document_item.document_id, index, mark_dirty=False)
                    self._lifecycle.documents.activate(
                        collection.active_document_id or presentation.document_id
                    )
                active_document = self._lifecycle.documents.active_document
            if self._presentation_activation_bridge is not None:
                self._presentation_activation_bridge(active_document)

            def rollback() -> None:
                self._lifecycle.restore_last_state(snapshot)
                if self._presentation_activation_bridge is not None:
                    self._presentation_activation_bridge(previous_document)

            return rollback
        except BaseException:
            self._lifecycle.restore_last_state(snapshot)
            if self._presentation_activation_bridge is not None:
                self._presentation_activation_bridge(previous_document)
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

    def activate_document(self, document_id: str) -> ProjectWorkspaceState:
        """Atomically activate one canonical workspace document and presentation."""
        document = self._lifecycle.documents.require(document_id)
        if not isinstance(document, SLDDocument):
            raise TypeError("Only SLDDocument activation is supported by the SLD document lifecycle.")
        snapshot = self._lifecycle.capture_transition_state()
        previous = self._lifecycle.document
        try:
            if self._document_transition_guard is not None:
                self._document_transition_guard()
            self._lifecycle.activate_document_id(document_id)
            self._application.activate_presentation(document)
            if self._presentation_activation_bridge is not None:
                self._presentation_activation_bridge(document)
            self._publish("activate_document", self._lifecycle.state, self._lifecycle.project.project_id)
            return self._lifecycle.state
        except BaseException:
            self._lifecycle.restore_last_state(snapshot)
            if previous is not None:
                try:
                    self._application.activate_presentation(previous)
                    if self._presentation_activation_bridge is not None:
                        self._presentation_activation_bridge(previous)
                except BaseException:
                    pass
            raise

    def new_sld_document(self, name: str | None = None) -> SLDDocument:
        """Create/register/activate a real SLD document through the canonical manager."""
        project = self._lifecycle.project
        if project is None:
            raise RuntimeError("Cannot create an SLD document without an active project.")
        previous = self._lifecycle.document
        if self._document_transition_guard is not None:
            self._document_transition_guard()
        document_name = name or f"SLD-{len(tuple(self._lifecycle.documents.documents())) + 1:02d}"
        document = self._lifecycle.create_document(
            "sld",
            name=document_name,
            factory=lambda document_id, project_id, item_name: SLDDocument(
                document_id=document_id,
                project_id=project_id,
                name=item_name,
            ),
        )
        self._lifecycle.add_view(ViewRecord(
            view_id=f"{document.document_id}:sld",
            document_id=document.document_id,
            view_type="sld",
        ))
        try:
            self.activate_document(document.document_id)
        except BaseException:
            self._lifecycle.remove_document(document.document_id)
            if previous is not None:
                try:
                    self._lifecycle.documents.activate(previous.document_id)
                    self._application.activate_presentation(previous)
                    if self._presentation_activation_bridge is not None:
                        self._presentation_activation_bridge(previous)
                except BaseException:
                    pass
            raise
        return document

    def close_document(
        self,
        document_id: str,
        *,
        decision: str = "cancel",
    ) -> ProjectWorkspaceState:
        """Close exactly one SLD document with save/discard/cancel semantics."""
        document = self._lifecycle.documents.require(document_id)
        if not isinstance(document, SLDDocument):
            raise TypeError("Only SLDDocument documents can be closed here.")
        decision = str(decision).strip().lower()
        if decision not in {"save", "discard", "cancel"}:
            raise ValueError("decision must be save, discard, or cancel.")
        if decision == "cancel":
            return self._lifecycle.state
        if self._document_transition_guard is not None:
            self._document_transition_guard()
        if self._lifecycle.documents.is_dirty(document_id):
            if decision == "save":
                previous_active = self._lifecycle.document
                previous_snapshot = self._lifecycle.capture_transition_state()
                try:
                    if previous_active is not document:
                        self.activate_document(document_id)
                    self._application.save_project()
                except BaseException:
                    self._lifecycle.restore_last_state(previous_snapshot)
                    if previous_active is not None:
                        try:
                            self._application.activate_presentation(previous_active)
                            if self._presentation_activation_bridge is not None:
                                self._presentation_activation_bridge(previous_active)
                        except BaseException:
                            pass
                    raise
            elif decision == "discard":
                document.mark_clean()
                self._lifecycle.documents.mark_clean(document_id)

        if len(self._lifecycle.documents) <= 1:
            raise RuntimeError("The active project must retain at least one SLD document.")
        snapshot = self._lifecycle.capture_transition_state()
        previous = self._lifecycle.document
        try:
            self._lifecycle.remove_document(document_id)
            active = self._lifecycle.document
            if active is not None:
                self._application.activate_presentation(active)
                if self._presentation_activation_bridge is not None:
                    self._presentation_activation_bridge(active)
            self._publish("close_document", self._lifecycle.state, self._lifecycle.project.project_id)
            return self._lifecycle.state
        except BaseException:
            self._lifecycle.restore_last_state(snapshot)
            if previous is not None:
                self._application.activate_presentation(previous)
                if self._presentation_activation_bridge is not None:
                    self._presentation_activation_bridge(previous)
            raise

    def is_document_dirty(self, document_id: str) -> bool:
        return self._lifecycle.documents.is_dirty(document_id)

    def save_project_as(self, path: str) -> ProjectContext:
        """Persist through the Application facade using a UI-resolved Save As path."""
        if not isinstance(path, str) or not path.strip():
            raise ValueError("A non-empty Save As path is required.")
        return self._application.save_project_as(path)

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
