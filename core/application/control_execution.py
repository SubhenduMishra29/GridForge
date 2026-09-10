"""Application orchestration for executing evaluated Control decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.control.decision import ControlDecision
from core.control.engine import ControlEvaluationResult

from .control_dispatch import ControlCommandDispatcher
from .results import ApplicationResult


@dataclass(frozen=True, slots=True)
class ControlExecutionResult:
    """Immutable outcome of one Application-side Control execution cycle."""

    executed_decisions: tuple[ControlDecision, ...] = ()
    invalid_decisions: tuple[ControlDecision, ...] = ()
    blocked_decisions: tuple[ControlDecision, ...] = ()
    failed_decisions: tuple[ControlDecision, ...] = ()
    application_results: tuple[ApplicationResult[Any], ...] = ()
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "executed_decisions", tuple(self.executed_decisions))
        object.__setattr__(self, "invalid_decisions", tuple(self.invalid_decisions))
        object.__setattr__(self, "blocked_decisions", tuple(self.blocked_decisions))
        object.__setattr__(self, "failed_decisions", tuple(self.failed_decisions))
        object.__setattr__(self, "application_results", tuple(self.application_results))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))


class ControlExecutionService:
    """Execute permitted Control intent through the existing command boundary.

    This service deliberately lives in Application. Control remains an intent
    producer and never reaches Core equipment or Network mutation itself.
    """

    def __init__(self, dispatcher: ControlCommandDispatcher) -> None:
        if not isinstance(dispatcher, ControlCommandDispatcher):
            raise TypeError("dispatcher must be a ControlCommandDispatcher.")
        self._dispatcher = dispatcher

    @property
    def dispatcher(self) -> ControlCommandDispatcher:
        """Return the configured Control command dispatcher."""
        return self._dispatcher

    def execute(self, evaluation: ControlEvaluationResult) -> ControlExecutionResult:
        """Dispatch valid decisions while preserving every execution outcome.

        Blocked evaluation actions and invalid decisions are reported separately
        and are never dispatched. A failed Application command is recorded as
        an execution failure and does not suppress later deterministic intents.
        """
        if not isinstance(evaluation, ControlEvaluationResult):
            raise TypeError("evaluation must be a ControlEvaluationResult.")

        executed: list[ControlDecision] = []
        invalid: list[ControlDecision] = []
        failed: list[ControlDecision] = []
        results: list[ApplicationResult[Any]] = []
        diagnostics: list[str] = []

        for decision in evaluation.decisions:
            if not decision.valid:
                invalid.append(decision)
                continue

            try:
                result = self._dispatcher.execute(decision)
            except Exception as exc:
                failed.append(decision)
                diagnostics.append(
                    f"Control '{decision.control_id}' execution failed: {exc}"
                )
                continue

            executed.append(decision)
            results.append(result)

        return ControlExecutionResult(
            executed_decisions=tuple(executed),
            invalid_decisions=tuple(invalid),
            blocked_decisions=tuple(evaluation.blocked_actions),
            failed_decisions=tuple(failed),
            application_results=tuple(results),
            diagnostics=tuple(diagnostics),
        )


__all__ = ["ControlExecutionResult", "ControlExecutionService"]
