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

The Logic Control branch supports:

    - AND / OR / NOT / XOR
    - contacts
    - coils
    - timers
    - latches
    - interlocks
    - comparators
    - sequences
    - future PLC / relay-style logic elements

The visual logic-layout/editing canvas is a UI concern. This module
contains no canvas, scene, node, port, graphics, or layout concepts.

Architectural Boundary
----------------------

    UI Logic Canvas
          |
          | commands / DTOs
          v
    Application / Control orchestration
          |
          v
    LogicControlComponent
          |
          +---- LogicState
          |
          +---- LogicInput / LogicOutput
          |
          v
       ControlResult

Rules
-----
1. Logic components are headless domain contracts.
2. Logic components do not access core/model directly.
3. Logic components do not access the electrical network directly.
4. Logic components do not import UI modules.
5. Logic components do not import plugins.
6. Logic evaluation is deterministic.
7. Boolean signal truth remains Boolean.
8. Persistent logic state is explicit.
9. State transitions are discrete; no numerical integration occurs.
10. Components may report events, but event dispatch belongs outside
    this module.
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
    ControlResult,
    Inputs,
    Outputs,
    SignalValue,
    State,
)
from ..state import (
    ControlState,
    StateVariable,
)


# ============================================================================
# ERRORS
# ============================================================================


class LogicControlError(RuntimeError):
    """Base exception for Logic Control."""


class LogicConfigurationError(
    LogicControlError,
):
    """Invalid logic component configuration."""


class LogicInputError(
    LogicControlError,
):
    """Invalid logic input."""


class LogicOutputError(
    LogicControlError,
):
    """Invalid logic output."""


class LogicStateError(
    LogicControlError,
):
    """Invalid logic state."""


class LogicEvaluationError(
    LogicControlError,
):
    """Failure during logic evaluation."""


# ============================================================================
# ENUMERATIONS
# ============================================================================


class LogicEdge(str, Enum):
    """
    Edge semantics used by event-sensitive logic components.
    """

    NONE = "none"
    RISING = "rising"
    FALLING = "falling"


class LogicEventType(str, Enum):
    """
    Generic discrete event categories.

    These are descriptors only. Event dispatch is outside this module.
    """

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
    Definition of one persistent logic state variable.

    Logic state is intentionally separate from numerical dynamic state.

    Typical examples:

        latched
        previous_input
        timer_active
        elapsed
        counter
    """

    name: str
    value_type: type = bool
    default: SignalValue = False
    description: str = ""

    def __post_init__(self) -> None:
        name = str(
            self.name
        ).strip()

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

        _validate_logic_value(
            name,
            self.default,
            self.value_type,
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

    The event is data only. The Control layer does not dispatch it.
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
                f"{self.event_type!r}"
            ) from exc

        try:
            time = float(
                self.time
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise LogicConfigurationError(
                "Logic event time must be numeric."
            ) from exc

        if not math.isfinite(time):
            raise LogicConfigurationError(
                "Logic event time must be finite."
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
            dict(
                self.data or {}
            ),
        )


# ============================================================================
# LOGIC RESULT
# ============================================================================


@dataclass(frozen=True)
class LogicControlResult:
    """
    Result of evaluating one Logic Control component.

    ``outputs`` contain the component's current output values.

    ``state`` contains the resulting persistent discrete state.

    ``events`` describe discrete transitions.

    No numerical derivatives are produced.
    """

    outputs: Mapping[str, SignalValue]
    state: Mapping[str, SignalValue]
    time: float
    events: Sequence[LogicEvent] = ()
    diagnostics: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        time = _finite_float(
            self.time,
            "time",
        )

        outputs = dict(
            self.outputs
        )

        state = dict(
            self.state
        )

        events = tuple(
            self.events
        )

        for event in events:
            if not isinstance(
                event,
                LogicEvent,
            ):
                raise LogicEvaluationError(
                    "All logic events must be "
                    "LogicEvent instances."
                )

        object.__setattr__(
            self,
            "outputs",
            outputs,
        )

        object.__setattr__(
            self,
            "state",
            state,
        )

        object.__setattr__(
            self,
            "time",
            time,
        )

        object.__setattr__(
            self,
            "events",
            events,
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
        Convert the logic result to the common ControlResult contract.

        Persistent logic state remains in diagnostics because the common
        ControlResult represents component outputs and optional
        derivative data, while discrete state ownership remains explicit
        to LogicControlComponent.
        """

        diagnostics = dict(
            self.diagnostics or {}
        )

        diagnostics[
            "logic_state"
        ] = dict(
            self.state
        )

        diagnostics[
            "logic_events"
        ] = tuple(
            self.events
        )

        return ControlResult(
            outputs=self.outputs,
            derivatives=None,
            time=self.time,
            diagnostics=diagnostics,
        )


