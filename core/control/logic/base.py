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


# ============================================================================
# ERRORS
# ============================================================================


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


# ============================================================================
# ENUMERATIONS
# ============================================================================


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
    TIMER_EXPIRED = "timer_expired"
    TRIGGERED = "triggered"


# ============================================================================
# LOGIC STATE DEFINITION
# ============================================================================


@dataclass(frozen=True)
class LogicStateDefinition:
    """
    Definition of one persistent discrete logic state variable.

    Examples:

        energized
        Q
        running
        elapsed
        start_time
        status
    """

    name: str
    value_type: type = bool
    default: SignalValue = False
    description: str = ""

    def __post_init__(self) -> None:
        name = str(self.name).strip()

        if not name:
            raise LogicConfigurationError(
                "Logic state name cannot be empty."
            )

        if self.value_type not in (
            bool,
            int,
            float,
        ):
            raise LogicConfigurationError(
                "Logic state value_type must be "
                "bool, int, or float."
            )

        _validate_value(
            name,
            self.default,
            self.value_type,
            LogicStateError,
        )

        object.__setattr__(
            self,
            "name",
            name,
        )


# ============================================================================
# LOGIC EVENT
# ============================================================================


@dataclass(frozen=True)
class LogicEvent:
    """
    Immutable description of a discrete logic event.

    Event dispatch is outside this module.
    """

    event_type: LogicEventType
    component_id: str
    signal_name: str | None = None
    previous_value: SignalValue | None = None
    current_value: SignalValue | None = None
    time: float = 0.0
    data: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        component_id = str(
            self.component_id
        ).strip()

        if not component_id:
            raise LogicConfigurationError(
                "Logic event component_id cannot be empty."
            )

        try:
            event_type = (
                self.event_type
                if isinstance(
                    self.event_type,
                    LogicEventType,
                )
                else LogicEventType(
                    self.event_type
                )
            )
        except ValueError as exc:
            raise LogicConfigurationError(
                f"Invalid logic event type: "
                f"{self.event_type!r}."
            ) from exc

        time = _finite_float(
            self.time,
            "Logic event time",
        )

        object.__setattr__(
            self,
            "component_id",
            component_id,
        )
        object.__setattr__(
            self,
            "event_type",
            event_type,
        )
        object.__setattr__(
            self,
            "time",
            time,
        )
        object.__setattr__(
            self,
            "data",
            dict(self.data or {}),
        )


# ============================================================================
# LOGIC RESULT
# ============================================================================


@dataclass(frozen=True)
class LogicControlResult:
    """
    Result of one discrete Logic Control evaluation.

    ``outputs``
        Current component outputs.

    ``state``
        Complete resulting persistent logic state.

    ``events``
        Discrete event descriptions.

    ``diagnostics``
        Optional non-authoritative evaluation metadata.
    """

    outputs: Mapping[str, SignalValue]
    state: Mapping[str, SignalValue]
    time: float
    events: Sequence[LogicEvent] = ()
    diagnostics: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        time = _finite_float(
            self.time,
            "Logic result time",
        )

        object.__setattr__(
            self,
            "outputs",
            dict(self.outputs),
        )

        object.__setattr__(
            self,
            "state",
            dict(self.state),
        )

        events = tuple(self.events)

        for event in events:
            if not isinstance(
                event,
                LogicEvent,
            ):
                raise LogicEvaluationError(
                    "Logic events must be LogicEvent instances."
                )

        object.__setattr__(
            self,
            "events",
            events,
        )

        object.__setattr__(
            self,
            "time",
            time,
        )

        object.__setattr__(
            self,
            "diagnostics",
            dict(
                self.diagnostics or {}
            ),
        )

    def as_control_result(
        self,
    ) -> ControlResult:
        """
        Adapt this Logic result to the common ControlResult contract.

        Logic state and events are preserved in diagnostics because
        numerical derivatives do not belong to Logic Control.
        """

        diagnostics = dict(
            self.diagnostics or {}
        )

        diagnostics["logic_state"] = dict(
            self.state
        )

        diagnostics["logic_events"] = tuple(
            self.events
        )

        return ControlResult(
            outputs=self.outputs,
            time=self.time,
            derivatives=None,
            diagnostics=diagnostics,
        )


