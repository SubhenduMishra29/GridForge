"""
GridForge V2 - OR Logic Gate
============================

Author:
    Subhendu Mishra

File:
    core/control/logic/gates/or_gate.py

Purpose
-------
Headless Boolean OR gate for the Logic Control domain.

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


class ORGate(LogicControlComponent):
    """Two-input Boolean OR gate."""

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "or_gate"

    def __init__(self, component_id: str) -> None:
        component_id = str(component_id).strip()

        if not component_id:
            raise ValueError(
                "ORGate component_id cannot be empty."
            )

        self._component_id = component_id

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="A",
                role=SignalRole.INPUT,
                description="First Boolean input.",
                value_type=bool,
            ),
            ControlSignal(
                name="B",
                role=SignalRole.INPUT,
                description="Second Boolean input.",
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
                description="Boolean OR result.",
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
                "OUT": (
                    normalized["A"]
                    or normalized["B"]
                ),
            },
            state={},
            time=time,
        )


__all__ = ["ORGate"]
