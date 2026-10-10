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

        evaluation_by_id = {}
        for decision in (*self.evaluation.decisions, *self.evaluation.blocked_actions):
            if decision.control_id in evaluation_by_id:
                raise ValueError(f"Evaluation contains duplicate decision identity {decision.control_id!r}.")
            if decision.simulation_time != self.evaluation.simulation_time:
                raise ValueError("Evaluated decision simulation_time must match evaluation simulation_time.")
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

        expected_ids = {decision.control_id for decision in self.evaluation.decisions}
        reported_ids = {
            decision.control_id
            for category in (
                self.execution.executed_decisions,
                self.execution.failed_decisions,
                self.execution.invalid_decisions,
            )
            for decision in category
        }
        if expected_ids != reported_ids:
            missing = sorted(expected_ids - reported_ids)
            unexpected = sorted(reported_ids - expected_ids)
            raise ValueError(
                f"Execution outcomes must account for every evaluated decision; missing={missing}, unexpected={unexpected}."
            )

        if self.execution.blocked_decisions != self.evaluation.blocked_actions:
            raise ValueError("blocked_decisions must match evaluation.blocked_actions in identity, content, and order.")

        executed_by_id = {item.control_id: item for item in self.execution.executed_decisions}
        for category_name, feedback in (
            ("acknowledged", self.execution.acknowledged_decisions),
            ("mismatched", self.execution.mismatched_decisions),
        ):
            feedback_ids: set[str] = set()
            for decision in feedback:
                if decision.control_id in feedback_ids:
                    raise ValueError(f"{category_name} feedback contains duplicate decision identity {decision.control_id!r}.")
                feedback_ids.add(decision.control_id)
                if executed_by_id.get(decision.control_id) != decision:
                    raise ValueError(f"{category_name} feedback must reference the exact successfully executed decision.")
                if decision.simulation_time != self.evaluation.simulation_time:
                    raise ValueError(f"{category_name} feedback simulation_time must match evaluation simulation_time.")

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
        if self.execution.failure_diagnostics:
            return self.execution.failure_diagnostics
        # Legacy results have no structured association. Do not guess which
        # failure a free-form diagnostic belongs to by positional pairing.
        return ()

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
        interlock_inputs: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
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
                metadata={
                    "control_signal_bindings": resolved.bindings,
                    "control_interlock_inputs": resolved.interlock_inputs,
                },
            )
            # Keep ordinary logic inputs and freshness-bearing interlock inputs
            # separate. Route only mapped envelopes to the interlocks attached
            # to the corresponding action binding.
            if interlock_inputs is not None:
                raise ValueError("interlock_inputs cannot be combined with signal_mapping.")
            mapped = resolved.interlock_inputs
            interlock_inputs = {}
            for binding in self._control_engine.bindings:
                if binding.interlock_id is None:
                    continue
                values = mapped.get(binding.control_id, {})
                interlock_inputs.setdefault(binding.interlock_id, {}).update(values)

        if context is not None:
            # Context owns simulation time and ordinary inputs. Do not pass
            # mutually exclusive legacy arguments alongside it.
            evaluation = self._control_engine.evaluate(
                context=context,
                interlock_inputs=interlock_inputs,
            )
        else:
            # Preserve the legacy path for callers without an explicit context.
            evaluation = self._control_engine.evaluate(
                simulation_time=simulation_time,
                external_inputs=external_inputs,
                interlock_inputs=interlock_inputs,
            )
        execution = self._execution_service.execute(evaluation)
        return ControlCycleResult(evaluation=evaluation, execution=execution)


__all__ = ["ControlDiagnostic", "ControlCycleResult", "ControlCycleService"]