# ============================================================================
# LOGIC CONTROL COMPONENT
# ============================================================================


class LogicControlComponent(
    ControlComponent,
):
    """
    Common contract for all headless Logic Control components.

    Concrete implementations provide:

        input_definition()
        output_definition()
        evaluate_logic()

    The class provides:

        - common ControlKind classification
        - logic-state definition
        - initial/reset state
        - input validation
        - output validation
        - common evaluate() adapter
        - required ControlComponent.output() adapter
        - state transition detection
        - edge detection
    """

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    def control_kind(
        self,
    ) -> ControlKind:
        """All subclasses belong to the Logic Control branch."""

        return ControlKind.LOGIC

    # ========================================================================
    # LOGIC STATE
    # ========================================================================

    def logic_state_definition(
        self,
    ) -> Sequence[LogicStateDefinition]:
        """
        Return persistent logic-state definitions.

        Stateless components return ``()``.
        """

        return ()

    @property
    def logic_state_names(
        self,
    ) -> tuple[str, ...]:
        """Return ordered persistent logic-state names."""

        return tuple(
            definition.name
            for definition
            in self.logic_state_definition()
        )

    @property
    def logic_state_size(
        self,
    ) -> int:
        """Return number of persistent logic states."""

        return len(
            self.logic_state_names
        )

    # ------------------------------------------------------------------------
    # Compatibility with the common Control state contract
    # ------------------------------------------------------------------------

    def state_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Adapt LogicStateDefinition objects to ControlSignal definitions.

        This preserves the frozen common ControlComponent contract while
        retaining the richer LogicStateDefinition API.
        """

        return tuple(
            ControlSignal(
                name=definition.name,
                role=SignalRole.INTERNAL,
                description=definition.description,
                required=True,
                value_type=definition.value_type,
            )
            for definition
            in self.logic_state_definition()
        )

    @property
    def state_names(
        self,
    ) -> tuple[str, ...]:
        """
        Return the authoritative Logic state names.

        This explicitly mirrors ``logic_state_names`` so the inherited
        ControlComponent validation operates on the same state contract.
        """

        return self.logic_state_names

    @property
    def state_size(
        self,
    ) -> int:
        return self.logic_state_size

    def initial_state(
        self,
        inputs: Inputs | None = None,
    ) -> Mapping[str, SignalValue]:
        """
        Return a fresh initial logic state.

        ``inputs`` is accepted for compatibility with the common contract.
        """

        del inputs

        return {
            definition.name:
                definition.default
            for definition
            in self.logic_state_definition()
        }

    # ========================================================================
    # INPUT VALIDATION
    # ========================================================================

    def validate_logic_inputs(
        self,
        inputs: Inputs,
    ) -> dict[str, SignalValue]:
        """
        Validate Logic inputs using the common Control signal contract.
        """

        try:
            return dict(
                self.validate_inputs(
                    inputs
                )
            )
        except Exception as exc:
            if isinstance(
                exc,
                LogicControlError,
            ):
                raise

            raise LogicInputError(
                f"{self.component_id}: "
                "invalid logic inputs."
            ) from exc

    # ========================================================================
    # STATE VALIDATION
    # ========================================================================

    def validate_logic_state(
        self,
        state: State,
    ) -> dict[str, SignalValue]:
        """
        Validate persistent Logic state against LogicStateDefinition.
        """

        if state is None:
            raise LogicStateError(
                f"{self.component_id}: "
                "logic state cannot be None."
            )

        expected = set(
            self.logic_state_names
        )
        actual = {
            str(name)
            for name in state
        }

        missing = expected - actual
        unknown = actual - expected

        if missing:
            raise LogicStateError(
                f"{self.component_id}: "
                f"missing logic states: "
                f"{sorted(missing)}"
            )

        if unknown:
            raise LogicStateError(
                f"{self.component_id}: "
                f"unknown logic states: "
                f"{sorted(unknown)}"
            )

        definitions = {
            definition.name: definition
            for definition
            in self.logic_state_definition()
        }

        normalized: dict[
            str,
            SignalValue,
        ] = {}

        for name in self.logic_state_names:
            value = state[name]
            definition = definitions[name]

            _validate_value(
                name,
                value,
                definition.value_type,
                LogicStateError,
            )

            normalized[name] = value

        return normalized

    def validate_state(
        self,
        state: State,
    ) -> dict[str, SignalValue]:
        """
        Override the common state adapter so Logic state is validated
        against LogicStateDefinition rather than being treated as a
        generic numerical state.
        """

        return self.validate_logic_state(
            state
        )

    # ========================================================================
    # LOGIC EVALUATION
    # ========================================================================

    @abstractmethod
    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        """
        Evaluate the discrete Logic Control behavior.

        Implementations must return the complete resulting logic state.
        """

        raise NotImplementedError

    # ========================================================================
    # COMMON CONTROL OUTPUT ADAPTER
    # ========================================================================

    def output(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> Outputs:
        """
        Satisfy the common ControlComponent.output() contract.

        This is a compatibility adapter only.

        ``evaluate_logic()`` remains the authoritative Logic execution
        method. The adapter evaluates the component and returns only its
        outputs.

        The normal Logic execution path is ``evaluate()`` below, which
        evaluates exactly once and preserves Logic state/events.
        """

        time = _finite_float(
            time,
            "Logic output time",
        )

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

        result = self._evaluate_logic_safe(
            normalized_state,
            normalized_inputs,
            time,
        )

        self.validate_logic_result(
            result
        )

        return dict(
            result.outputs
        )

    # ========================================================================
    # COMMON CONTROL EVALUATION
    # ========================================================================

    def evaluate(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> ControlResult:
        """
        Execute the authoritative Logic Control lifecycle.

        Unlike the previous implementation, this is the single normal
        Logic execution path:

            validate
                ↓
            evaluate_logic
                ↓
            validate result
                ↓
            ControlResult
        """

        time = _finite_float(
            time,
            "Logic evaluation time",
        )

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

        result = self._evaluate_logic_safe(
            normalized_state,
            normalized_inputs,
            time,
        )

        self.validate_logic_result(
            result
        )

        return result.as_control_result()

    def _evaluate_logic_safe(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        """Wrap implementation errors in the Logic error hierarchy."""

        try:
            result = self.evaluate_logic(
                state,
                inputs,
                time,
            )
        except LogicControlError:
            raise
        except Exception as exc:
            raise LogicEvaluationError(
                f"{self.component_id}: "
                "logic evaluation failed."
            ) from exc

        if not isinstance(
            result,
            LogicControlResult,
        ):
            raise LogicEvaluationError(
                f"{self.component_id}: "
                "evaluate_logic() must return "
                "LogicControlResult."
            )

        return result

    # ========================================================================
    # RESULT VALIDATION
    # ========================================================================

    def validate_logic_result(
        self,
        result: LogicControlResult,
    ) -> None:
        """
        Validate a complete LogicControlResult.
        """

        if not isinstance(
            result,
            LogicControlResult,
        ):
            raise LogicEvaluationError(
                f"{self.component_id}: "
                "invalid LogicControlResult."
            )

        if result.time != float(
            result.time
        ):
            raise LogicEvaluationError(
                f"{self.component_id}: "
                "invalid result time."
            )

        expected_states = set(
            self.logic_state_names
        )

        actual_states = set(
            result.state
        )

        missing = (
            expected_states - actual_states
        )

        unknown = (
            actual_states - expected_states
        )

        if missing:
            raise LogicStateError(
                f"{self.component_id}: "
                f"result missing logic states: "
                f"{sorted(missing)}"
            )

        if unknown:
            raise LogicStateError(
                f"{self.component_id}: "
                f"result contains unknown logic states: "
                f"{sorted(unknown)}"
            )

        definitions = {
            definition.name: definition
            for definition
            in self.logic_state_definition()
        }

        for name, value in result.state.items():
            definition = definitions[name]

            _validate_value(
                name,
                value,
                definition.value_type,
                LogicStateError,
            )

        try:
            self.validate_outputs(
                result.outputs
            )
        except Exception as exc:
            if isinstance(
                exc,
                LogicOutputError,
            ):
                raise

            raise LogicOutputError(
                f"{self.component_id}: "
                "invalid logic outputs."
            ) from exc

    # ========================================================================
    # RESET
    # ========================================================================

    def reset_logic(
        self,
    ) -> State:
        """
        Return a deterministic initial Logic state.
        """

        return dict(
            self.initial_state()
        )

    def reset(
        self,
        inputs: Inputs | None = None,
    ) -> Mapping[str, SignalValue]:
        """
        Common Control lifecycle reset.
        """

        return dict(
            self.initial_state(
                inputs
            )
        )

    # ========================================================================
    # STATE TRANSITIONS
    # ========================================================================

    def transition(
        self,
        previous: State,
        current: State,
    ) -> Mapping[
        str,
        tuple[
            SignalValue,
            SignalValue,
        ],
    ]:
        """
        Return persistent Logic state values that changed.

        No mutation occurs.
        """

        previous_state = (
            self.validate_logic_state(
                previous
            )
        )

        current_state = (
            self.validate_logic_state(
                current
            )
        )

        changes: dict[
            str,
            tuple[
                SignalValue,
                SignalValue,
            ],
        ] = {}

        for name in self.logic_state_names:
            old = previous_state[name]
            new = current_state[name]

            if old != new:
                changes[name] = (
                    old,
                    new,
                )

        return changes

    # ========================================================================
    # EDGE DETECTION
    # ========================================================================

    @staticmethod
    def detect_edge(
        previous: bool,
        current: bool,
    ) -> LogicEdge:
        """
        Detect a Boolean transition.
        """

        if not isinstance(
            previous,
            bool,
        ):
            raise LogicInputError(
                "Previous edge value must be Boolean."
            )

        if not isinstance(
            current,
            bool,
        ):
            raise LogicInputError(
                "Current edge value must be Boolean."
            )

        if not previous and current:
            return LogicEdge.RISING

        if previous and not current:
            return LogicEdge.FALLING

        return LogicEdge.NONE

    # ========================================================================
    # EVENT HELPERS
    # ========================================================================

    def state_change_events(
        self,
        previous: State,
        current: State,
        time: float,
    ) -> tuple[LogicEvent, ...]:
        """
        Create state-change event descriptions.

        Dispatch remains outside Core Control.
        """

        changes = self.transition(
            previous,
            current,
        )

        return tuple(
            LogicEvent(
                event_type=(
                    LogicEventType.STATE_CHANGED
                ),
                component_id=self.component_id,
                signal_name=name,
                previous_value=old,
                current_value=new,
                time=time,
            )
            for name, (
                old,
                new,
            ) in changes.items()
        )


# ============================================================================
# MODULE HELPERS
# ============================================================================


def _finite_float(
    value: float,
    name: str,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise LogicConfigurationError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(result):
        raise LogicConfigurationError(
            f"{name} must be finite."
        )

    return result


def _validate_value(
    name: str,
    value: SignalValue,
    expected_type: type,
    error_type: type[LogicControlError],
) -> None:
    """
    Validate a Logic value while preserving Boolean type semantics.

    In particular, ``bool`` is not accepted as an ``int``/``float`` value
    merely because Python's bool subclasses int.
    """

    if expected_type is bool:
        valid = isinstance(
            value,
            bool,
        )

    elif expected_type is int:
        valid = (
            isinstance(value, int)
            and not isinstance(value, bool)
        )

    elif expected_type is float:
        valid = (
            isinstance(
                value,
                (int, float),
            )
            and not isinstance(
                value,
                bool,
            )
        )

    else:
        valid = False

    if not valid:
        raise error_type(
            f"Logic value '{name}' must be "
            f"{expected_type.__name__}."
        )

    if (
        isinstance(
            value,
            (int, float),
        )
        and not isinstance(
            value,
            bool,
        )
        and not math.isfinite(
            float(value)
        )
    ):
        raise error_type(
            f"Logic value '{name}' must be finite."
        )


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
