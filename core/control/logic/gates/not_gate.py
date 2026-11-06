"""
GridForge V2 - NOT Logic Gate
=============================

Author:
    Subhendu Mishra

File:
    core/control/logic/gates/not_gate.py

Purpose
-------
Headless Boolean NOT gate for the Logic Control domain.

The gate is stateless and deterministic. UI/layout concerns remain
outside Core Control.
"""

from __future__ import annotations

from typing import Sequence

from ...base import (
    ControlSignal,
    Inputs,
    SignalRole,
    State,
)
from ..base import (
    LogicControlComponent,
    LogicControlResult,
)


class NOTGate(LogicControlComponent):
    """Single-input Boolean NOT gate."""

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "not_gate"

    def __init__(self, component_id: str) -> None:
        component_id = str(component_id).strip()

        if not component_id:
            raise ValueError(
                "NOTGate component_id cannot be empty."
            )

        self._component_id = component_id

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="IN",
                role=SignalRole.INPUT,
                description="Boolean input.",
                value_type=bool,
            ),
        )

    def output_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="OUT",
                role=SignalRole.OUTPUT,
                description="Boolean inverted result.",
                value_type=bool,
            ),
        )

    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        normalized = self.validate_logic_inputs(inputs)

        return LogicControlResult(
            outputs={
                "OUT": not normalized["IN"],
            },
            state={},
            time=time,
        )


__all__ = ["NOTGate"]
