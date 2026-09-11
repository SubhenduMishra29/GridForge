"""
GridForge V2 - Logic Control Base Contracts
============================================

Author:
    Subhendu Mishra

File:
    core/control/logic/base.py

Purpose
-------
Defines the headless Core Control contract for discrete / logic-control
components.

The Logic branch supports:

    - Boolean gates
    - contacts
    - coils
    - timers
    - latches
    - interlocks
    - future PLC / relay-style logic elements

The UI logic-layout/editing canvas is deliberately outside this module.

Architectural rules
-------------------
1. Logic components are headless domain components.
2. Logic components do not access core/model directly.
3. Logic components do not access the electrical network directly.
4. Logic components do not import UI modules.
5. Logic components do not import plugins.
6. Logic evaluation is deterministic.
7. Boolean truth remains Boolean.
8. Persistent logic state is explicit.
9. Logic does not perform numerical integration.
10. Events are reported as data; dispatch belongs outside Core Control.

Common Control boundary
-----------------------
ControlComponent requires:

    output(state, inputs, time) -> Outputs

Logic components additionally expose:

    evaluate_logic(state, inputs, time) -> LogicControlResult

The adapter below satisfies the common ControlComponent contract without
introducing UI or plugin dependencies.

Authoritative logic evaluation remains ``evaluate_logic()``.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Mapping, Sequence

from ..base import (
    ControlComponent,
    ControlKind,
    ControlSignal,
    ControlResult,
    Inputs,
    Outputs,
    SignalRole,
    SignalValue,
    State,
)


class LogicControlError(RuntimeError):
    """Base exception for Logic Control."""


class LogicConfigurationError(LogicControlError):
    """Invalid Logic Control configuration."""


class LogicInputError(LogicControlError):
    """Invalid Logic Control input."""


class LogicOutputError(LogicControlError):
    """Invalid Logic Control output."""


class LogicStateError(LogicControlError):
    """Invalid Logic Control state."""


class LogicEvaluationError(LogicControlError):
    """Failure during Logic Control evaluation."""


class LogicEdge(str, Enum):
    """Discrete edge classification."""

    NONE = "none"
    RISING = "rising"
    FALLING = "falling"


class LogicEventType(str, Enum):
    """Discrete logic-event categories."""

    NONE = "none"
    RISING_EDGE = "rising_edge"
    FALLING_EDGE = "falling_edge"
    STATE_CHANGED = "state_changed"
    OUTPUT_CHANGED = "output_changed"
    TIMER_EXPIRED = "timer_expired"
    TRIGGERED = "triggered"


@dataclass(frozen=True)
class LogicStateDefinition:
    """Definition of one persistent discrete logic state variable."""

    name: str
    value_type: type = bool
    default: SignalValue = False
    description: str = ""

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise LogicConfigurationError("Logic state name cannot be empty.")
        if self.value_type not in (bool, int, float):
            raise LogicConfigurationError("Logic state value_type must be bool, int, or float.")
        _validate_value(name, self.default, self.value_type, LogicStateError)
        object.__setattr__(self, "name", name)


@dataclass(frozen=True)
class LogicEvent:
    """Immutable description of a discrete logic event."""

    event_type: LogicEventType
    component_id: str
    signal_name: str | None = None
    previous_value: SignalValue | None = None
    current_value: SignalValue | None = None
    time: float = 0.0
    data: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        component_id = str(self.component_id).strip()
        if not component_id:
            raise LogicConfigurationError("Logic event component_id cannot be empty.")
        try:
            event_type = self.event_type if isinstance(self.event_type, LogicEventType) else LogicEventType(self.event_type)
        except ValueError as exc:
            raise LogicConfigurationError(f"Invalid logic event type: {self.event_type!r}.") from exc
        time = _finite_float(self.time, "Logic event time")
        object.__setattr__(self, "component_id", component_id)
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "time", time)
        object.__setattr__(self, "data", dict(self.data or {}))


@dataclass(frozen=True)
class LogicControlResult:
    """Result of one discrete Logic Control evaluation."""

    outputs: Mapping[str, SignalValue]
    state: Mapping[str, SignalValue]
    time: float
    events: Sequence[LogicEvent] = ()
    diagnostics: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        time = _finite_float(self.time, "Logic result time")
        object.__setattr__(self, "time", time)
        object.__setattr__(self, "outputs", dict(self.outputs))
        object.__setattr__(self, "state", dict(self.state))
        events = tuple(self.events)
        for event in events:
            if not isinstance(event, LogicEvent):
                raise LogicEvaluationError("Logic events must be LogicEvent instances.")
        object.__setattr__(self, "events", events)
        object.__setattr__(self, "diagnostics", dict(self.diagnostics or {}))

    def as_control_result(self) -> ControlResult:
        """Adapt this Logic result to the common ControlResult contract."""
        diagnostics = dict(self.diagnostics or {})
        diagnostics["logic_state"] = dict(self.state)
        diagnostics["logic_events"] = tuple(self.events)
        return ControlResult(
            outputs=self.outputs,
            time=self.time,
            derivatives=None,
            diagnostics=diagnostics,
        )


class LogicControlComponent(ControlComponent):
    """Common contract for all headless Logic Control components."""

    @property
    def control_kind(self) -> ControlKind:
        return ControlKind.LOGIC

    def logic_state_definition(self) -> Sequence[LogicStateDefinition]:
        return ()

    @property
    def logic_state_names(self) -> tuple[str, ...]:
        return tuple(definition.name for definition in self.logic_state_definition())

    @property
    def logic_state_size(self) -> int:
        return len(self.logic_state_names)

    def state_definition(self) -> Sequence[ControlSignal]:
        return tuple(
            ControlSignal(
                name=definition.name,
                role=SignalRole.INTERNAL,
                description=definition.description,
                required=True,
                value_type=definition.value_type,
            )
            for definition in self.logic_state_definition()
        )

    @property
    def state_names(self) -> tuple[str, ...]:
        return self.logic_state_names

    @property
    def state_size(self) -> int:
        return self.logic_state_size

    def initial_state(self, inputs: Inputs | None = None) -> Mapping[str, SignalValue]:
        del inputs
        return {definition.name: definition.default for definition in self.logic_state_definition()}

    def validate_logic_inputs(self, inputs: Inputs) -> dict[str, SignalValue]:
        try:
            return dict(self.validate_inputs(inputs))
        except Exception as exc:
            if isinstance(exc, LogicControlError):
                raise
            raise LogicInputError(f"{self.component_id}: invalid logic inputs.") from exc

    def validate_logic_state(self, state: State) -> dict[str, SignalValue]:
        if state is None:
            raise LogicStateError(f"{self.component_id}: logic state cannot be None.")
        expected = set(self.logic_state_names)
        actual = {str(name) for name in state}
        missing = expected - actual
        unknown = actual - expected
        if missing:
            raise LogicStateError(f"{self.component_id}: missing logic states: {sorted(missing)}")
        if unknown:
            raise LogicStateError(f"{self.component_id}: unknown logic states: {sorted(unknown)}")
        definitions = {definition.name: definition for definition in self.logic_state_definition()}
        normalized: dict[str, SignalValue] = {}
        for name in self.logic_state_names:
            value = state[name]
            definition = definitions[name]
            _validate_value(name, value, definition.value_type, LogicStateError)
            normalized[name] = value
        return normalized

    def validate_state(self, state: State) -> dict[str, SignalValue]:
        return self.validate_logic_state(state)

    @abstractmethod
    def evaluate_logic(self, state: State, inputs: Inputs, time: float) -> LogicControlResult:
        raise NotImplementedError

    def output(self, state: State, inputs: Inputs, time: float) -> Outputs:
        time = _finite_float(time, "Logic output time")
        normalized_state = self.validate_logic_state(state)
        normalized_inputs = self.validate_logic_inputs(inputs)
        result = self._evaluate_logic_safe(normalized_state, normalized_inputs, time)
        self.validate_logic_result(result)
        return dict(result.outputs)

    def evaluate(self, state: State, inputs: Inputs, time: float) -> ControlResult:
        time = _finite_float(time, "Logic evaluation time")
        normalized_state = self.validate_logic_state(state)
        normalized_inputs = self.validate_logic_inputs(inputs)
        result = self._evaluate_logic_safe(normalized_state, normalized_inputs, time)
        self.validate_logic_result(result)
        return result.as_control_result()

    def _evaluate_logic_safe(self, state: State, inputs: Inputs, time: float) -> LogicControlResult:
        try:
            return self.evaluate_logic(state, inputs, time)
        except LogicControlError:
            raise
        except Exception as exc:
            raise LogicEvaluationError(f"{self.component_id}: logic evaluation failed.") from exc

    def validate_logic_result(self, result: LogicControlResult) -> None:
        if not isinstance(result, LogicControlResult):
            raise LogicOutputError("Logic evaluation must return LogicControlResult.")
        expected_outputs = {signal.name for signal in self.output_definition()}
        actual_outputs = set(result.outputs)
        if expected_outputs != actual_outputs:
            raise LogicOutputError(
                f"{self.component_id}: output mismatch; expected {sorted(expected_outputs)}, got {sorted(actual_outputs)}."
            )
        self.validate_logic_state(result.state)
        for name, value in result.outputs.items():
            signal = next(signal for signal in self.output_definition() if signal.name == name)
            _validate_value(name, value, signal.value_type, LogicOutputError)


def _validate_value(name: str, value: SignalValue, value_type: type, error_type: type[Exception]) -> None:
    if value_type is bool:
        valid = isinstance(value, bool)
    elif value_type is int:
        valid = isinstance(value, int) and not isinstance(value, bool)
    elif value_type is float:
        valid = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    else:
        valid = False
    if not valid:
        raise error_type(f"Invalid value for logic state/signal '{name}': {value!r}.")


def _finite_float(value: float, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise LogicEvaluationError(f"{label} must be numeric.") from exc
    if not math.isfinite(result):
        raise LogicEvaluationError(f"{label} must be finite.")
    return result


__all__ = [
    "LogicControlError",
    "LogicConfigurationError",
    "LogicInputError",
    "LogicOutputError",
    "LogicStateError",
    "LogicEvaluationError",
    "LogicEdge",
    "LogicEventType",
    "LogicStateDefinition",
    "LogicEvent",
    "LogicControlResult",
    "LogicControlComponent",
]
