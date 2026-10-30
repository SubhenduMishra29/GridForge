# ============================================================
# File: core/application/study.py
# GridForge V2 — Application Study Boundary
# Author: Subhendu Mishra
# ============================================================
"""Application-owned study request, lifecycle, execution, and result boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Mapping
from threading import Lock, RLock
from uuid import UUID, uuid4

from .event_bus import ApplicationEventBus
from .revision import ProjectRevision
from .events import StudyCancelled, StudyCompleted, StudyFailed, StudyStarted
from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.short_circuit_configuration import ShortCircuitStudyConfiguration
from core.analysis.transient_stability import TransientStabilityStudyConfiguration
from core.analysis.coordination_study import CoordinationStudyConfiguration
from core.network.topology_snapshot import TopologySnapshot


@dataclass(frozen=True, slots=True)
class StudyExecutionContext:
    """Detached execution-time study context carrying canonical topology provenance."""
    project_id: str
    activation_generation: int
    source_revision: ProjectRevision
    topology_snapshot: TopologySnapshot
    project_snapshot: Any

    def __post_init__(self) -> None:
        if not isinstance(self.source_revision, ProjectRevision): raise TypeError("source_revision must be ProjectRevision.")
        if not isinstance(self.topology_snapshot, TopologySnapshot): raise TypeError("topology_snapshot must be TopologySnapshot.")
        if self.topology_snapshot.project_id != self.project_id or self.topology_snapshot.activation_generation != self.activation_generation:
            raise ValueError("TopologySnapshot provenance does not match study execution context.")
        if self.topology_snapshot.topology_revision != self.source_revision.topology_revision:
            raise ValueError("TopologySnapshot revision does not match source revision.")
        if self.project_snapshot is None:
            raise ValueError("project_snapshot is required.")
        # Both detached inputs must describe the same activated project state.
        # Matching only the topology snapshot is insufficient: a project/network
        # snapshot from another activation or model revision could otherwise be
        # paired with this request and yield a numerically valid but mis-scoped result.
        if getattr(self.project_snapshot, "project_id", None) != self.project_id:
            raise ValueError("ProjectSnapshot project identity does not match study execution context.")
        if getattr(self.project_snapshot, "activation_generation", None) != self.activation_generation:
            raise ValueError("ProjectSnapshot activation generation does not match study execution context.")
        snapshot_revision = getattr(self.project_snapshot, "revision", None)
        if not isinstance(snapshot_revision, ProjectRevision):
            raise TypeError("ProjectSnapshot revision must be ProjectRevision.")
        if snapshot_revision != self.source_revision:
            raise ValueError("ProjectSnapshot revision does not match study execution context source revision.")

@dataclass(frozen=True, slots=True)
class StudyRequest:
    """Immutable request boundary for one Application study execution."""

    study_id: UUID = field(default_factory=uuid4)
    project_id: str = ""
    activation_generation: int = 0
    source_revision: ProjectRevision | None = None
    study_type: str = ""
    configuration: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.study_id, UUID):
            raise TypeError("study_id must be a UUID.")
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        if not isinstance(self.activation_generation, int) or isinstance(self.activation_generation, bool) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if not isinstance(self.source_revision, ProjectRevision):
            raise TypeError("source_revision must be ProjectRevision.")
        if not isinstance(self.study_type, str) or not self.study_type.strip():
            raise ValueError("study_type must be a non-empty string.")
        if not isinstance(self.configuration, Mapping):
            raise TypeError("configuration must be a mapping.")
        object.__setattr__(self, "project_id", self.project_id.strip())
        object.__setattr__(self, "study_type", self.study_type.strip())
        object.__setattr__(self, "configuration", _freeze_study_value(self.configuration))


def _freeze_study_value(value: Any) -> Any:
    """Freeze Study Case configuration without converting typed Core/Analysis contracts."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_study_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_study_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_study_value(item) for item in value)
    return value


