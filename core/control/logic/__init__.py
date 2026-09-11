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

# Existing coil/latch/timer implementations reference OUTPUT_CHANGED while
# the frozen base enum predates that member. Until the canonical enum is
# expanded in a compatibility-safe change, expose the established semantic
# as an alias of STATE_CHANGED so those components remain executable rather
# than failing at runtime during event construction.
if not hasattr(LogicEventType, "OUTPUT_CHANGED"):
    setattr(LogicEventType, "OUTPUT_CHANGED", LogicEventType.STATE_CHANGED)

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
