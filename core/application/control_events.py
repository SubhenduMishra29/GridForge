"""Semantic Application events for Control and Ladder operations.

Author: Subhendu Mishra
"""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from .events import ApplicationEvent


class _ControlEvent(ApplicationEvent):
    _EVENT_TYPE = ""

    def __init__(
        self,
        *,
        payload: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        merged = dict(payload or {})
        merged.update(metadata or {})
        super().__init__(
            self._EVENT_TYPE,
            merged,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class ControlComponentCreated(_ControlEvent):
    _EVENT_TYPE = "control.component.created"

    def __init__(self, *, component_id: str, component_type: str,
                 metadata: Mapping[str, Any] | None = None,
                 correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(
            payload={"component_id": component_id, "component_type": component_type},
            metadata=metadata, correlation_id=correlation_id, causation_id=causation_id,
        )


class ControlComponentUpdated(_ControlEvent):
    _EVENT_TYPE = "control.component.updated"

    def __init__(self, *, component_id: str, changes: Mapping[str, Any] | None = None,
                 metadata: Mapping[str, Any] | None = None,
                 correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(
            payload={"component_id": component_id, "changes": dict(changes or {})},
            metadata=metadata, correlation_id=correlation_id, causation_id=causation_id,
        )


class ControlComponentRemoved(_ControlEvent):
    _EVENT_TYPE = "control.component.removed"

    def __init__(self, *, component_id: str, component_type: str | None = None,
                 metadata: Mapping[str, Any] | None = None,
                 correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        payload: dict[str, Any] = {"component_id": component_id}
        if component_type is not None:
            payload["component_type"] = component_type
        super().__init__(
            payload=payload, metadata=metadata,
            correlation_id=correlation_id, causation_id=causation_id,
        )


class ControlConnectionCreated(_ControlEvent):
    _EVENT_TYPE = "control.connection.created"

    def __init__(self, *, connection_id: str | None = None,
                 source_id: str | None = None, target_id: str | None = None,
                 metadata: Mapping[str, Any] | None = None,
                 correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        payload = {"connection_id": connection_id, "source_id": source_id, "target_id": target_id}
        super().__init__(
            payload={k: v for k, v in payload.items() if v is not None},
            metadata=metadata, correlation_id=correlation_id, causation_id=causation_id,
        )


class ControlConnectionRemoved(_ControlEvent):
    _EVENT_TYPE = "control.connection.removed"

    def __init__(self, *, connection_id: str | None = None,
                 source_id: str | None = None, target_id: str | None = None,
                 metadata: Mapping[str, Any] | None = None,
                 correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        payload = {"connection_id": connection_id, "source_id": source_id, "target_id": target_id}
        super().__init__(
            payload={k: v for k, v in payload.items() if v is not None},
            metadata=metadata, correlation_id=correlation_id, causation_id=causation_id,
        )


class ControlDependencyCreated(_ControlEvent):
    _EVENT_TYPE = "control.dependency.created"


class ControlDependencyRemoved(_ControlEvent):
    _EVENT_TYPE = "control.dependency.removed"


class ControlProgramChanged(_ControlEvent):
    _EVENT_TYPE = "control.program.changed"


class ControlStateChanged(_ControlEvent):
    _EVENT_TYPE = "control.state.changed"


class ControlExecutionStarted(_ControlEvent):
    _EVENT_TYPE = "control.execution.started"


class ControlExecutionCompleted(_ControlEvent):
    _EVENT_TYPE = "control.execution.completed"


class ControlExecutionFailed(_ControlEvent):
    _EVENT_TYPE = "control.execution.failed"


__all__ = [
    "ControlComponentCreated", "ControlComponentUpdated", "ControlComponentRemoved",
    "ControlConnectionCreated", "ControlConnectionRemoved",
    "ControlDependencyCreated", "ControlDependencyRemoved", "ControlProgramChanged",
    "ControlStateChanged", "ControlExecutionStarted", "ControlExecutionCompleted",
    "ControlExecutionFailed",
]
