"""Application-side Control feedback and acknowledgement contract.

Author: Subhendu Mishra

This module distinguishes command lifecycle from observed physical state.
It consumes Application read models; it never reaches Core objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


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
        object.__setattr__(self, "metadata", dict(self.metadata or {}))


__all__ = ["ControlFeedbackStatus", "ControlFeedback"]
