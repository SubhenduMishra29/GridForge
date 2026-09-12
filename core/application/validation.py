# ============================================================
# File: core/application/validation.py
# GridForge V2 — Application Validation Contracts
# Author: Subhendu Mishra
# ============================================================

"""Immutable Application-layer validation results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One immutable validation diagnostic."""

    code: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    element_id: str | None = None
    element_type: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code.strip():
            raise ValueError("ValidationIssue.code must be non-empty.")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("ValidationIssue.message must be non-empty.")
        if not isinstance(self.severity, ValidationSeverity):
            raise TypeError("ValidationIssue.severity must be ValidationSeverity.")


@dataclass(frozen=True, slots=True)
class ValidationSummary:
    """Immutable aggregate counts for a validation result."""

    errors: int = 0
    warnings: int = 0
    infos: int = 0

    @property
    def valid(self) -> bool:
        return self.errors == 0


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Immutable authoritative snapshot produced by Application validation."""

    model_revision: int
    topology_revision: int
    issues: tuple[ValidationIssue, ...]
    summary: ValidationSummary
    authoritative: bool = True

    @property
    def valid(self) -> bool:
        return self.summary.valid


__all__ = [
    "ValidationIssue",
    "ValidationResult",
    "ValidationSeverity",
    "ValidationSummary",
]
