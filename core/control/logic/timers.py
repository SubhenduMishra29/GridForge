```python
"""
GridForge V2 - Logic Timers
===========================

Author:
    Subhendu Mishra

File:
    core/control/logic/timers.py

Purpose
-------
Deterministic timer components for the Logic Control branch.

Timers are simulation-time driven. They never use wall-clock time.

Architecture
------------
The timer is a LogicControlComponent.

Inputs:
    IN

Outputs:
    Q

Persistent state:
    elapsed
    active

The Core owns timer state and semantics. The UI logic-layout/editing
canvas only represents and edits the component and its connections.
"""

from __future__ import annotations

from enum import Enum
import math
from typing import Sequence

from ...base import (
    ControlSignal,
    SignalRole,
    State,
    Inputs,
)
from .base import (
    LogicControlComponent,
    LogicControlResult,
    LogicEvent,
    LogicEventType,
    LogicStateDefinition,
)


# ============================================================================
# TIMER MODE
# ============================================================================


class TimerMode(str, Enum):
    """Supported deterministic timer modes."""

    TON = "ton"
    TOF = "tof"
    TP = "tp"


# ============================================================================
# TIMER
# ============================================================================


class LogicTimer(
    LogicControlComponent,
):
    """
    Generic deterministic Logic timer.

    TON
        Q becomes true after IN remains true for the preset duration.

    TOF
        Q remains true for the preset duration after IN becomes false.

    TP
        A rising edge on IN starts a pulse of the preset duration.

    The timer uses the supplied ``time`` value and therefore remains
    deterministic under simulation, replay, testing, and time stepping.
    """

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "timer"

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def __init__(
        self,
        component_id: str,
        *,
        preset: float,
        mode: TimerMode = TimerMode.TON,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicTimer component_id cannot be empty."
            )

        preset = float(
            preset
        )

        if not math.isfinite(
            preset
        ):
            raise ValueError(
                "LogicTimer preset must be finite."
            )

        if preset < 0.0:
            raise ValueError(
                "LogicTimer preset cannot be negative."
            )

        try:
            normalized_mode = (
                mode
                if isinstance(
                    mode,
                    TimerMode,
                )
                else TimerMode(
                    mode
                )
            )
        except ValueError as exc:
            raise ValueError(
                f"Unsupported timer mode: {mode!r}."
            ) from exc

        self._component_id = component_id
        self._preset = preset
        self._mode = normalized_mode

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    @property
    def preset(self) -> float:
        """Preset duration in simulation-time units."""

        return self._preset

    @property
    def mode(self) -> TimerMode:
        """Timer operating mode."""

        return self._mode

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
                    "Boolean timer input."
                ),
                value_type=bool,
            ),
        )

    def output_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="Q",
                role=SignalRole.OUTPUT,
                description=(
                    "Boolean timer output."
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
                name="elapsed",
                value_type=float,
                default=0.0,
                description=(
                    "Accumulated timer duration."
                ),
            ),
            LogicStateDefinition(
                name="active",
                value_type=bool,
                default=False,
                description=(
                    "Whether the timer is currently timing."
                ),
            ),
            LogicStateDefinition(
                name="input_previous",
                value_type=bool,
                default=False,
                description=(
                    "Previous sampled input used for edge detection."
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
            "elapsed": 0.0,
            "active": False,
            "input_previous": False,
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
        time = _finite_time(
            time
        )

        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        normalized_state = (
            self.validate_logic_state(
                state
            )
        )

        input_active = bool(
            normalized_inputs[
                "IN"
            ]
        )

        previous_input = bool(
            normalized_state[
                "input_previous"
            ]
        )

        previous_elapsed = float(
            normalized_state[
                "elapsed"
            ]
        )

        previous_active = bool(
            normalized_state[
                "active"
            ]
        )

        # --------------------------------------------------------------------
        # INITIAL / REPEATED SAMPLE
        # --------------------------------------------------------------------

        elapsed = max(
            0.0,
            previous_elapsed,
        )

        active = previous_active
        output = False

        # --------------------------------------------------------------------
        # TON
        # --------------------------------------------------------------------

        if self.mode is TimerMode.TON:
            if input_active:
                if not previous_active:
                    elapsed = 0.0

                elapsed = min(
                    self.preset,
                    elapsed
                    + _sample_delta(
                        time,
                        normalized_state,
                    ),
                )

                active = True

                output = (
                    elapsed
                    >= self.preset
                )
            else:
                elapsed = 0.0
                active = False
                output = False

        # --------------------------------------------------------------------
        # TOF
        # --------------------------------------------------------------------

        elif self.mode is TimerMode.TOF:
            if input_active:
                elapsed = 0.0
                active = False
                output = True
            else:
                if previous_input:
                    elapsed = 0.0
                    active = True

                if active:
                    elapsed = min(
                        self.preset,
                        elapsed
                        + _sample_delta(
                            time,
                            normalized_state,
                        ),
                    )

                    output = (
                        elapsed
                        < self.preset
                    )

                    if (
                        elapsed
                        >= self.preset
                    ):
                        active = False
                        output = False
                else:
                    output = False

        # --------------------------------------------------------------------
        # TP
        # --------------------------------------------------------------------

        elif self.mode is TimerMode.TP:
            rising_edge = (
                input_active
                and not previous_input
            )

            if rising_edge:
                elapsed = 0.0
                active = True

            if active:
                elapsed = min(
                    self.preset,
                    elapsed
                    + _sample_delta(
                        time,
                        normalized_state,
                    ),
                )

                output = (
                    elapsed
                    < self.preset
                )

                if (
                    elapsed
                    >= self.preset
                ):
                    active = False
                    output = False
            else:
                output = False

        # --------------------------------------------------------------------
        # STATE / EVENTS
        # --------------------------------------------------------------------

        events: list[
            LogicEvent
        ] = []

        if previous_active != active:
            events.append(
                LogicEvent(
                    event_type=(
                        LogicEventType.STATE_CHANGED
                    ),
                    component_id=self.component_id,
                    signal_name="active",
                    previous_value=previous_active,
                    current_value=active,
                    time=time,
                    data={
                        "mode": self.mode.value,
                    },
                )
            )

        previous_output = (
            previous_active
            and (
                previous_elapsed
                < self.preset
            )
        )

        if previous_output != output:
            events.append(
                LogicEvent(
                    event_type=(
                        LogicEventType.OUTPUT_CHANGED
                    ),
                    component_id=self.component_id,
                    signal_name="Q",
                    previous_value=previous_output,
                    current_value=output,
                    time=time,
                    data={
                        "mode": self.mode.value,
                        "elapsed": elapsed,
                        "preset": self.preset,
                    },
                )
            )

        if (
            not previous_active
            and active
        ):
            events.append(
                LogicEvent(
                    event_type=(
                        LogicEventType.TRIGGERED
                    ),
                    component_id=self.component_id,
                    signal_name="IN",
                    previous_value=previous_input,
                    current_value=input_active,
                    time=time,
                    data={
                        "mode": self.mode.value,
                        "preset": self.preset,
                    },
                )
            )

        return LogicControlResult(
            outputs={
                "Q": output,
            },
            state={
                "elapsed": elapsed,
                "active": active,
                "input_previous": input_active,
            },
            time=time,
            events=tuple(
                events
            ),
            diagnostics={
                "mode": self.mode.value,
                "preset": self.preset,
                "elapsed": elapsed,
                "active": active,
            },
        )


# ============================================================================
# SPECIALIZED TIMERS
# ============================================================================


class LogicTONTimer(
    LogicTimer,
):
    """IEC-style on-delay timer."""

    def __init__(
        self,
        component_id: str,
        *,
        preset: float,
    ) -> None:
        super().__init__(
            component_id,
            preset=preset,
            mode=TimerMode.TON,
        )


class LogicTOFTimer(
    LogicTimer,
):
    """IEC-style off-delay timer."""

    def __init__(
        self,
        component_id: str,
        *,
        preset: float,
    ) -> None:
        super().__init__(
            component_id,
            preset=preset,
            mode=TimerMode.TOF,
        )


class LogicTPTimer(
    LogicTimer,
):
    """IEC-style pulse timer."""

    def __init__(
        self,
        component_id: str,
        *,
        preset: float,
    ) -> None:
        super().__init__(
            component_id,
            preset=preset,
            mode=TimerMode.TP,
        )


# ============================================================================
# HELPERS
# ============================================================================


def _finite_time(
    value: float,
) -> float:
    try:
        result = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "Timer evaluation time must be numeric."
        ) from exc

    if not math.isfinite(
        result
    ):
        raise ValueError(
            "Timer evaluation time must be finite."
        )

    return result


def _sample_delta(
    current_time: float,
    state: State,
) -> float:
    """
    Obtain the deterministic sample interval.

    The Logic component state contract intentionally stores only the timer's
    logical state. If the base component supplies a previous evaluation time,
    use it; otherwise the current invocation is treated as a zero-duration
    first sample.

    No wall-clock source is consulted.
    """

    previous_time = state.get(
        "_evaluation_time"
    )

    if previous_time is None:
        return 0.0

    try:
        previous_time = float(
            previous_time
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    if not math.isfinite(
        previous_time
    ):
        return 0.0

    delta = (
        current_time
        - previous_time
    )

    if delta < 0.0:
        return 0.0

    return delta


__all__ = [
    "TimerMode",
    "LogicTimer",
    "LogicTONTimer",
    "LogicTOFTimer",
    "LogicTPTimer",
]
```
