"""Semantic Application events for Control and Ladder operations.

Author: Subhendu Mishra
"""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from .events import ApplicationEvent


class _ControlEvent(ApplicationEvent):
    _EVENT_TYPE = ""

    def __init__(self, *, metadata: Mapping[str, Any] | None = None,
                 correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(self._EVENT_TYPE, dict(metadata or {}),
                         correlation_id=correlation_id, causation_id=causation_id)


class ControlComponentCreated(_ControlEvent):
    _EVENT_TYPE = "control.component.created"


class ControlComponentUpdated(_ControlEvent):
    _EVENT_TYPE = "control.component.updated"


class ControlComponentRemoved(_ControlEvent):
    _EVENT_TYPE = "control.component.removed"


class ControlConnectionCreated(_ControlEvent):
    _EVENT_TYPE = "control.connection.created"


class ControlConnectionRemoved(_ControlEvent):
    _EVENT_TYPE = "control.connection.removed"


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
    "ControlComponentCreated",
    "ControlComponentUpdated",
    "ControlComponentRemoved",
    "ControlConnectionCreated",
    "ControlConnectionRemoved",
    "ControlDependencyCreated",
    "ControlDependencyRemoved",
    "ControlProgramChanged",
    "ControlStateChanged",
    "ControlExecutionStarted",
    "ControlExecutionCompleted",
    "ControlExecutionFailed",
]
