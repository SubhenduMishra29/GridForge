"""Typed recovery state and composition contracts at the Application boundary.

This module deliberately does not attempt to repair degraded runtime state.
Recovery requires a fresh Application composition from a canonical project package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .application import Application
    from .project import ProjectContext


@dataclass(frozen=True, slots=True)
class ApplicationRecoveryStatus:
    """Immutable summary of command and project-lifecycle recovery state."""

    command_integrity_state: str
    project_lifecycle_state: str
    project_id: str | None
    activation_generation: int
    recovery_artifact_available: bool
    recovery_required: bool

    @property
    def recovery_reason(self) -> str | None:
        """Return a stable, non-sensitive reason code for UI presentation."""
        if self.command_integrity_state == "DEGRADED":
            return "COMMAND_BOUNDARY_DEGRADED"
        if self.project_lifecycle_state == "ROLLBACK_FAILED":
            return "PROJECT_ACTIVATION_ROLLBACK_FAILED"
        return None


@dataclass(frozen=True, slots=True)
class ApplicationRecoveryComposition:
    """Composition-owner hooks for restoring and validating a replacement.

    The configure callback runs on the fresh Application before the canonical
    package is opened. It must install the complete presentation persistence and
    activation contracts, including the collection contract and the fresh
    workspace/SLD activation dependencies.

    The validate callback runs after project activation. It must verify that the
    newly composed workspace adopted the restored collection and persisted
    active-document identity. UI-specific validation stays outside Core.
    """

    configure_replacement: Callable[["Application"], None]
    validate_replacement: Callable[["Application", "ProjectContext"], None]

    def __post_init__(self) -> None:
        if not callable(self.configure_replacement):
            raise TypeError("configure_replacement must be callable.")
        if not callable(self.validate_replacement):
            raise TypeError("validate_replacement must be callable.")


__all__ = ["ApplicationRecoveryStatus", "ApplicationRecoveryComposition"]
