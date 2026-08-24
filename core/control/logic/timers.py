"""
GridForge V2 - Logic Timers
============================

Author:
    Subhendu Mishra

File:
    core/control/logic/timers.py

Purpose
-------
Headless industrial timer elements for the Logic Control domain.

Supported timer modes:

    TON - On-delay timer
    TOF - Off-delay timer
    TP  - Pulse timer

Timers are deterministic and use the supplied control/simulation time.
They never use wall-clock time.

The UI logic-layout/editing canvas owns only the graphical representation
of timers. Timer behavior and persistent timing state belong to Core.

Architectural boundary
----------------------
    Logic inputs
        |
        v
      Timer
        |
        +----> Boolean output
        |
        +----> persistent timing state

The timer does not directly mutate core/model or simulation state.
"""

from __future__ import annotations

from enum import Enum
import math
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
    LogicStateDefinition,
)


class TimerType(str, Enum):
    """Supported industrial timer modes."""

    TON = "ton"
    TOF = "tof"
    TP = "tp"


class LogicTimer(LogicControlComponent):
    """
    Base deterministic timer implementation.

    Input:
        IN
            Boolean timer command.

    Output:
        Q
            Timer output.

    Persistent state:
        Q
            Current timer output.
        running
            Whether the timing interval is active.
        elapsed
            Elapsed time in seconds.
        start_time
            Control/simulation time at which the active interval started.
        previous_input
            Previous evaluated input state.

    The timer uses the supplied ``time`` argument exclusively.
    """

    _STATE_Q = "Q"
    _STATE_RUNNING = "running"
    _STATE_ELAPSED = "elapsed"
    _STATE_START_TIME = "start_time"
    _STATE_PREVIOUS_INPUT = "previous_input"

    def __init__(
        self,
        component_id: str,
        preset: float,
        timer_type: TimerType,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicTimer component_id cannot be empty."
            )

        preset = float(preset)

        if not math.isfinite(preset):
            raise ValueError(
                "Timer preset must be finite."
            )

        if preset < 0.0:
            raise ValueError(
                "Timer preset cannot be negative."
            )

        if not isinstance(
            timer_type,
            TimerType,
        ):
            try:
                timer_type = TimerType(
                    timer_type
                )
            except ValueError as exc:
                raise ValueError(
                    f"Invalid timer type: "
                    f"{timer_type!r}."
                ) from exc

        self._component_id = component_id
        self._preset = preset
        self._timer_type = timer_type

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return f"timer_{self._timer_type.value}"

    @property
    def timer_type(self) -> TimerType:
        return self._timer_type

    @property
    def preset(self) -> float:
        """Return preset duration in seconds."""

        return self._preset

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
                description="Boolean timer command.",
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
                description="Boolean timer output.",
                value_type=bool,
            ),
        )

    # ========================================================================
    # STATE CONTRACT
    # ========================================================================

    @property
    def logic_state_names(
        self,
    ) -> Sequence[str]:
        return (
            self._STATE_Q,
            self._STATE_RUNNING,
            self._STATE_ELAPSED,
            self._STATE_START_TIME,
            self._STATE_PREVIOUS_INPUT,
        )

    def logic_state_definition(
        self,
    ) -> Sequence[LogicStateDefinition]:
        return (
            LogicStateDefinition(
                name=self._STATE_Q,
                description="Current timer output.",
                value_type=bool,
                default=False,
            ),
            LogicStateDefinition(
                name=self._STATE_RUNNING,
                description="Whether the timer is currently timing.",
                value_type=bool,
                default=False,
            ),
            LogicStateDefinition(
                name=self._STATE_ELAPSED,
                description="Elapsed timing duration in seconds.",
                value_type=float,
                default=0.0,
            ),
            LogicStateDefinition(
                name=self._STATE_START_TIME,
                description="Control time at which timing started.",
                value_type=float,
                default=0.0,
            ),
            LogicStateDefinition(
                name=self._STATE_PREVIOUS_INPUT,
                description="Previous Boolean input state.",
                value_type=bool,
                default=False,
            ),
        )

    # ========================================================================
    # EVALUATION
    # ========================================================================

    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        normalized_state = self.validate_state(
            state
        )

        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        current_time = _finite_time(
            time
        )

        input_active = bool(
            normalized_inputs["IN"]
        )

        previous_input = bool(
            normalized_state[
                self._STATE_PREVIOUS_INPUT
            ]
        )

        q = bool(
            normalized_state[
                self._STATE_Q
            ]
        )

        running = bool(
            normalized_state[
                self._STATE_RUNNING
            ]
        )

        elapsed = _non_negative_finite(
            normalized_state[
                self._STATE_ELAPSED
            ],
            "elapsed",
        )

        start_time = _finite_time(
            normalized_state[
                self._STATE_START_TIME
            ]
        )

        if self._timer_type is TimerType.TON:
            (
                q,
                running,
                elapsed,
                start_time,
            ) = self._evaluate_ton(
                input_active=input_active,
                previous_input=previous_input,
                current_time=current_time,
                q=q,
                running=running,
                elapsed=elapsed,
                start_time=start_time,
            )

        elif self._timer_type is TimerType.TOF:
            (
                q,
                running,
                elapsed,
                start_time,
            ) = self._evaluate_tof(
                input_active=input_active,
                previous_input=previous_input,
                current_time=current_time,
                q=q,
                running=running,
                elapsed=elapsed,
                start_time=start_time,
            )

        elif self._timer_type is TimerType.TP:
            (
                q,
                running,
                elapsed,
                start_time,
            ) = self._evaluate_tp(
                input_active=input_active,
                previous_input=previous_input,
                current_time=current_time,
                q=q,
                running=running,
                elapsed=elapsed,
                start_time=start_time,
            )

        else:
            raise ValueError(
                f"Unsupported timer type: "
                f"{self._timer_type!r}."
            )

        return LogicControlResult(
            outputs={
                "Q": q,
            },
            state={
                self._STATE_Q: q,
                self._STATE_RUNNING: running,
                self._STATE_ELAPSED: elapsed,
                self._STATE_START_TIME: start_time,
                self._STATE_PREVIOUS_INPUT: input_active,
            },
            time=current_time,
        )

    # ========================================================================
    # TON
    # ========================================================================

    def _evaluate_ton(
        self,
        *,
        input_active: bool,
        previous_input: bool,
        current_time: float,
        q: bool,
        running: bool,
        elapsed: float,
        start_time: float,
    ) -> tuple[
        bool,
        bool,
        float,
        float,
    ]:
        """
        On-delay behavior.

        IN = False:
            Q = False
            timer reset

        IN changes False -> True:
            timing starts

        elapsed >= preset:
            Q = True
        """

        if not input_active:
            return (
                False,
                False,
                0.0,
                current_time,
            )

        if not previous_input and input_active:
            running = True
            start_time = current_time
            elapsed = 0.0

        elif not running and not q:
            running = True
            start_time = current_time
            elapsed = 0.0

        if self._preset == 0.0:
            return (
                True,
                False,
                0.0,
                start_time,
            )

        if running:
            elapsed = max(
                0.0,
                current_time - start_time,
            )

            if elapsed >= self._preset:
                elapsed = self._preset
                q = True
                running = False

        return (
            q,
            running,
            elapsed,
            start_time,
        )

    # ========================================================================
    # TOF
    # ========================================================================

    def _evaluate_tof(
        self,
        *,
        input_active: bool,
        previous_input: bool,
        current_time: float,
        q: bool,
        running: bool,
        elapsed: float,
        start_time: float,
    ) -> tuple[
        bool,
        bool,
        float,
        float,
    ]:
        """
        Off-delay behavior.

        IN = True:
            Q = True
            timer reset

        IN changes True -> False:
            timing starts

        elapsed >= preset:
            Q = False
        """

        if input_active:
            return (
                True,
                False,
                0.0,
                current_time,
            )

        if previous_input and not input_active:
            running = True
            start_time = current_time
            elapsed = 0.0

        elif not running and q:
            running = True
            start_time = current_time
            elapsed = 0.0

        if self._preset == 0.0:
            return (
                False,
                False,
                0.0,
                start_time,
            )

        if running:
            elapsed = max(
                0.0,
                current_time - start_time,
            )

            if elapsed >= self._preset:
                elapsed = self._preset
                q = False
                running = False

        return (
            q,
            running,
            elapsed,
            start_time,
        )

    # ========================================================================
    # TP
    # ========================================================================

    def _evaluate_tp(
        self,
        *,
        input_active: bool,
        previous_input: bool,
        current_time: float,
        q: bool,
        running: bool,
        elapsed: float,
        start_time: float,
    ) -> tuple[
        bool,
        bool,
        float,
        float,
    ]:
        """
        Pulse timer behavior.

        A rising edge starts one pulse.

        During the preset duration:
            Q = True

        After the preset duration:
            Q = False

        A sustained input does not retrigger the pulse.
        """

        rising_edge = (
            input_active
            and not previous_input
        )

        if rising_edge and not running:
            q = True
            running = True
            elapsed = 0.0
            start_time = current_time

            if self._preset == 0.0:
                return (
                    False,
                    False,
                    0.0,
                    start_time,
                )

        if running:
            elapsed = max(
                0.0,
                current_time - start_time,
            )

            if elapsed >= self._preset:
                elapsed = self._preset
                q = False
                running = False

        return (
            q,
            running,
            elapsed,
            start_time,
        )

    # ========================================================================
    # RESET
    # ========================================================================

    def reset_logic(
        self,
    ) -> State:
        """
        Return the timer's reset state.
        """

        return {
            self._STATE_Q: False,
            self._STATE_RUNNING: False,
            self._STATE_ELAPSED: 0.0,
            self._STATE_START_TIME: 0.0,
            self._STATE_PREVIOUS_INPUT: False,
        }

    # ========================================================================
    # STATUS HELPERS
    # ========================================================================

    def output(
        self,
        state: State,
    ) -> bool:
        """Return the timer output from a supplied state."""

        normalized = self.validate_state(
            state
        )

        return bool(
            normalized[
                self._STATE_Q
            ]
        )

    def is_running(
        self,
        state: State,
    ) -> bool:
        """Return whether the timer is timing."""

        normalized = self.validate_state(
            state
        )

        return bool(
            normalized[
                self._STATE_RUNNING
            ]
        )

    def elapsed(
        self,
        state: State,
    ) -> float:
        """Return elapsed timer duration in seconds."""

        normalized = self.validate_state(
            state
        )

        return float(
            normalized[
                self._STATE_ELAPSED
            ]
        )


