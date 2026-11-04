"""Deterministic numeric comparators for the headless Logic Control branch."""

from __future__ import annotations

import math
from typing import Sequence

from ..measurement_input import ControlInput
from ..base import ControlSignal, Inputs, SignalRole, State
from .base import LogicControlComponent, LogicControlResult


class UndervoltageComparator(LogicControlComponent):
    """Assert a Boolean trip output when a numeric voltage is below pickup."""

    def __init__(self, component_id: str, *, pickup: float, pickup_unit: str | None = None) -> None:
        component_id = str(component_id).strip()
        if not component_id:
            raise ValueError("UndervoltageComparator component_id cannot be empty.")
        pickup = float(pickup)
        if not math.isfinite(pickup):
            raise ValueError("UndervoltageComparator pickup must be finite.")
        self._component_id = component_id
        self._pickup = pickup
        if pickup_unit is not None:
            pickup_unit = str(pickup_unit).strip()
            if pickup_unit.casefold() not in {"v", "kv", "mv", "pu"}:
                raise ValueError("UndervoltageComparator pickup_unit must be V, kV, mV or pu.")
        self._pickup_unit = pickup_unit

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
        if not control_input.is_usable_at(
            simulation_time,
            require_freshness=True,
        ):
            raise ValueError(
                f"ControlInput '{control_input.source_id}' is unavailable, invalid, "
                "future-dated, stale, or missing a timestamp for undervoltage evaluation."
            )
        if control_input.signal_type is None or control_input.signal_type.value != "VOLTAGE":
            actual = control_input.signal_type.value if control_input.signal_type is not None else "unspecified"
            raise TypeError(
                f"ControlInput '{control_input.source_id}' has signal type "
                f"{actual}; VOLTAGE is required."
            )
        if control_input.phase.value == "NONE":
            raise ValueError(
                f"UndervoltageComparator requires an explicit voltage phase/basis for "
                f"Measurement '{control_input.source_id}'."
            )
        if self._pickup_unit is None:
            raise ValueError(
                "UndervoltageComparator requires pickup_unit so the pickup and measurement "
                "use the same engineering basis."
            )
        if control_input.unit.strip().casefold() != self._pickup_unit.casefold():
            raise ValueError(
                f"UndervoltageComparator pickup unit is {self._pickup_unit!r}, but Measurement "
                f"'{control_input.source_id}' uses {control_input.unit!r}; implicit conversion is not permitted."
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
        logic_state = dict(diagnostics.pop("logic_state", {}))
        logic_events = tuple(diagnostics.pop("logic_events", ()))
        return LogicControlResult(
            outputs=result.outputs,
            state=logic_state,
            time=result.time,
            events=logic_events,
            diagnostics=diagnostics,
        )


__all__ = ["UndervoltageComparator"]
