"""Control orchestration over the existing deterministic LogicEngine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .action import ControlActionBinding
from .decision import ControlDecision
from .logic.engine import LogicEngine, LogicEngineResult


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

    This class deliberately does not own time, mutate Core, access Network,
    execute commands, or touch UI. Simulation supplies the evaluation time.
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
        """Register one output-to-action binding."""
        if not isinstance(binding, ControlActionBinding):
            raise TypeError("binding must be a ControlActionBinding.")
        if binding in self._bindings:
            return
        self._bindings = (*self._bindings, binding)

    def evaluate(
        self,
        *,
        simulation_time: float,
        external_inputs: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> ControlEvaluationResult:
        """Evaluate logic once and convert asserted action bindings to intent."""
        logic_result = self._logic_engine.evaluate(
            time=simulation_time,
            external_inputs=external_inputs,
        )
        decisions: list[ControlDecision] = []
        diagnostics: list[str] = []
        for binding in self._bindings:
            outputs = logic_result.signals.get(binding.source_component, {})
            if outputs.get(binding.source_output) is True:
                decisions.append(binding.decision(simulation_time=simulation_time))
        return ControlEvaluationResult(
            simulation_time=simulation_time,
            decisions=tuple(decisions),
            diagnostics=tuple(diagnostics),
            logic_result=logic_result,
        )


__all__ = ["ControlEngine", "ControlEvaluationResult"]
