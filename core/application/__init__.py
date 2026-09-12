# ============================================================
# File: core/application/__init__.py
# GridForge V2 — Headless Application Layer
# Author: Subhendu Mishra
# ============================================================

"""Headless Application boundary between consumers and GridForge Core."""

from __future__ import annotations

from .application import Application
from .control_cycle import ControlCycleResult, ControlCycleService, ControlDiagnostic
from .control_execution import ControlExecutionResult, ControlExecutionService
from .read_models import (
    ElementReadModel,
    NetworkReadModel,
    ProtectionReadModel,
    RelayInputBindingReadModel,
    RelayReadModel,
)
from .read_service import NetworkReadService, ProtectionReadService, ReadService
from .revision import ProjectRevision
from .revision_service import RevisionService
from .validation import ValidationIssue, ValidationResult, ValidationSeverity, ValidationSummary
from .services.validation_service import ValidationService

__all__ = [
    "Application",
    "ControlDiagnostic",
    "ControlCycleResult",
    "ControlCycleService",
    "ControlExecutionResult",
    "ControlExecutionService",
    "ElementReadModel",
    "NetworkReadModel",
    "ProtectionReadModel",
    "RelayInputBindingReadModel",
    "RelayReadModel",
    "NetworkReadService",
    "ProtectionReadService",
    "ReadService",
    "ProjectRevision",
    "RevisionService",
    "ValidationIssue",
    "ValidationResult",
    "ValidationSeverity",
    "ValidationSummary",
    "ValidationService",
]
