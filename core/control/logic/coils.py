"""
GridForge V2 - Logic Coils
==========================

Author:
    Subhendu Mishra

File:
    core/control/logic/coils.py

Purpose
-------
Headless coil components for the Logic Control branch.

A coil represents the output actuator/state of a logic network.

Signal contract:

    IN  ->  OUT

Persistent state:

    energized : bool

The Core owns the authoritative state. The UI logic-layout/editing
canvas only represents the coil and its logical connections.
"""

from __future__ import annotations

from typing import Sequence

from ...base import (
    ControlSignal,
    Inputs,
    SignalRole,
    State,
)
from .base import (
    LogicControlComponent,
    LogicControlResult,
    LogicEvent,
    LogicEventType,
    LogicStateDefinition,
)


# ============================================================================
# LOGIC COIL
# ============================================================================


class LogicCoil(
    LogicControlComponent,
):
    """
    Boolean output coil.

    IN
        Boolean command supplied by the logic network.

    OUT
        Current Boolean coil state.

    energized
        Persistent Boolean state.

    The coil does not perform electrical calculations. Any physical
    actuator/equipment behavior belongs to the appropriate domain model
    or application service.
    """

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "coil"

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def __init__(
        self,
        component_id: str,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicCoil component_id cannot be empty."
            )

        self._component_id = component_id

    # ========================================================================
    # SIGNAL CONTRACT
    # ========================================================================

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="IN",
                role=SignalRole.INPUT,
                description=(
                    "Boolean coil command."
                ),
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
                description=(
                    "Current Boolean coil state."
                ),
                value_type=bool,
            ),
        )

    # ========================================================================
    # STATE CONTRACT
    # ========================================================================

    def logic_state_definition(
        self,
    ) -> Sequence[LogicStateDefinition]:
        return (
            LogicStateDefinition(
                name="energized",
                value_type=bool,
                default=False,
                description=(
                    "Persistent Boolean coil state."
                ),
            ),
        )

    # ========================================================================
    # RESET
    # ========================================================================

    def reset_logic(
        self,
    ) -> State:
        return {
            "energized": False,
        }

    def reset(
        self,
        inputs: Inputs | None = None,
    ) -> State:
        del inputs
        return self.reset_logic()

    # ========================================================================
    # EVALUATION
    # ========================================================================

    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        normalized_state = (
            self.validate_logic_state(
                state
            )
        )

        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        previous_energized = bool(
            normalized_state[
                "energized"
            ]
        )

        energized = bool(
            normalized_inputs[
                "IN"
            ]
        )

        events: list[
            LogicEvent
        ] = []

        if energized != previous_energized:
            events.append(
                LogicEvent(
                    event_type=(
                        LogicEventType.OUTPUT_CHANGED
                    ),
                    component_id=self.component_id,
                    signal_name="OUT",
                    previous_value=(
                        previous_energized
                    ),
                    current_value=energized,
                    time=time,
                    data={
                        "energized": energized,
                    },
                )
            )

            events.append(
                LogicEvent(
                    event_type=(
                        LogicEventType.STATE_CHANGED
                    ),
                    component_id=self.component_id,
                    signal_name="energized",
                    previous_value=(
                        previous_energized
                    ),
                    current_value=energized,
                    time=time,
                    data={
                        "energized": energized,
                    },
                )
            )

        return LogicControlResult(
            outputs={
                "OUT": energized,
            },
            state={
                "energized": energized,
            },
            time=time,
            events=tuple(
                events
            ),
            diagnostics={
                "energized": energized,
            },
        )


# ============================================================================
# SPECIALIZED COILS
# ============================================================================


class LogicSetCoil(
    LogicControlComponent,
):
    """
    Set-dominant coil.

    A TRUE input latches the output ON.

    RESET is intentionally not represented here; use LogicResetCoil or
    LogicLatch when explicit reset semantics are required.
    """

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "set_coil"

    def __init__(
        self,
        component_id: str,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicSetCoil component_id cannot be empty."
            )

        self._component_id = component_id

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="IN",
                role=SignalRole.INPUT,
                description=(
                    "Boolean set command."
                ),
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
                description=(
                    "Latched Boolean output."
                ),
                value_type=bool,
            ),
        )

    def logic_state_definition(
        self,
    ) -> Sequence[LogicStateDefinition]:
        return (
            LogicStateDefinition(
                name="energized",
                value_type=bool,
                default=False,
                description=(
                    "Persistent Boolean coil state."
                ),
            ),
        )

    def reset_logic(
        self,
    ) -> State:
        return {
            "energized": False,
        }

    def reset(
        self,
        inputs: Inputs | None = None,
    ) -> State:
        del inputs
        return self.reset_logic()

    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        normalized_state = (
            self.validate_logic_state(
                state
            )
        )

        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        previous = bool(
            normalized_state[
                "energized"
            ]
        )

        energized = (
            previous
            or bool(
                normalized_inputs[
                    "IN"
                ]
            )
        )

        events: list[
            LogicEvent
        ] = []

        if energized != previous:
            events.append(
                LogicEvent(
                    event_type=(
                        LogicEventType.OUTPUT_CHANGED
                    ),
                    component_id=self.component_id,
                    signal_name="OUT",
                    previous_value=previous,
                    current_value=energized,
                    time=time,
                )
            )

        return LogicControlResult(
            outputs={
                "OUT": energized,
            },
            state={
                "energized": energized,
            },
            time=time,
            events=tuple(
                events
            ),
            diagnostics={
                "energized": energized,
            },
        )


class LogicResetCoil(
    LogicControlComponent,
):
    """
    Reset-dominant coil.

    A TRUE input forces the output OFF.

    This component is useful when explicit reset semantics are required
    without introducing a separate latch component.
    """

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "reset_coil"

    def __init__(
        self,
        component_id: str,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicResetCoil component_id cannot be empty."
            )

        self._component_id = component_id

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="IN",
                role=SignalRole.INPUT,
                description=(
                    "Boolean reset command."
                ),
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
                description=(
                    "Boolean coil output."
                ),
                value_type=bool,
            ),
        )

    def logic_state_definition(
        self,
    ) -> Sequence[LogicStateDefinition]:
        return (
            LogicStateDefinition(
                name="energized",
                value_type=bool,
                default=False,
                description=(
                    "Persistent Boolean coil state."
                ),
            ),
        )

    def reset_logic(
        self,
    ) -> State:
        return {
            "energized": False,
        }

    def reset(
        self,
        inputs: Inputs | None = None,
    ) -> State:
        del inputs
        return self.reset_logic()

    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        normalized_state = (
            self.validate_logic_state(
                state
            )
        )

        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        previous = bool(
            normalized_state[
                "energized"
            ]
        )

        reset_active = bool(
            normalized_inputs[
                "IN"
            ]
        )

        energized = (
            False
            if reset_active
            else previous
        )

        events: list[
            LogicEvent
        ] = []

        if energized != previous:
            events.append(
                LogicEvent(
                    event_type=(
                        LogicEventType.OUTPUT_CHANGED
                    ),
                    component_id=self.component_id,
                    signal_name="OUT",
                    previous_value=previous,
                    current_value=energized,
                    time=time,
                )
            )

        return LogicControlResult(
            outputs={
                "OUT": energized,
            },
            state={
                "energized": energized,
            },
            time=time,
            events=tuple(
                events
            ),
            diagnostics={
                "energized": energized,
                "reset": reset_active,
            },
        )


__all__ = [
    "LogicCoil",
    "LogicSetCoil",
    "LogicResetCoil",
]
