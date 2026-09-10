"""Application-owned lifecycle orchestration for one Control cycle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.control.context import ControlExecutionContext
from core.control.engine import ControlEngine, ControlEvaluationResult

from .control_execution import ControlExecutionResult, ControlExecutionService


@dataclass(frozen=True, slots=True)
class ControlCycleResult:
    """Immutable combined report for one evaluate-and-execute cycle."""

    evaluation: ControlEvaluationResult
    execution: ControlExecutionResult

    @property
    def simulation_time(self) -> float:
        return self.evaluation.simulation_time

    @property
    def diagnostics(self) -> tuple[str, ...]:
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


__all__ = ["ControlCycleResult", "ControlCycleService"]