def _validate_study_case_configuration(study_type: str, configuration: Mapping[str, Any]) -> None:
    """Validate the existing typed study configuration contract at the Application boundary."""
    typed = configuration.get("configuration")
    if study_type == "power_flow" and not isinstance(typed, PowerFlowStudyConfiguration):
        raise TypeError("power_flow Study Case requires PowerFlowStudyConfiguration.")
    if study_type == "short_circuit" and not isinstance(typed, ShortCircuitStudyConfiguration):
        raise TypeError("short_circuit Study Case requires ShortCircuitStudyConfiguration.")
    if study_type == "transient_stability" and not isinstance(typed, TransientStabilityStudyConfiguration):
        raise TypeError("transient_stability Study Case requires TransientStabilityStudyConfiguration.")
    if study_type == "contingency" and not isinstance(typed, PowerFlowStudyConfiguration):
        raise TypeError("contingency Study Case requires its existing PowerFlowStudyConfiguration contract.")
    if study_type == "protection_coordination" and not isinstance(typed, CoordinationStudyConfiguration):
        raise TypeError("protection_coordination Study Case requires CoordinationStudyConfiguration.")


@dataclass(frozen=True, slots=True)
class StudyCaseDefinition:
    """Immutable Application-owned definition of a runnable Study Case."""

    study_id: UUID
    project_id: str
    activation_generation: int
    source_revision: ProjectRevision
    study_type: str
    configuration: Mapping[str, Any]
    display_name: str = ""
    is_stale: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.is_stale, bool):
            raise TypeError("is_stale must be a boolean.")
        if not isinstance(self.study_id, UUID):
            raise TypeError("study_id must be a UUID.")
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be non-empty.")
        if not isinstance(self.activation_generation, int) or isinstance(self.activation_generation, bool) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if not isinstance(self.source_revision, ProjectRevision):
            raise TypeError("source_revision must be ProjectRevision.")
        study_type = str(self.study_type).strip()
        if not study_type:
            raise ValueError("study_type must be non-empty.")
        if not isinstance(self.configuration, Mapping):
            raise TypeError("configuration must be a mapping.")
        _validate_study_case_configuration(study_type, self.configuration)
        object.__setattr__(self, "project_id", self.project_id.strip())
        object.__setattr__(self, "study_type", study_type)
        object.__setattr__(self, "configuration", _freeze_study_value(self.configuration))
        name = str(self.display_name).strip() or f"{study_type.replace('_', ' ').title()} Study"
        object.__setattr__(self, "display_name", name)

    @classmethod
    def from_request(cls, request: "StudyRequest") -> "StudyCaseDefinition":
        return cls(
            study_id=request.study_id,
            project_id=request.project_id,
            activation_generation=request.activation_generation,
            source_revision=request.source_revision,
            study_type=request.study_type,
            configuration=request.configuration,
        )


@dataclass(frozen=True, slots=True)
class StudyResult:
    """Immutable Application study result registration."""

    study_id: UUID
    project_id: str
    activation_generation: int
    source_revision: ProjectRevision
    study_type: str
    status: str
    value: Any = None
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.study_id, UUID):
            raise TypeError("study_id must be a UUID.")
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        if not isinstance(self.activation_generation, int) or isinstance(self.activation_generation, bool) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if not isinstance(self.source_revision, ProjectRevision):
            raise TypeError("source_revision must be ProjectRevision.")
        if not isinstance(self.study_type, str) or not self.study_type.strip():
            raise ValueError("study_type must be a non-empty string.")
        if self.status not in {"completed", "failed", "cancelled"}:
            raise ValueError("status must be completed, failed, or cancelled.")
        object.__setattr__(self, "project_id", self.project_id.strip())
        object.__setattr__(self, "study_type", self.study_type.strip())
        object.__setattr__(self, "message", str(self.message))
        object.__setattr__(self, "metadata", _freeze_study_value(self.metadata))


class StudyCancellationToken:
    """Cooperative cancellation state supplied to long-running study handlers.

    Cancellation and completion are coordinated by StudyService under its
    lock. Once finish() has linearized the terminal outcome, cancel() refuses
    late requests instead of reporting cancellation that cannot affect result.
    """

    def __init__(self) -> None:
        self._cancelled = False
        self._finished = False
        self._lock = Lock()

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def cancel(self) -> bool:
        """Request cancellation; return False once a terminal outcome is fixed."""
        with self._lock:
            if self._finished:
                return False
            self._cancelled = True
            return True

    def finish(self) -> bool:
        """Atomically mark terminal state and return whether cancellation won."""
        with self._lock:
            self._finished = True
            return self._cancelled


StudyHandler = Callable[[StudyRequest, StudyExecutionContext, StudyCancellationToken], Any]


