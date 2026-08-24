"""
GridForge V2 - XOR Logic Gate
==============================

Author:
    Subhendu Mishra

File:
    core/control/logic/gates/xor_gate.py

Purpose
-------
Headless Boolean XOR gate for the Logic Control domain.

The gate is stateless and deterministic.

UI logic-layout/editing concerns remain outside Core Control.
"""

from __future__ import annotations

from typing import Sequence

from ...base import (
    ControlSignal,
    SignalRole,
    Inputs,
    State,
)
from ..base import (
    LogicControlComponent,
    LogicControlResult,
)


class XORGate(LogicControlComponent):
    """
    Boolean XOR gate.

    Inputs:
        A
        B

    Output:
        OUT

    Semantics:
        OUT = A XOR B

    Truth table:

        A     B     OUT
        ----------------
        False False False
        False True  True
        True  False True
        True  True  False
    """

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "xor_gate"

    def __init__(
        self,
        component_id: str,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "XORGate component_id cannot be empty."
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
                description="Boolean XOR result.",
                value_type=bool,
            ),
        )

    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        normalized = self.validate_logic_inputs(
            inputs
        )

        output = (
            normalized["A"]
            != normalized["B"]
        )

        return LogicControlResult(
            outputs={
                "OUT": output,
            },
            state={},
            time=time,
        )


__all__ = [
    "XORGate",
]
