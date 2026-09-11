"""Application boundary for protection outputs.

Protection functions produce immutable decisions. This service translates an
actionable decision into the canonical TripBreakerCommand and delegates its
execution to the Application facade so transaction, history, validation, and
semantic events remain Application-owned.
"""

from __future__ import annotations

from core.application.application import Application
from core.application.commands.breaker_commands import TripBreakerCommand
from core.application.results import ApplicationResult
from core.protection.decision import ProtectionDecision


class ProtectionOutputService:
    """Translate protection decisions into the authoritative Application path."""

    def __init__(self, application: Application) -> None:
        if not isinstance(application, Application):
            raise TypeError("application must be an Application.")
        self._application = application

    def trip_from_decision(
        self,
        *,
        decision: ProtectionDecision,
        breaker_id: str,
    ) -> ApplicationResult:
        """Execute an actionable protection trip through Application.execute()."""
        if not isinstance(decision, ProtectionDecision):
            raise TypeError("decision must be a ProtectionDecision.")
        if not decision.actionable:
            raise ValueError("Only an actionable ProtectionDecision may request a trip.")

        command = TripBreakerCommand(breaker_id=breaker_id)
        return self._application.execute(command)


__all__ = ["ProtectionOutputService"]
