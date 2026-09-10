"""Application boundary for protection outputs.

Author: Subhendu Mishra

Protection functions produce decisions; this service translates an actionable
decision into the existing Breaker application command path. It does not
operate a breaker directly and does not own protection state.
"""

from __future__ import annotations

from core.application.commands.breaker_commands import TripBreakerCommand
from core.application.results import ApplicationResult
from core.application.services.model_service import ModelService
from core.application.transaction import Transaction
from core.protection.decision import ProtectionDecision


class ProtectionOutputService:
    """Translate protection decisions into existing Application mutations."""

    def __init__(self, model_service: ModelService) -> None:
        if not isinstance(model_service, ModelService):
            raise TypeError("model_service must be a ModelService.")
        self._model_service = model_service

    def trip_from_decision(
        self,
        *,
        decision: ProtectionDecision,
        breaker_id: str,
        transaction: Transaction,
    ) -> ApplicationResult:
        """Execute an actionable protection trip through the canonical command path."""
        if not isinstance(decision, ProtectionDecision):
            raise TypeError("decision must be a ProtectionDecision.")
        if not decision.actionable:
            raise ValueError("Only an actionable ProtectionDecision may request a trip.")

        command = TripBreakerCommand(breaker_id=breaker_id)
        return self._model_service.trip_breaker(
            breaker_id=command.payload["breaker_id"],
            transaction=transaction,
        )


__all__ = ["ProtectionOutputService"]
