"""Application-owned lifecycle orchestration for one Control cycle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.control.context import ControlExecutionContext
from core.control.engine import ControlEngine, ControlEvaluationResult

from .control_execution import ControlExecutionResult, ControlExecutionService


@dataclass(frozen=True, slots=True)
class ControlDiagnostic:
    """Structured diagnostic retaining its Control-cycle provenance."""

    stage: str
    message: str
    control_id: str | None = None

    def __post_init__(self) -> None:
        if self.stage not in {"evaluation", "blocked", "execution"}:
            raise ValueError("stage must be evaluation, blocked, or execution.")
        if not self.message:
            raise ValueError("message must not be empty.")
        if self.control_id is not None and not self.control_id:
            raise ValueError("control_id must not be empty when provided.")


@dataclass(frozen=True, slots=True)
class ControlCycleResult:
    """Immutable combined report for one evaluate-and-execute cycle."""

    evaluation: ControlEvaluationResult
    execution: ControlExecutionResult

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation, ControlEvaluationResult):
            raise TypeError("evaluation must be a ControlEvaluationResult.")
        if not isinstance(self.execution, ControlExecutionResult):
            raise TypeError("execution must be a ControlExecutionResult.")

        evaluation_by_id = {
            decision.control_id: decision for decision in self.evaluation.decisions
        }
        for decision in self.evaluation.blocked_actions:
            evaluation_by_id[decision.control_id] = decision

        outcome_sets = (
            self.execution.executed_decisions,
            self.execution.failed_decisions,
            self.execution.invalid_decisions,
            self.execution.blocked_decisions,
        )
        seen_outcomes: dict[str, str] = {}
        outcome_names = ("executed", "failed", "invalid", "blocked")

        for name, decisions in zip(outcome_names, outcome_sets, strict=True):
            for decision in decisions:
                originating = evaluation_by_id.get(decision.control_id)
                if originating is None or originating != decision:
                    raise ValueError(
                        f"{name} decisions must originate from evaluation."
                    )
                if decision.simulation_time != self.evaluation.simulation_time:
                    raise ValueError(
                        "execution decision simulation_time must match evaluation simulation_time."
                    )
                previous = seen_outcomes.get(decision.control_id)
                if previous is not None:
                    raise ValueError(
                        f"Control decision cannot appear in multiple execution outcome "
                        f"categories: {previous}, {name}."
                    )
                seen_outcomes[decision.control_id] = name

        evaluation_blocked = tuple(
            decision.control_id for decision in self.evaluation.blocked_actions
        )
        execution_blocked = tuple(
            decision.control_id for decision in self.execution.blocked_decisions
        )
        if evaluation_blocked != execution_blocked:
            raise ValueError(
                "blocked_decisions must match evaluation.blocked_actions in order."
            )

    @property
    def simulation_time(self) -> float:
        return self.evaluation.simulation_time

    @property
    def evaluation_diagnostics(self) -> tuple[str, ...]:
        """Diagnostics produced while evaluating Control intent."""
        return self.evaluation.diagnostics

    @property
    def blocked_diagnostics(self) -> tuple[tuple[str, str], ...]:
        """Blocked/interlock diagnostics keyed to their originating Control ID."""
        return tuple(
            (decision.control_id, decision.diagnostic)
            for decision in self.execution.blocked_decisions
            if decision.diagnostic
        )

    @property
    def execution_diagnostics(self) -> tuple[str, ...]:
        """Diagnostics produced while dispatching commands through Application."""
        return self.execution.diagnostics

    @property
    def execution_failure_diagnostics(self) -> tuple[tuple[str, str], ...]:
        """Application execution failures keyed to their originating Control ID."""
        failed_ids = tuple(decision.control_id for decision in self.execution.failed_decisions)
        diagnostics = self.execution.diagnostics
        return tuple(zip(failed_ids, diagnostics, strict=False))

    @property
    def diagnostic_records(self) -> tuple[ControlDiagnostic, ...]:
        """Return all cycle diagnostics with explicit provenance."""
        records = [
            ControlDiagnostic(stage="evaluation", message=message)
            for message in self.evaluation.diagnostics
        ]
        records.extend(
            ControlDiagnostic(
                stage="blocked",
                control_id=control_id,
                message=message,
            )
            for control_id, message in self.blocked_diagnostics
        )
        records.extend(
            ControlDiagnostic(
                stage="execution",
                control_id=control_id,
                message=message,
            )
            for control_id, message in self.execution_failure_diagnostics
        )
        return tuple(records)

    @property
    def diagnostics(self) -> tuple[str, ...]:
        """Backward-compatible flattened diagnostics view."""
        return self.evaluation.diagnostics + self.execution.diagnostics


class ControlCycleService:
    """Coordinate Control evaluation and Application command execution."""

    def __init__(
        self,
        control_engine: ControlEngine,
        execution_service: ControlExecutionService,
    ) -> None:
        if not isinstance(control_engine, ControlEngine):
            raise TypeError("control_engine must be a ControlEngine.")
        if not isinstance(execution_service, ControlExecutionService):
            raise TypeError("execution_service must be a ControlExecutionService.")
        self._control_engine = control_engine
        self._execution_service = execution_service

    @property
    def control_engine(self) -> ControlEngine:
        return self._control_engine

    @property
    def execution_service(self) -> ControlExecutionService:
        return self._execution_service

    def execute(
        self,
        *,
        simulation_time: float | None = None,
        external_inputs: Mapping[str, Mapping[str, Any]] | None = None,
        context: ControlExecutionContext | None = None,
        interlock_inputs: Mapping[str, Mapping[str, bool]] | None = None,
    ) -> ControlCycleResult:
        """Evaluate Control intent, then execute only permitted decisions."""
        evaluation = self._control_engine.evaluate(
            simulation_time=simulation_time,
            external_inputs=external_inputs,
            context=context,
            interlock_inputs=interlock_inputs,
        )
        execution = self._execution_service.execute(evaluation)
        return ControlCycleResult(evaluation=evaluation, execution=execution)


__all__ = ["ControlDiagnostic", "ControlCycleResult", "ControlCycleService"]
