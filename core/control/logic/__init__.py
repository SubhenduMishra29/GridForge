"""
GridForge V2 - Logic Control Domain
====================================

Author:
    Subhendu Mishra

Package:
    core.control.logic

Purpose
-------
Headless domain contracts for discrete and logic-based control.

The visual logic-layout/editing canvas remains in the UI layer.
Concrete logic elements consume these Core contracts without introducing
UI dependencies.
"""

from .base import (
    LogicControlComponent,
    LogicControlError,
    LogicControlResult,
    LogicConfigurationError,
    LogicEdge,
    LogicEvaluationError,
    LogicEvent,
    LogicEventType,
    LogicInputError,
    LogicOutputError,
    LogicStateDefinition,
    LogicStateError,
)
from .comparators import UndervoltageComparator
from .ladder import LadderElementRef, LadderModelError, LadderProgram, LadderRung

# Existing Logic components use OUTPUT_CHANGED as the signal-transition
# vocabulary. Keep that established contract available without changing the
# meaning of the existing STATE_CHANGED event.
if not hasattr(LogicEventType, "OUTPUT_CHANGED"):
    setattr(LogicEventType, "OUTPUT_CHANGED", "output_changed")

__all__ = [
    "LogicControlComponent",
    "LogicControlError",
    "LogicControlResult",
    "LogicConfigurationError",
    "LogicEdge",
    "LogicEvaluationError",
    "LogicEvent",
    "LogicEventType",
    "LogicInputError",
    "LogicOutputError",
    "LogicStateDefinition",
    "LogicStateError",
    "LadderElementRef",
    "LadderModelError",
    "LadderProgram",
    "LadderRung",
    "UndervoltageComparator",
]
