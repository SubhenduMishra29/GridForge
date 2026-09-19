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
from uuid import UUID, uuid4

from .event_bus import ApplicationEventBus
from .events import StudyCancelled, StudyCompleted, StudyFailed, StudyStarted


@dataclass(frozen=True, slots=True)
class StudyRequest:
    """Immutable request boundary for one Application study execution."""

    study_id: UUID = field(default_factory=uuid4)
    project_id: str = ""
    activation_generation: int = 0
    study_type: str = ""
    configuration: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.study_id, UUID):
            raise TypeError("study_id must be a UUID.")
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        if not isinstance(self.activation_generation, int) or isinstance(self.activation_generation, bool) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if not isinstance(self.study_type, str) or not self.study_type.strip():
            raise ValueError("study_type must be a non-empty string.")
        if not isinstance(self.configuration, Mapping):
            raise TypeError("configuration must be a mapping.")
        object.__setattr__(self, "project_id", self.project_id.strip())
        object.__setattr__(self, "study_type", self.study_type.strip())
        object.__setattr__(self, "configuration", MappingProxyType(dict(self.configuration)))


@dataclass(frozen=True, slots=True)
class StudyResult:
    """Immutable Application study result registration."""

    study_id: UUID
    project_id: str
    activation_generation: int
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
        if not isinstance(self.study_type, str) or not self.study_type.strip():
            raise ValueError("study_type must be a non-empty string.")
        if self.status not in {"completed", "failed", "cancelled"}:
            raise ValueError("status must be completed, failed, or cancelled.")
        object.__setattr__(self, "project_id", self.project_id.strip())
        object.__setattr__(self, "study_type", self.study_type.strip())
        object.__setattr__(self, "message", str(self.message))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class StudyCancellationToken:
    """Cooperative cancellation state supplied to long-running study handlers."""

    def __init__(self) -> None:
        self._cancelled = False

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True


StudyHandler = Callable[[StudyRequest, StudyCancellationToken], Any]


class StudyService:
    """Single Application-owned study execution/orchestration boundary."""

    def __init__(self, event_bus: ApplicationEventBus) -> None:
        if not isinstance(event_bus, ApplicationEventBus):
            raise TypeError("event_bus must be an ApplicationEventBus.")
        self._event_bus = event_bus
        self._handlers: dict[str, StudyHandler] = {}
        self._results: dict[tuple[str, int, UUID], StudyResult] = {}
        self._tokens: dict[tuple[str, int, UUID], StudyCancellationToken] = {}

    @property
    def registered_study_types(self) -> tuple[str, ...]:
        return tuple(self._handlers)

    def register(self, study_type: str, handler: StudyHandler) -> None:
        if not isinstance(study_type, str) or not study_type.strip():
            raise ValueError("study_type must be a non-empty string.")
        if not callable(handler):
            raise TypeError("handler must be callable.")
        key = study_type.strip()
        if key in self._handlers:
            raise ValueError(f"Study type already registered: {key!r}")
        self._handlers[key] = handler

    def execute(self, request: StudyRequest) -> StudyResult:
        if not isinstance(request, StudyRequest):
            raise TypeError("request must be a StudyRequest.")
        handler = self._handlers.get(request.study_type)
        if handler is None:
            raise KeyError(f"No study handler registered for {request.study_type!r}.")

        key = (request.project_id, request.activation_generation, request.study_id)
        if key in self._tokens:
            raise ValueError(f"Study is already active: {request.study_id}")
        token = StudyCancellationToken()
        self._tokens[key] = token
        self._event_bus.publish(StudyStarted(metadata={
            "study_id": str(request.study_id),
            "study_type": request.study_type,
            "project_id": request.project_id,
            "activation_generation": request.activation_generation,
        }))

        try:
            value = handler(request, token)
            if token.cancelled:
                result = StudyResult(
                    study_id=request.study_id,
                    project_id=request.project_id,
                    activation_generation=request.activation_generation,
                    study_type=request.study_type,
                    status="cancelled",
                    message="Study cancelled.",
                )
                self._results[request.study_id] = result
                self._event_bus.publish(StudyCancelled(metadata={
                    "study_id": str(request.study_id),
                    "study_type": request.study_type,
                    "project_id": request.project_id,
                    "activation_generation": request.activation_generation,
                }))
                return result

            result = StudyResult(
                study_id=request.study_id,
                project_id=request.project_id,
                activation_generation=request.activation_generation,
                study_type=request.study_type,
                status="completed",
                value=value,
            )
            self._results[request.study_id] = result
            self._event_bus.publish(StudyCompleted(metadata={
                "study_id": str(request.study_id),
                "study_type": request.study_type,
                "project_id": request.project_id,
                "activation_generation": request.activation_generation,
            }))
            return result
        except Exception as exc:
            result = StudyResult(
                study_id=request.study_id,
                project_id=request.project_id,
                activation_generation=request.activation_generation,
                study_type=request.study_type,
                status="failed",
                message=str(exc),
            )
            self._results[request.study_id] = result
            self._event_bus.publish(StudyFailed(metadata={
                "study_id": str(request.study_id),
                "study_type": request.study_type,
                "project_id": request.project_id,
                "activation_generation": request.activation_generation,
                "error": str(exc),
            }))
            raise
        finally:
            self._tokens.pop(key, None)

    def cancel(self, study_id: UUID, *, project_id: str, activation_generation: int) -> bool:
        token = self._tokens.get((project_id, activation_generation, study_id))
        if token is None:
            return False
        token.cancel()
        return True

    def get_result(self, study_id: UUID, *, project_id: str, activation_generation: int) -> StudyResult | None:
        return self._results.get((project_id, activation_generation, study_id))

    def results(self, *, project_id: str | None = None, activation_generation: int | None = None) -> tuple[StudyResult, ...]:
        values = tuple(self._results.values())
        if project_id is None and activation_generation is None:
            return values
        return tuple(result for result in values if (project_id is None or result.project_id == project_id) and (activation_generation is None or result.activation_generation == activation_generation))


__all__ = [
    "StudyRequest",
    "StudyResult",
    "StudyCancellationToken",
    "StudyHandler",
    "StudyService",
]