# ============================================================================
# CONCRETE TIMER TYPES
# ============================================================================


class TONTimer(LogicTimer):
    """Industrial on-delay timer."""

    def __init__(
        self,
        component_id: str,
        preset: float,
    ) -> None:
        super().__init__(
            component_id=component_id,
            preset=preset,
            timer_type=TimerType.TON,
        )


class TOFTimer(LogicTimer):
    """Industrial off-delay timer."""

    def __init__(
        self,
        component_id: str,
        preset: float,
    ) -> None:
        super().__init__(
            component_id=component_id,
            preset=preset,
            timer_type=TimerType.TOF,
        )


class TPTimer(LogicTimer):
    """Industrial pulse timer."""

    def __init__(
        self,
        component_id: str,
        preset: float,
    ) -> None:
        super().__init__(
            component_id=component_id,
            preset=preset,
            timer_type=TimerType.TP,
        )


# Engineering-friendly aliases.
OnDelayTimer = TONTimer
OffDelayTimer = TOFTimer
PulseTimer = TPTimer


# ============================================================================
# HELPERS
# ============================================================================


def _finite_time(
    value: float,
) -> float:
    try:
        value = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "Timer time must be numeric."
        ) from exc

    if not math.isfinite(value):
        raise ValueError(
            "Timer time must be finite."
        )

    return value


def _non_negative_finite(
    value: float,
    name: str,
) -> float:
    try:
        value = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(value):
        raise ValueError(
            f"{name} must be finite."
        )

    if value < 0.0:
        raise ValueError(
            f"{name} cannot be negative."
        )

    return value


__all__ = [
    "TimerType",
    "LogicTimer",
    "TONTimer",
    "TOFTimer",
    "TPTimer",
    "OnDelayTimer",
    "OffDelayTimer",
    "PulseTimer",
]
