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



class SLDAssociationState(str, Enum):
    """Application validation state for one persistent SLD equipment reference.

    UNREFERENCED is deliberately distinct from UNRESOLVED so that
    equipment_id=None does not acquire an implicit orphan meaning.
    """

    UNREFERENCED = "unreferenced"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class SLDAssociationReference:
    """Immutable diagnostic for one persistent SLD node equipment reference."""

    node_id: str
    equipment_id: str | None
    state: SLDAssociationState

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise ValueError("SLDAssociationReference.node_id must be non-empty.")
        if self.equipment_id is not None and not isinstance(self.equipment_id, str):
            raise TypeError("SLDAssociationReference.equipment_id must be a string or None.")
        if not isinstance(self.state, SLDAssociationState):
            raise TypeError("SLDAssociationReference.state must be SLDAssociationState.")
        object.__setattr__(self, "node_id", self.node_id.strip())


@dataclass(frozen=True, slots=True)
class SLDAssociationValidationResult:
    """Read-only Application validation of ProjectContext + Network + SLD data."""

    project_id: str
    references: tuple[SLDAssociationReference, ...] = ()
    issues: tuple[ValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("SLDAssociationValidationResult.project_id must be non-empty.")
        object.__setattr__(self, "project_id", self.project_id.strip())
        object.__setattr__(self, "references", tuple(self.references))
        object.__setattr__(self, "issues", tuple(self.issues))

    @property
    def unresolved(self) -> tuple[SLDAssociationReference, ...]:
        return tuple(
            reference
            for reference in self.references
            if reference.state is SLDAssociationState.UNRESOLVED
        )

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
    """Immutable validation result scoped to one project activation generation."""

    model_revision: int
    topology_revision: int
    issues: tuple[ValidationIssue, ...]
    summary: ValidationSummary
    authoritative: bool = True
    project_id: str | None = None
    activation_generation: int | None = None

    def __post_init__(self) -> None:
        if self.project_id is not None:
            if not isinstance(self.project_id, str) or not self.project_id.strip():
                raise ValueError("ValidationResult.project_id must be non-empty when supplied.")
            object.__setattr__(self, "project_id", self.project_id.strip())
        if self.activation_generation is not None:
            if (
                not isinstance(self.activation_generation, int)
                or isinstance(self.activation_generation, bool)
                or self.activation_generation < 1
            ):
                raise ValueError(
                    "ValidationResult.activation_generation must be a positive integer when supplied."
                )

    @property
    def valid(self) -> bool:
        return self.summary.valid

    @property
    def scope(self) -> tuple[str | None, int | None, int, int]:
        """Return project/generation/model/topology identity as one scope tuple."""
        return (
            self.project_id,
            self.activation_generation,
            self.model_revision,
            self.topology_revision,
        )


__all__ = [
    "SLDAssociationReference",
    "SLDAssociationState",
    "SLDAssociationValidationResult",
    "ValidationIssue",
    "ValidationResult",
    "ValidationSeverity",
    "ValidationSummary",
]
