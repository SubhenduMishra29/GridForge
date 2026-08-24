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
]
