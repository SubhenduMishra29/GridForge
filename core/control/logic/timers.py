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

Authoritative timer state is maintained entirely by Core.
"""

from __future__ import annotations

from enum import Enum
import math
from typing import Sequence

from ...base import ControlSignal, SignalRole, State, Inputs
from .base import LogicControlComponent, LogicControlResult, LogicEvent, LogicEventType, LogicStateDefinition


class TimerMode(str, Enum):
    """Supported deterministic timer modes."""

    TON = "ton"
    TOF = "tof"
    TP = "tp"


class LogicTimer(LogicControlComponent):
    """Generic deterministic TON/TOF/TP Logic timer."""

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "timer"

    def __init__(self, component_id: str, *, preset: float, mode: TimerMode = TimerMode.TON) -> None:
        component_id = str(component_id).strip()
        if not component_id:
            raise ValueError("LogicTimer component_id cannot be empty.")
        preset = float(preset)
        if not math.isfinite(preset):
            raise ValueError("LogicTimer preset must be finite.")
        if preset < 0.0:
            raise ValueError("LogicTimer preset cannot be negative.")
        try:
            normalized_mode = mode if isinstance(mode, TimerMode) else TimerMode(mode)
        except ValueError as exc:
            raise ValueError(f"Unsupported timer mode: {mode!r}.") from exc
        self._component_id = component_id
        self._preset = preset
        self._mode = normalized_mode

    @property
    def preset(self) -> float:
        return self._preset

    @property
    def mode(self) -> TimerMode:
        return self._mode

    def input_definition(self) -> Sequence[ControlSignal]:
        return (ControlSignal(name="IN", role=SignalRole.INPUT, description="Boolean timer input.", value_type=bool),)

    def output_definition(self) -> Sequence[ControlSignal]:
        return (ControlSignal(name="Q", role=SignalRole.OUTPUT, description="Boolean timer output.", value_type=bool),)

    def logic_state_definition(self) -> Sequence[LogicStateDefinition]:
        return (
            LogicStateDefinition("elapsed", float, 0.0, "Accumulated timer duration."),
            LogicStateDefinition("active", bool, False, "Whether the timer is currently timing."),
            LogicStateDefinition("input_previous", bool, False, "Previous sampled input used for edge detection."),
            LogicStateDefinition("output", bool, False, "Previous timer output."),
            LogicStateDefinition("evaluation_time", float, 0.0, "Previous simulation evaluation time."),
        )

    def reset_logic(self) -> State:
        return {"elapsed": 0.0, "active": False, "input_previous": False, "output": False, "evaluation_time": 0.0}

    def reset(self, inputs: Inputs | None = None) -> State:
        del inputs
        return self.reset_logic()

    def evaluate_logic(self, state: State, inputs: Inputs, time: float) -> LogicControlResult:
        time = _finite_time(time)
        normalized_inputs = self.validate_logic_inputs(inputs)
        normalized_state = self.validate_logic_state(state)

        input_active = bool(normalized_inputs["IN"])
        previous_input = bool(normalized_state["input_previous"])
        previous_elapsed = float(normalized_state["elapsed"])
        previous_active = bool(normalized_state["active"])
        previous_output = bool(normalized_state["output"])
        previous_time = float(normalized_state["evaluation_time"])
        delta = _sample_delta(time, previous_time)

        elapsed = max(0.0, previous_elapsed)
        active = previous_active
        output = previous_output

        if self.mode is TimerMode.TON:
            if input_active:
                if not previous_active:
                    elapsed = 0.0
                elapsed = min(self.preset, elapsed + delta)
                active = True
                output = elapsed >= self.preset
            else:
                elapsed = 0.0
                active = False
                output = False

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
                    elapsed = min(self.preset, elapsed + delta)
                    output = elapsed < self.preset
                    if elapsed >= self.preset:
                        active = False
                        output = False
                else:
                    output = False

        else:
            rising_edge = input_active and not previous_input
            if rising_edge:
                elapsed = 0.0
                active = True
            if active:
                elapsed = min(self.preset, elapsed + delta)
                output = elapsed < self.preset
                if elapsed >= self.preset:
                    active = False
                    output = False
            else:
                output = False

        events: list[LogicEvent] = []
        if previous_active != active:
            events.append(LogicEvent(
                event_type=LogicEventType.STATE_CHANGED,
                component_id=self.component_id,
                signal_name="active",
                previous_value=previous_active,
                current_value=active,
                time=time,
                data={"mode": self.mode.value},
            ))

        if previous_output != output:
            events.append(LogicEvent(
                event_type=LogicEventType.OUTPUT_CHANGED,
                component_id=self.component_id,
                signal_name="Q",
                previous_value=previous_output,
                current_value=output,
                time=time,
                data={"mode": self.mode.value, "elapsed": elapsed, "preset": self.preset},
            ))

        if not previous_active and active:
            events.append(LogicEvent(
                event_type=LogicEventType.TRIGGERED,
                component_id=self.component_id,
                signal_name="IN",
                previous_value=previous_input,
                current_value=input_active,
                time=time,
                data={"mode": self.mode.value, "preset": self.preset},
            ))

        return LogicControlResult(
            outputs={"Q": output},
            state={
                "elapsed": elapsed,
                "active": active,
                "input_previous": input_active,
                "output": output,
                "evaluation_time": time,
            },
            time=time,
            events=tuple(events),
            diagnostics={"mode": self.mode.value, "preset": self.preset, "elapsed": elapsed, "active": active},
        )


class LogicTONTimer(LogicTimer):
    """IEC-style on-delay timer."""

    def __init__(self, component_id: str, *, preset: float) -> None:
        super().__init__(component_id, preset=preset, mode=TimerMode.TON)


class LogicTOFTimer(LogicTimer):
    """IEC-style off-delay timer."""

    def __init__(self, component_id: str, *, preset: float) -> None:
        super().__init__(component_id, preset=preset, mode=TimerMode.TOF)


class LogicTPTimer(LogicTimer):
    """IEC-style pulse timer."""

    def __init__(self, component_id: str, *, preset: float) -> None:
        super().__init__(component_id, preset=preset, mode=TimerMode.TP)


def _finite_time(value: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Timer evaluation time must be numeric.") from exc
    if not math.isfinite(result):
        raise ValueError("Timer evaluation time must be finite.")
    return result


def _sample_delta(current_time: float, previous_time: float) -> float:
    return max(0.0, current_time - previous_time)


__all__ = ["TimerMode", "LogicTimer", "LogicTONTimer", "LogicTOFTimer", "LogicTPTimer"]
