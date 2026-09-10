"""Control orchestration over the existing deterministic LogicEngine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .action import ControlActionBinding
from .context import ControlExecutionContext
from .decision import ControlActionType, ControlDecision
from .logic.engine import LogicEngine, LogicEngineResult


_ACTION_PRIORITY = {
    ControlActionType.TRIP: 400,
    ControlActionType.OPEN: 300,
    ControlActionType.CLOSE: 200,
    ControlActionType.TAKE_OUT_OF_SERVICE: 100,
    ControlActionType.PUT_IN_SERVICE: 50,
}


@dataclass(frozen=True, slots=True)
class ControlEvaluationResult:
    """Immutable result of one Control evaluation cycle."""

    simulation_time: float
    decisions: tuple[ControlDecision, ...] = ()
    blocked_actions: tuple[ControlDecision, ...] = ()
    diagnostics: tuple[str, ...] = ()
    logic_result: LogicEngineResult | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "simulation_time", float(self.simulation_time))
        object.__setattr__(self, "decisions", tuple(self.decisions))
        object.__setattr__(self, "blocked_actions", tuple(self.blocked_actions))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))
        object.__setattr__(self, "metadata", dict(self.metadata))


class ControlEngine:
    """Coordinate logic evaluation and produce equipment-action intents.

    This class does not own time, mutate Core, access Network, execute
    commands, or touch UI. The Simulation layer supplies a context snapshot.
    """

    def __init__(self, logic_engine: LogicEngine) -> None:
        if not isinstance(logic_engine, LogicEngine):
            raise TypeError("logic_engine must be a LogicEngine.")
        self._logic_engine = logic_engine
        self._bindings: tuple[ControlActionBinding, ...] = ()

    @property
    def logic_engine(self) -> LogicEngine:
        return self._logic_engine

    @property
    def bindings(self) -> tuple[ControlActionBinding, ...]:
        return self._bindings

    def bind_action(self, binding: ControlActionBinding) -> None:
        """Register one output-to-action binding and validate its source."""
        if not isinstance(binding, ControlActionBinding):
            raise TypeError("binding must be a ControlActionBinding.")
        if binding in self._bindings:
            return
        component = self._logic_engine.get(binding.source_component)
        output_names = set(component.output_names)
        if binding.source_output not in output_names:
            raise ValueError(
                f"Unknown Control output '{binding.source_component}.{binding.source_output}'."
            )
        self._bindings = (*self._bindings, binding)

    def evaluate(
        self,
        *,
        simulation_time: float | None = None,
        external_inputs: Mapping[str, Mapping[str, Any]] | None = None,
        context: ControlExecutionContext | None = None,
    ) -> ControlEvaluationResult:
        """Evaluate logic at supplied simulation time and emit deterministic intents."""
        if context is not None:
            if simulation_time is not None or external_inputs is not None:
                raise ValueError("context cannot be combined with simulation_time or external_inputs.")
        else:
            if simulation_time is None:
                raise ValueError("simulation_time or context is required.")
            context = ControlExecutionContext(
                simulation_time=simulation_time,
                external_inputs=external_inputs or {},
            )

        logic_result = self._logic_engine.evaluate(
            time=context.simulation_time,
            external_inputs=context.external_inputs,
        )
        candidates: list[ControlDecision] = []
        for binding in self._bindings:
            outputs = logic_result.signals.get(binding.source_component, {})
            if outputs.get(binding.source_output) is True:
                candidates.append(binding.decision(simulation_time=context.simulation_time))

        decisions: list[ControlDecision] = []
        blocked: list[ControlDecision] = []
        diagnostics: list[str] = []
        winners: dict[str, ControlDecision] = {}
        for decision in sorted(
            candidates,
            key=lambda item: (
                -_ACTION_PRIORITY[item.action_type],
                item.control_id,
                item.triggered_by or "",
            ),
        ):
            current = winners.get(decision.target_equipment_id)
            if current is None:
                winners[decision.target_equipment_id] = decision
                decisions.append(decision)
                continue
            blocked.append(
                ControlDecision.blocked(
                    control_id=decision.control_id,
                    action_type=decision.action_type,
                    target_equipment_id=decision.target_equipment_id,
                    reason=decision.reason,
                    simulation_time=context.simulation_time,
                    diagnostic=(
                        f"Action conflicts with {current.control_id}; "
                        f"{current.action_type.value} has higher priority."
                    ),
                )
            )
            diagnostics.append(
                f"{decision.target_equipment_id}: {decision.action_type.value} "
                f"blocked by {current.action_type.value} from {current.control_id}."
            )

        return ControlEvaluationResult(
            simulation_time=context.simulation_time,
            decisions=tuple(decisions),
            blocked_actions=tuple(blocked),
            diagnostics=tuple(diagnostics),
            logic_result=logic_result,
            metadata=context.metadata,
        )


__all__ = ["ControlEngine", "ControlEvaluationResult"]