class StudyService:
    """Single Application-owned study execution/orchestration boundary."""

    def __init__(self, event_bus: ApplicationEventBus, *, publication_lock: Any | None = None) -> None:
        if not isinstance(event_bus, ApplicationEventBus):
            raise TypeError("event_bus must be an ApplicationEventBus.")
        if publication_lock is not None and not callable(getattr(publication_lock, "__enter__", None)):
            raise TypeError("publication_lock must be a context manager or None.")
        if publication_lock is not None and not callable(getattr(publication_lock, "__exit__", None)):
            raise TypeError("publication_lock must be a context manager or None.")
        self._event_bus = event_bus
        self._publication_lock = publication_lock
        self._handlers: dict[str, StudyHandler] = {}
        self._results: dict[tuple[str, int, UUID], StudyResult] = {}
        self._tokens: dict[tuple[str, int, UUID], StudyCancellationToken] = {}
        # Counts by study type prevent teardown while any execution is active.
        self._active_study_types: dict[str, int] = {}
        self._lock = RLock()

    @property
    def registered_study_types(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._handlers)

    @staticmethod
    def _event_metadata(request: StudyRequest, *, status: str | None = None, error: str | None = None) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "study_id": str(request.study_id),
            "study_type": request.study_type,
            "project_id": request.project_id,
            "activation_generation": request.activation_generation,
            "model_revision": request.source_revision.model_revision,
            "topology_revision": request.source_revision.topology_revision,
            "presentation_revision": request.source_revision.presentation_revision,
            "persisted_revision": request.source_revision.persisted_revision,
        }
        if status is not None:
            metadata["status"] = status
        if error is not None:
            metadata["error"] = error
        return metadata

    def register(self, study_type: str, handler: StudyHandler) -> None:
        if not isinstance(study_type, str) or not study_type.strip():
            raise ValueError("study_type must be a non-empty string.")
        if not callable(handler):
            raise TypeError("handler must be callable.")
        key = study_type.strip()
        with self._lock:
            if key in self._handlers:
                raise ValueError(f"Study type already registered: {key!r}")
            self._handlers[key] = handler

    def unregister(self, study_type: str, handler: StudyHandler | None = None) -> bool:
        """Remove an idle registration, optionally guarded by handler identity.

        A stale plugin instance cannot remove a replacement registration, and
        teardown cannot remove a handler while its study type is executing.
        """
        if not isinstance(study_type, str) or not study_type.strip():
            raise ValueError("study_type must be a non-empty string.")
        if handler is not None and not callable(handler):
            raise TypeError("handler must be callable when supplied.")
        key = study_type.strip()
        with self._lock:
            if key not in self._handlers:
                return False
            if handler is not None and self._handlers.get(key) is not handler:
                return False
            if self._active_study_types.get(key, 0):
                raise RuntimeError(f"Cannot unregister active study type: {key!r}")
            del self._handlers[key]
            return True

    def execute(
        self,
        request: StudyRequest,
        execution_context: StudyExecutionContext,
        *,
        publication_guard: Callable[[], bool] | None = None,
    ) -> StudyResult:
        if not isinstance(request, StudyRequest):
            raise TypeError("request must be a StudyRequest.")
        if not isinstance(execution_context, StudyExecutionContext):
            raise TypeError("execution_context must be StudyExecutionContext.")
        if execution_context.project_id != request.project_id or execution_context.activation_generation != request.activation_generation:
            raise ValueError("Study execution context does not match StudyRequest scope.")
        if execution_context.source_revision != request.source_revision:
            raise ValueError("Study execution context does not match StudyRequest revision.")
        if publication_guard is not None and not callable(publication_guard):
            raise TypeError("publication_guard must be callable or None.")
        key = (request.project_id, request.activation_generation, request.study_id)
        token = StudyCancellationToken()
        with self._lock:
            handler = self._handlers.get(request.study_type)
            if handler is None:
                raise KeyError(f"No study handler registered for {request.study_type!r}.")
            if key in self._tokens:
                raise ValueError(f"Study is already active: {request.study_id}")
            self._tokens[key] = token
            self._active_study_types[request.study_type] = self._active_study_types.get(request.study_type, 0) + 1

        try:
            self._event_bus.publish(StudyStarted(metadata=self._event_metadata(request, status="started")))
            value = handler(request, execution_context, token)
            # Serialize the final freshness check, result registration, and
            # terminal event against Application command mutations. Numerical
            # work remains concurrent and never holds this lock.
            publication_scope = self._publication_lock
            if publication_scope is None:
                from contextlib import nullcontext
                publication_scope = nullcontext()
            with publication_scope:
                with self._lock:
                    cancelled = token.finish()
                    stale = (
                        not cancelled
                        and publication_guard is not None
                        and not publication_guard()
                    )
                    if cancelled:
                        result = StudyResult(
                            study_id=request.study_id,
                            project_id=request.project_id,
                            activation_generation=request.activation_generation,
                            source_revision=request.source_revision,
                            study_type=request.study_type,
                            status="cancelled",
                            message="Study cancelled.",
                        )
                    elif stale:
                        message = (
                            "Study inputs changed before result publication; "
                            "the calculated value was discarded."
                        )
                        result = StudyResult(
                            study_id=request.study_id,
                            project_id=request.project_id,
                            activation_generation=request.activation_generation,
                            source_revision=request.source_revision,
                            study_type=request.study_type,
                            status="failed",
                            message=message,
                            metadata={"failure_reason": "stale_source"},
                        )
                    else:
                        result = StudyResult(
                            study_id=request.study_id,
                            project_id=request.project_id,
                            activation_generation=request.activation_generation,
                            source_revision=request.source_revision,
                            study_type=request.study_type,
                            status="completed",
                            value=value,
                        )
                    self._results[key] = result
                if cancelled:
                    self._event_bus.publish(StudyCancelled(metadata=self._event_metadata(request, status="cancelled")))
                elif stale:
                    self._event_bus.publish(
                        StudyFailed(
                            metadata=self._event_metadata(
                                request,
                                status="failed",
                                error=result.message,
                            )
                        )
                    )
                else:
                    self._event_bus.publish(StudyCompleted(metadata=self._event_metadata(request, status="completed")))
            return result
        except Exception as exc:
            # A cancellation request may race with a solver exception. Resolve
            # the terminal state atomically: if cancellation was already
            # requested before finish(), publish cancellation rather than a
            # contradictory failure event. Otherwise preserve the exception.
            with self._lock:
                cancelled = token.finish()
                if cancelled:
                    result = StudyResult(
                        study_id=request.study_id,
                        project_id=request.project_id,
                        activation_generation=request.activation_generation,
                        source_revision=request.source_revision,
                        study_type=request.study_type,
                        status="cancelled",
                        message="Study cancelled.",
                    )
                else:
                    result = StudyResult(
                        study_id=request.study_id,
                        project_id=request.project_id,
                        activation_generation=request.activation_generation,
                        source_revision=request.source_revision,
                        study_type=request.study_type,
                        status="failed",
                        message=str(exc),
                    )
                self._results[key] = result
            if cancelled:
                self._event_bus.publish(StudyCancelled(metadata=self._event_metadata(request, status="cancelled")))
                return result
            self._event_bus.publish(StudyFailed(metadata=self._event_metadata(request, status="failed", error=str(exc))))
            raise
        finally:
            with self._lock:
                self._tokens.pop(key, None)
                active_count = self._active_study_types.get(request.study_type, 0)
                if active_count <= 1:
                    self._active_study_types.pop(request.study_type, None)
                else:
                    self._active_study_types[request.study_type] = active_count - 1

    @property
    def has_active_studies(self) -> bool:
        with self._lock:
            return bool(self._tokens)

    def ensure_no_active_studies(self) -> None:
        with self._lock:
            if self._tokens:
                scopes = ", ".join(
                    f"{project_id}:{generation}:{study_id}"
                    for project_id, generation, study_id in self._tokens
                )
                raise RuntimeError(f"Project transition blocked by active study scope(s): {scopes}")

    def cancel(self, study_id: UUID, *, project_id: str, activation_generation: int) -> bool:
        with self._lock:
            token = self._tokens.get((project_id, activation_generation, study_id))
            if token is None:
                return False
            return token.cancel()

    def get_result(self, study_id: UUID, *, project_id: str, activation_generation: int) -> StudyResult | None:
        with self._lock:
            return self._results.get((project_id, activation_generation, study_id))

    def results(self, *, project_id: str | None = None, activation_generation: int | None = None) -> tuple[StudyResult, ...]:
        with self._lock:
            values = tuple(self._results.values())
        if project_id is None and activation_generation is None:
            return values
        return tuple(result for result in values if (project_id is None or result.project_id == project_id) and (activation_generation is None or result.activation_generation == activation_generation))


__all__ = [
    "StudyExecutionContext",
    "StudyRequest",
    "StudyCaseDefinition",
    "StudyResult",
    "StudyCancellationToken",
    "StudyHandler",
    "StudyService",
]
