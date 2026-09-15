# ============================================================
# File: core/application/protection_execution.py
# GridForge V2 — Protection Application Orchestration
# Author: Subhendu Mishra
# ============================================================

"""Application-owned orchestration for evaluating protection intent.

Protection functions remain pure Core decision producers. This service
coordinates evaluation and translates an actionable trip decision into
the existing immutable Application ``TripBreakerCommand``. It never
mutates Core directly and never introduces a second event bus or breaker API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from core.application.command import Command
from core.application.commands.breaker_commands import TripBreakerCommand
from core.application.results import ApplicationResult
from core.protection.decision import ProtectionDecision


@dataclass(frozen=True, slots=True)
class ProtectionExecutionResult:
    """Immutable result of one Application-side protection evaluation."""

    decisions: tuple[ProtectionDecision, ...] = ()
    trip_commands: tuple[TripBreakerCommand, ...] = ()
    application_results: tuple[ApplicationResult, ...] = ()
    diagnostics: tuple[str, ...] = ()


class ProtectionExecutionService:
    """Dispatch actionable protection trips through Application commands."""

    def __init__(
        self,
        command_executor: Callable[[Command], ApplicationResult],
        *,
        breaker_resolver: Callable[[ProtectionDecision], str | None] | None = None,
    ) -> None:
        if not callable(command_executor):
            raise TypeError("command_executor must be callable.")
        if breaker_resolver is not None and not callable(breaker_resolver):
            raise TypeError("breaker_resolver must be callable or None.")
        self._command_executor = command_executor
        self._breaker_resolver = breaker_resolver

    def execute(
        self,
        decisions: Iterable[ProtectionDecision],
    ) -> ProtectionExecutionResult:
        """Evaluate already-produced decisions and dispatch valid trip intent.

        A ProtectionDecision remains authoritative for protection semantics.
        Only ``trip_request`` decisions are translated. A breaker target must
        be explicitly supplied by the configured resolver; this service never
        guesses a breaker from arbitrary project objects.
        """
        decision_tuple = tuple(decisions)
        commands: list[TripBreakerCommand] = []
        results: list[ApplicationResult] = []
        diagnostics: list[str] = []

        for decision in decision_tuple:
            if not isinstance(decision, ProtectionDecision):
                raise TypeError("decisions must contain ProtectionDecision values.")
            if not decision.trip_request:
                continue
            if self._breaker_resolver is None:
                diagnostics.append(
                    f"Protection decision '{decision.element_id}' requested a trip "
                    "but no explicit breaker resolver is configured."
                )
                continue
            breaker_id = self._breaker_resolver(decision)
            if not isinstance(breaker_id, str) or not breaker_id.strip():
                diagnostics.append(
                    f"Protection decision '{decision.element_id}' has no valid breaker target."
                )
                continue
            command = TripBreakerCommand(
                breaker_id=breaker_id.strip(),
                causation_id=decision.metadata.get("command_id")
                if isinstance(decision.metadata.get("command_id"), object)
                else None,
            )
            commands.append(command)
            try:
                results.append(self._command_executor(command))
            except Exception as exc:
                diagnostics.append(
                    f"Protection trip execution failed for '{breaker_id.strip()}': {exc}"
                )

        return ProtectionExecutionResult(
            decisions=decision_tuple,
            trip_commands=tuple(commands),
            application_results=tuple(results),
            diagnostics=tuple(diagnostics),
        )


__all__ = ["ProtectionExecutionResult", "ProtectionExecutionService"]
