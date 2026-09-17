"""Application-owned lifecycle orchestration for one Control cycle.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.control.context import ControlExecutionContext
from core.control.engine import ControlEngine, ControlEvaluationResult

from .control_execution import ControlExecutionResult, ControlExecutionService
from .control_signal_mapping import ControlSignalMapping
from .read_service import ReadService


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
                    raise ValueError(f"{name} decisions must originate from evaluation.")
                if decision.simulation_time != self.evaluation.simulation_time:
                    raise ValueError("execution decision simulation_time must match evaluation simulation_time.")
                previous = seen_outcomes.get(decision.control_id)
                if previous is not None:
                    raise ValueError(
                        f"Control decision cannot appear in multiple execution outcome categories: {previous}, {name}."
                    )
                seen_outcomes[decision.control_id] = name

        evaluation_blocked = tuple(decision.control_id for decision in self.evaluation.blocked_actions)
        execution_blocked = tuple(decision.control_id for decision in self.execution.blocked_decisions)
        if evaluation_blocked != execution_blocked:
            raise ValueError("blocked_decisions must match evaluation.blocked_actions in order.")

    @property
    def simulation_time(self) -> float:
        return self.evaluation.simulation_time

    @property
    def evaluation_diagnostics(self) -> tuple[str, ...]:
        return self.evaluation.diagnostics

    @property
    def blocked_diagnostics(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (decision.control_id, decision.diagnostic)
            for decision in self.execution.blocked_decisions
            if decision.diagnostic
        )

    @property
    def execution_diagnostics(self) -> tuple[str, ...]:
        return self.execution.diagnostics

    @property
    def execution_failure_diagnostics(self) -> tuple[tuple[str, str], ...]:
        failed_ids = tuple(decision.control_id for decision in self.execution.failed_decisions)
        return tuple(zip(failed_ids, self.execution.diagnostics, strict=False))

    @property
    def diagnostic_records(self) -> tuple[ControlDiagnostic, ...]:
        records = [ControlDiagnostic(stage="evaluation", message=message) for message in self.evaluation.diagnostics]
        records.extend(
            ControlDiagnostic(stage="blocked", control_id=control_id, message=message)
            for control_id, message in self.blocked_diagnostics
        )
        records.extend(
            ControlDiagnostic(stage="execution", control_id=control_id, message=message)
            for control_id, message in self.execution_failure_diagnostics
        )
        return tuple(records)

    @property
    def diagnostics(self) -> tuple[str, ...]:
        return self.evaluation.diagnostics + self.execution.diagnostics


class ControlCycleService:
    """Coordinate Application signal resolution, Control evaluation, and command execution."""

    def __init__(
        self,
        control_engine: ControlEngine,
        execution_service: ControlExecutionService,
        *,
        signal_mapping: ControlSignalMapping | None = None,
        read_service: ReadService | None = None,
    ) -> None:
        if not isinstance(control_engine, ControlEngine):
            raise TypeError("control_engine must be a ControlEngine.")
        if not isinstance(execution_service, ControlExecutionService):
            raise TypeError("execution_service must be a ControlExecutionService.")
        if signal_mapping is not None and not isinstance(signal_mapping, ControlSignalMapping):
            raise TypeError("signal_mapping must be a ControlSignalMapping or None.")
        if signal_mapping is not None and not isinstance(read_service, ReadService):
            raise TypeError("read_service is required when signal_mapping is configured.")
        self._control_engine = control_engine
        self._execution_service = execution_service
        self._signal_mapping = signal_mapping
        self._read_service = read_service

    @property
    def control_engine(self) -> ControlEngine:
        return self._control_engine

    @property
    def execution_service(self) -> ControlExecutionService:
        return self._execution_service

    @property
    def signal_mapping(self) -> ControlSignalMapping | None:
        return self._signal_mapping

    def execute(
        self,
        *,
        simulation_time: float | None = None,
        external_inputs: Mapping[str, Mapping[str, Any]] | None = None,
        context: ControlExecutionContext | None = None,
        interlock_inputs: Mapping[str, Mapping[str, bool]] | None = None,
    ) -> ControlCycleResult:
        """Resolve engineering inputs when configured, then evaluate and execute Control intent."""
        if self._signal_mapping is not None:
            if context is not None or external_inputs is not None:
                raise ValueError("signal_mapping cannot be combined with context or external_inputs.")
            if simulation_time is None:
                raise ValueError("simulation_time is required when signal_mapping is configured.")
            resolved = self._signal_mapping.resolve(self._read_service)  # type: ignore[arg-type]
            context = ControlExecutionContext(
                simulation_time=simulation_time,
                external_inputs=resolved.external_inputs,
                metadata={"control_signal_bindings": resolved.bindings},
            )

        evaluation = self._control_engine.evaluate(
            simulation_time=simulation_time,
            external_inputs=external_inputs,
            context=context,
            interlock_inputs=interlock_inputs,
        )
        execution = self._execution_service.execute(evaluation)
        return ControlCycleResult(evaluation=evaluation, execution=execution)


__all__ = ["ControlDiagnostic", "ControlCycleResult", "ControlCycleService"]
