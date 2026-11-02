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
    """Immutable outcome; execution is not physical acknowledgement."""

    executed_decisions: tuple[ControlDecision, ...] = ()
    acknowledged_decisions: tuple[ControlDecision, ...] = ()
    mismatched_decisions: tuple[ControlDecision, ...] = ()
    invalid_decisions: tuple[ControlDecision, ...] = ()
    blocked_decisions: tuple[ControlDecision, ...] = ()
    failed_decisions: tuple[ControlDecision, ...] = ()
    application_results: tuple[ApplicationResult[Any], ...] = ()
    diagnostics: tuple[str, ...] = ()
    failure_diagnostics: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "executed_decisions", "acknowledged_decisions", "mismatched_decisions",
            "invalid_decisions", "blocked_decisions", "failed_decisions",
            "application_results",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))
        pairs = tuple((str(control_id), str(message)) for control_id, message in self.failure_diagnostics)
        if any(not control_id or not message for control_id, message in pairs):
            raise ValueError("failure_diagnostics entries require a control ID and diagnostic.")
        object.__setattr__(self, "failure_diagnostics", pairs)
        categories = {
            "executed": self.executed_decisions,
            "failed": self.failed_decisions,
            "invalid": self.invalid_decisions,
            "blocked": self.blocked_decisions,
        }
        seen: dict[str, str] = {}
        for name, decisions in categories.items():
            for decision in decisions:
                if not isinstance(decision, ControlDecision):
                    raise TypeError(f"{name}_decisions must contain ControlDecision values.")
                if name in {"executed", "failed"} and not decision.valid:
                    raise ValueError(f"{name} decisions must be valid evaluated intents.")
                if name in {"invalid", "blocked"} and decision.valid:
                    raise ValueError(f"{name} decisions must be invalid.")
                previous = seen.get(decision.control_id)
                if previous is not None:
                    raise ValueError(f"Decision {decision.control_id!r} appears in both {previous} and {name}.")
                seen[decision.control_id] = name
        feedback_seen: dict[str, str] = {}
        for name, decisions in (("acknowledged", self.acknowledged_decisions), ("mismatched", self.mismatched_decisions)):
            for decision in decisions:
                if not isinstance(decision, ControlDecision):
                    raise TypeError(f"{name}_decisions must contain ControlDecision values.")
                if not decision.valid:
                    raise ValueError(f"{name} decisions must reference valid dispatched intent.")
                if decision.control_id not in {item.control_id for item in self.executed_decisions}:
                    raise ValueError(f"{name} decisions must reference successfully executed decisions.")
                previous = feedback_seen.get(decision.control_id)
                if previous is not None:
                    raise ValueError(f"Decision {decision.control_id!r} has contradictory feedback states.")
                feedback_seen[decision.control_id] = name
        failed_ids = {item.control_id for item in self.failed_decisions}
        attributed_ids = {control_id for control_id, _ in self.failure_diagnostics}
        unexpected_attributions = attributed_ids - failed_ids
        if unexpected_attributions:
            raise ValueError(
                "failure_diagnostics must reference failed decisions only; "
                f"unexpected control IDs={sorted(unexpected_attributions)}."
            )
        if len(attributed_ids) != len(self.failure_diagnostics):
            raise ValueError("failure_diagnostics must contain at most one record per control ID.")
        missing_attributions = failed_ids - attributed_ids
        if missing_attributions:
            raise ValueError(
                "Every failed decision must have exactly one failure diagnostic; "
                f"missing control IDs={sorted(missing_attributions)}."
            )


class ControlExecutionService:
    """Execute permitted Control intent through the existing command boundary."""

    def __init__(self, dispatcher: ControlCommandDispatcher) -> None:
        if not isinstance(dispatcher, ControlCommandDispatcher):
            raise TypeError("dispatcher must be a ControlCommandDispatcher.")
        self._dispatcher = dispatcher

    @property
    def dispatcher(self) -> ControlCommandDispatcher:
        return self._dispatcher

    def execute(self, evaluation: ControlEvaluationResult) -> ControlExecutionResult:
        """Execute coordinated breaker trips atomically; dispatch other intents normally."""
        if not isinstance(evaluation, ControlEvaluationResult):
            raise TypeError("evaluation must be a ControlEvaluationResult.")
        executed: list[ControlDecision] = []
        invalid: list[ControlDecision] = [
            item for item in evaluation.decisions if not item.valid
        ]
        failed: list[ControlDecision] = []
        results: list[ApplicationResult[Any]] = []
        diagnostics: list[str] = []
        failure_diagnostics: list[tuple[str, str]] = []
        valid = tuple(item for item in evaluation.decisions if item.valid)
        trip_batch = tuple(
            item for item in valid
            if item.target_equipment_type == "breaker"
            and item.action_type.value == "trip"
        )
        batched_ids = {item.control_id for item in trip_batch}
        if len(trip_batch) >= 2:
            try:
                result = self._dispatcher.execute_trip_batch(trip_batch)
                if not isinstance(result, ApplicationResult):
                    raise TypeError(
                        "Trip batch dispatcher returned "
                        f"{type(result).__name__}, not ApplicationResult."
                    )
                results.append(result)
                executed.extend(trip_batch)
            except Exception as exc:
                for decision in trip_batch:
                    failed.append(decision)
                    message = (
                        f"Control '{decision.control_id}' coordinated trip batch "
                        f"rolled back: {exc}"
                    )
                    diagnostics.append(message)
                    failure_diagnostics.append((decision.control_id, message))
        for decision in valid:
            if decision.control_id in batched_ids:
                continue
            try:
                result = self._dispatcher.execute(decision)
                if not isinstance(result, ApplicationResult):
                    raise TypeError(
                        "Dispatcher returned "
                        f"{type(result).__name__}, not ApplicationResult."
                    )
                results.append(result)
                if result.success:
                    executed.append(decision)
                else:
                    failed.append(decision)
                    detail = result.message.strip() or (
                        "Application command reported failure without a diagnostic."
                    )
                    message = f"Control '{decision.control_id}' execution failed: {detail}"
                    diagnostics.append(message)
                    failure_diagnostics.append((decision.control_id, message))
            except Exception as exc:
                failed.append(decision)
                message = f"Control '{decision.control_id}' execution failed: {exc}"
                diagnostics.append(message)
                failure_diagnostics.append((decision.control_id, message))
        return ControlExecutionResult(
            executed_decisions=tuple(executed),
            invalid_decisions=tuple(invalid),
            blocked_decisions=tuple(evaluation.blocked_actions),
            failed_decisions=tuple(failed),
            application_results=tuple(results),
            diagnostics=tuple(diagnostics),
            failure_diagnostics=tuple(failure_diagnostics),
        )

__all__ = ["ControlExecutionResult", "ControlExecutionService"]
