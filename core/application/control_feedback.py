"""Application-side Control feedback and acknowledgement contract.

Author: Subhendu Mishra

This module distinguishes command lifecycle from observed physical state.
It consumes Application read models; it never reaches Core objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


def _freeze_feedback_value(value: Any) -> Any:
    """Detach and freeze supported containers without coercing domain objects."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_feedback_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_feedback_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_feedback_value(item) for item in value)
    return value


class ControlFeedbackStatus(str, Enum):
    COMMAND_GENERATED = "command_generated"
    COMMAND_ACCEPTED = "command_accepted"
    COMMAND_EXECUTED = "command_executed"
    OBSERVED = "observed"
    INVALID = "invalid"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    MISMATCH = "mismatch"
    TIMEOUT = "timeout"
    ACKNOWLEDGED = "acknowledged"


@dataclass(frozen=True, slots=True)
class ControlFeedback:
    control_id: str
    target_id: str
    action: str
    status: ControlFeedbackStatus
    observed_state: Any = None
    expected_state: Any = None
    simulation_time: float | None = None
    diagnostic: str | None = None
    metadata: Mapping[str, Any] = None

    def __post_init__(self) -> None:
        metadata = self.metadata or {}
        if not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", _freeze_feedback_value(metadata))


__all__ = ["ControlFeedbackStatus", "ControlFeedback"]
