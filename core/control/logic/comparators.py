"""Deterministic numeric comparators for the headless Logic Control branch."""

from __future__ import annotations

import math
from typing import Sequence

from ..measurement_input import ControlInput
from ...base import ControlSignal, Inputs, SignalRole, State
from .base import LogicControlComponent, LogicControlResult


class UndervoltageComparator(LogicControlComponent):
    """Assert a Boolean trip output when a numeric voltage is below pickup.

    The comparator is deliberately electrical-model agnostic. The caller
    supplies the resolved engineering value through ``ControlInput`` or the
    normal LogicEngine input mapping; Core equipment/network objects are not
    retained or mutated here.
    """

    def __init__(self, component_id: str, *, pickup: float) -> None:
        component_id = str(component_id).strip()
        if not component_id:
            raise ValueError("UndervoltageComparator component_id cannot be empty.")
        pickup = float(pickup)
        if not math.isfinite(pickup):
            raise ValueError("UndervoltageComparator pickup must be finite.")
        self._component_id = component_id
        self._pickup = pickup

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "undervoltage_comparator"

    @property
    def pickup(self) -> float:
        return self._pickup

    def input_definition(self) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="VALUE",
                role=SignalRole.INPUT,
                description="Resolved voltage engineering value.",
                value_type=float,
            ),
        )

    def output_definition(self) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="TRIP",
                role=SignalRole.OUTPUT,
                description="Undervoltage pickup assertion.",
                value_type=bool,
            ),
        )

    def evaluate_logic(self, state: State, inputs: Inputs, time: float) -> LogicControlResult:
        del state
        value = inputs["VALUE"]
        if isinstance(value, bool):
            raise TypeError("UndervoltageComparator VALUE cannot be bool.")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("UndervoltageComparator VALUE must be finite.")
        return LogicControlResult(
            outputs={"TRIP": value < self._pickup},
            state={},
            time=time,
            diagnostics={
                "pickup": self._pickup,
                "value": value,
            },
        )

    def evaluate_input(self, control_input: ControlInput, *, simulation_time: float) -> LogicControlResult:
        """Evaluate one canonical, detached Measurement-to-Control input."""
        if not isinstance(control_input, ControlInput):
            raise TypeError("control_input must be a ControlInput.")
        if not control_input.is_usable:
            raise ValueError(
                f"ControlInput '{control_input.source_id}' is not usable for undervoltage evaluation."
            )
        if isinstance(control_input.value, complex):
            raise TypeError("UndervoltageComparator requires a real numeric ControlInput value.")
        result = self.evaluate(
            self.initial_state(),
            {"VALUE": float(control_input.value)},
            simulation_time,
        )
        diagnostics = dict(result.diagnostics)
        diagnostics["source_id"] = control_input.source_id
        diagnostics["unit"] = control_input.unit
        return LogicControlResult(
            outputs=result.outputs,
            state=result.state,
            time=result.time,
            events=result.events,
            diagnostics=diagnostics,
        )


__all__ = ["UndervoltageComparator"]
