"""Typed, read-only recovery state exposed by the Application boundary.

This module deliberately does not attempt to repair degraded runtime state.
Recovery requires a fresh Application composition from a canonical project package.
"""

from __future__ import annotations

from dataclasses import dataclass


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


__all__ = ["ApplicationRecoveryStatus"]