# ============================================================================
# LOGIC CONTROL COMPONENT
# ============================================================================


class LogicControlComponent(
    ControlComponent,
):
    """
    Base contract for discrete Logic Control components.

    Concrete elements implement the domain behavior while this class
    provides common lifecycle, validation, and deterministic evaluation
    semantics.

    Examples
    --------

        AND gate
        OR gate
        NOT gate
        Contact
        Coil
        Timer
        Latch
        Interlock

    The class is intentionally independent of the UI logic canvas.
    """

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    def control_kind(
        self,
    ) -> ControlKind:
        """
        Logic components always belong to the Logic branch.
        """

        return ControlKind.LOGIC

    # ========================================================================
    # STATE
    # ========================================================================

    def logic_state_definition(
        self,
    ) -> Sequence[
        LogicStateDefinition
    ]:
        """
        Return persistent logic-state definitions.

        Stateless logic elements should return an empty sequence.
        """

        return ()

    @property
    def logic_state_names(
        self,
    ) -> tuple[str, ...]:
        """Return persistent state names in deterministic order."""

        return tuple(
            definition.name
            for definition
            in self.logic_state_definition()
        )

    @property
    def logic_state_size(
        self,
    ) -> int:
        """Return the number of persistent logic states."""

        return len(
            self.logic_state_names
        )

    def state_definition(
        self,
    ) -> Sequence[StateVariable]:
        """
        Adapt LogicStateDefinition objects to the generic Control
        state contract.
        """

        return tuple(
            StateVariable(
                name=definition.name,
                unit="",
                description=definition.description,
                value_type=definition.value_type,
                default=definition.default,
            )
            for definition
            in self.logic_state_definition()
        )

    def initial_state(
        self,
        inputs: Inputs | None = None,
    ) -> Mapping[str, SignalValue]:
        """
        Return initial persistent logic state.
        """

        return {
            definition.name:
                definition.default
            for definition
            in self.logic_state_definition()
        }

    def control_state(
        self,
        state: State,
    ) -> ControlState:
        """
        Convert a generic state mapping into ControlState.
        """

        return ControlState(
            definitions=self.state_definition(),
            values=state,
        )

    # ========================================================================
    # INPUTS
    # ========================================================================

    def validate_logic_inputs(
        self,
        inputs: Inputs,
    ) -> dict[str, SignalValue]:
        """
        Validate logic inputs.

        Boolean inputs are expected for ordinary logic elements.

        Numeric inputs remain permitted because threshold/comparator
        elements are part of the Logic Control branch.
        """

        normalized = self.validate_inputs(
            inputs
        )

        return dict(
            normalized
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
        Evaluate the discrete logic behavior.

        Implementations must not:

            - integrate numerical states
            - access UI
            - mutate network/model truth
            - dispatch external events

        Persistent state changes must be explicitly returned in
        LogicControlResult.state.
        """

        raise NotImplementedError

    def evaluate(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> ControlResult:
        """
        Execute the common ControlComponent contract.
        """

        time = _finite_float(
            time,
            "time",
        )

        normalized_state = self.validate_state(
            state
        )

        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        try:
            result = self.evaluate_logic(
                normalized_state,
                normalized_inputs,
                time,
            )
        except LogicControlError:
            raise
        except Exception as exc:
            raise LogicEvaluationError(
                f"Logic evaluation failed for "
                f"component '{self.component_id}'."
            ) from exc

        if not isinstance(
            result,
            LogicControlResult,
        ):
            raise LogicEvaluationError(
                f"Logic component '{self.component_id}' "
                "must return LogicControlResult."
            )

        self.validate_logic_result(
            result
        )

        return result.as_control_result()

    # ========================================================================
    # RESULT VALIDATION
    # ========================================================================

    def validate_logic_result(
        self,
        result: LogicControlResult,
    ) -> None:
        """
        Validate output and persistent-state contracts.
        """

        expected_states = set(
            self.logic_state_names
        )

        actual_states = set(
            result.state
        )

        missing_states = (
            expected_states - actual_states
        )

        if missing_states:
            raise LogicStateError(
                f"{self.component_id}: "
                f"missing logic states: "
                f"{sorted(missing_states)}"
            )

        unknown_states = (
            actual_states - expected_states
        )

        if unknown_states:
            raise LogicStateError(
                f"{self.component_id}: "
                f"unknown logic states: "
                f"{sorted(unknown_states)}"
            )

        definitions = {
            definition.name: definition
            for definition
            in self.logic_state_definition()
        }

        for name, value in result.state.items():
            definition = definitions[name]

            _validate_logic_value(
                name,
                value,
                definition.value_type,
            )

        outputs = self.validate_outputs(
            result.outputs
        )

        if dict(outputs) != dict(
            result.outputs
        ):
            raise LogicOutputError(
                f"{self.component_id}: "
                "logic output validation changed the output mapping."
            )

    # ========================================================================
    # STATE TRANSITIONS
    # ========================================================================

    def transition(
        self,
        previous: State,
        current: State,
    ) -> Mapping[str, tuple[
        SignalValue,
        SignalValue,
    ]]:
        """
        Return state values that changed.

        The method does not mutate either mapping.
        """

        previous = dict(
            previous
        )

        current = dict(
            current
        )

        expected = set(
            self.logic_state_names
        )

        if set(previous) != expected:
            raise LogicStateError(
                f"{self.component_id}: "
                "previous state does not match "
                "logic-state definition."
            )

        if set(current) != expected:
            raise LogicStateError(
                f"{self.component_id}: "
                "current state does not match "
                "logic-state definition."
            )

        return {
            name: (
                previous[name],
                current[name],
            )
            for name in self.logic_state_names
            if previous[name] != current[name]
        }

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
                "previous must be Boolean."
            )

        if not isinstance(
            current,
            bool,
        ):
            raise LogicInputError(
                "current must be Boolean."
            )

        if (
            not previous
            and current
        ):
            return LogicEdge.RISING

        if (
            previous
            and not current
        ):
            return LogicEdge.FALLING

        return LogicEdge.NONE

    # ========================================================================
    # RESET
    # ========================================================================

    def reset_logic(
        self,
        inputs: Inputs | None = None,
    ) -> Mapping[str, SignalValue]:
        """
        Return reset state.

        Default behavior restores configured defaults.
        """

        return self.initial_state(
            inputs
        )

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def logic_diagnostics(
        self,
    ) -> Mapping[str, Any]:
        """
        Return serializable Logic Control metadata.
        """

        return {
            "component_id":
                self.component_id,
            "component_type":
                self.component_type,
            "control_kind":
                self.control_kind.value,
            "version":
                self.version,
            "logic_state_names":
                self.logic_state_names,
            "logic_state_size":
                self.logic_state_size,
            "input_names":
                self.input_names,
            "output_names":
                self.output_names,
        }


# ============================================================================
# VALUE VALIDATION
# ============================================================================


def _validate_logic_value(
    name: str,
    value: SignalValue,
    expected_type: type,
) -> None:
    """
    Validate a logic-state value.
    """

    if expected_type is bool:
        if not isinstance(
            value,
            bool,
        ):
            raise LogicStateError(
                f"Logic state '{name}' must be Boolean."
            )

        return

    if expected_type is int:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
        ):
            raise LogicStateError(
                f"Logic state '{name}' must be integer."
            )

        return

    if expected_type is float:
        if (
            isinstance(value, bool)
            or not isinstance(
                value,
                (int, float),
            )
        ):
            raise LogicStateError(
                f"Logic state '{name}' must be numeric."
            )

        if not math.isfinite(
            float(value)
        ):
            raise LogicStateError(
                f"Logic state '{name}' must be finite."
            )

        return

    raise LogicConfigurationError(
        f"Unsupported logic-state type for '{name}'."
    )


def _finite_float(
    value: float,
    name: str,
) -> float:
    """
    Convert value to finite float.
    """

    try:
        result = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise LogicConfigurationError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(
        result
    ):
        raise LogicConfigurationError(
            f"{name} must be finite."
        )

    return result


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "LogicEdge",
    "LogicEventType",
    "LogicStateDefinition",
    "LogicEvent",
    "LogicControlResult",
    "LogicControlComponent",
    "LogicControlError",
    "LogicConfigurationError",
    "LogicInputError",
    "LogicOutputError",
    "LogicStateError",
    "LogicEvaluationError",
]
