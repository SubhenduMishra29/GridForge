"""
GridForge V2 - Control Domain Base Contracts
=============================================

Author:
    Subhendu Mishra

File:
    core/control/base.py

Purpose
-------
Defines the common, headless Control-domain contracts.

The Control domain has two major branches:

    Dynamic Control
        AVR, Governor, PSS, inverter controllers, plant controllers, etc.

    Logic Control
        Contacts, coils, AND/OR/NOT, timers, latches, interlocks,
        sequences, comparators, and related discrete control elements.

This module defines only the COMMON Control contract.

Branch-specific behavior belongs in:

    core/control/dynamic/
    core/control/logic/

Concrete implementations remain in plugins.

Dynamic implementations currently live under:

    plugins/dynamics/

Architectural Rules
-------------------
1. Core Control owns control-domain semantics.
2. Plugins implement Core Control contracts.
3. Core Control never imports concrete plugins.
4. Control does not own electrical/network truth.
5. Control does not perform numerical integration.
6. Dynamic Control supplies derivatives; the solver integrates them.
7. Logic Control evaluates discrete/event semantics; it does not become
   a numerical solver.
8. UI is a projection/editing surface and never owns authoritative
   control state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

import math


# ============================================================================
# TYPE ALIASES
# ============================================================================

SignalValue = float | int | bool

State = Mapping[str, SignalValue]
Inputs = Mapping[str, SignalValue]
Outputs = Mapping[str, SignalValue]


# ============================================================================
# ENUMERATIONS
# ============================================================================


class ControlKind(str, Enum):
    """
    Broad Control-domain classification.
    """

    DYNAMIC = "dynamic"
    LOGIC = "logic"


class SignalRole(str, Enum):
    """
    Semantic role of a Control signal.
    """

    MEASUREMENT = "measurement"
    REFERENCE = "reference"
    INPUT = "input"
    OUTPUT = "output"
    FEEDBACK = "feedback"
    COMMAND = "command"
    STATUS = "status"
    INTERNAL = "internal"


# ============================================================================
# ERRORS
# ============================================================================


class ControlError(RuntimeError):
    """Base exception for Control-domain errors."""


class ControlConfigurationError(ControlError):
    """Invalid Control component configuration."""


class ControlStateError(ControlError):
    """Invalid Control component state."""


class ControlInputError(ControlError):
    """Invalid Control input."""


class ControlOutputError(ControlError):
    """Invalid Control output."""


# ============================================================================
# SIGNAL DEFINITION
# ============================================================================


@dataclass(frozen=True)
class ControlSignal:
    """
    Definition of a Control-domain signal.

    The signal definition contains metadata only.

    It does not own runtime state.

    ``value_type`` is intentionally descriptive rather than prescriptive.
    It supports both:

        continuous/numeric control
        discrete/Boolean logic
    """

    name: str
    role: SignalRole = SignalRole.INPUT
    unit: str = ""
    description: str = ""
    required: bool = True
    value_type: type = float

    def __post_init__(self) -> None:
        name = str(self.name).strip()

        if not name:
            raise ValueError(
                "ControlSignal name cannot be empty."
            )

        object.__setattr__(self, "name", name)

        if not isinstance(self.role, SignalRole):
            object.__setattr__(
                self,
                "role",
                SignalRole(self.role),
            )

        if self.value_type not in (float, int, bool):
            raise ValueError(
                "ControlSignal value_type must be float, int, or bool."
            )


# ============================================================================
# CONTROL RESULT
# ============================================================================


@dataclass(frozen=True)
class ControlResult:
    """
    Result of one Control-component evaluation.

    ``derivatives`` is optional because only Dynamic Control components
    necessarily produce derivatives.

    Logic components may return:

        derivatives = None

    while still producing outputs.

    Numerical integration is never performed here.
    """

    outputs: Mapping[str, SignalValue]
    time: float
    derivatives: Mapping[str, float] | None = None
    diagnostics: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        time = float(self.time)

        if not math.isfinite(time):
            raise ValueError(
                "ControlResult time must be finite."
            )

        outputs = dict(self.outputs)

        for name, value in outputs.items():
            if not isinstance(value, (bool, int, float)):
                raise ValueError(
                    f"Control output '{name}' has unsupported value type."
                )

            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if not math.isfinite(float(value)):
                    raise ValueError(
                        f"Control output '{name}' must be finite."
                    )

        derivatives = None

        if self.derivatives is not None:
            derivatives = {
                str(name): float(value)
                for name, value in self.derivatives.items()
            }

            for name, value in derivatives.items():
                if not math.isfinite(value):
                    raise ValueError(
                        f"Control derivative '{name}' must be finite."
                    )

        object.__setattr__(self, "outputs", outputs)
        object.__setattr__(self, "derivatives", derivatives)
        object.__setattr__(self, "time", time)
        object.__setattr__(
            self,
            "diagnostics",
            dict(self.diagnostics or {}),
        )


# ============================================================================
# CONTROL COMPONENT
# ============================================================================


class ControlComponent(ABC):
    """
    Common authoritative Control-domain contract.

    This is intentionally broader than the DynamicPlugin contract.

    It supports two branches:

        Dynamic Control
            derivative-producing continuous/dynamic components.

        Logic Control
            discrete/event-driven components.

    Concrete branch-specific contracts should extend this class.

    The common layer therefore does NOT require:

        derivatives()
        numerical state
        integration

    Those belong to the appropriate branch.
    """

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    @abstractmethod
    def component_id(self) -> str:
        """
        Stable component identifier.
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def component_type(self) -> str:
        """
        Engineering/control component type.

        Examples:

            avr
            governor
            pss
            contact
            coil
            and
            timer
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def control_kind(self) -> ControlKind:
        """
        Identify whether the component belongs to Dynamic or Logic Control.
        """

        raise NotImplementedError

    @property
    def version(self) -> str:
        """
        Contract/implementation version.
        """

        return "1.0"

    # ========================================================================
    # SIGNAL DEFINITIONS
    # ========================================================================

    @abstractmethod
    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Return the component's external input definitions.
        """

        raise NotImplementedError

    @abstractmethod
    def output_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Return the component's external output definitions.
        """

        raise NotImplementedError

    @property
    def input_names(self) -> tuple[str, ...]:
        """
        Ordered input names.
        """

        return tuple(
            signal.name
            for signal in self.input_definition()
        )

    @property
    def output_names(self) -> tuple[str, ...]:
        """
        Ordered output names.
        """

        return tuple(
            signal.name
            for signal in self.output_definition()
        )

    # ========================================================================
    # STATE
    # ========================================================================

    def state_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Return local component state definitions.

        The common Control contract permits stateless components.

        Dynamic Control components normally override this.

        Logic components may override this when they have persistent
        state, such as timers, counters, or latches.
        """

        return ()

    @property
    def state_names(self) -> tuple[str, ...]:
        """
        Ordered local state names.
        """

        return tuple(
            signal.name
            for signal in self.state_definition()
        )

    @property
    def state_size(self) -> int:
        """
        Number of local state variables.
        """

        return len(self.state_names)

    def initial_state(
        self,
        inputs: Inputs | None = None,
    ) -> Mapping[str, SignalValue]:
        """
        Return initial local component state.

        Stateless components return an empty mapping.
        """

        return {}

    # ========================================================================
    # EVALUATION
    # ========================================================================

    @abstractmethod
    def output(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> Outputs:
        """
        Evaluate component outputs.

        This is the common execution contract for both Dynamic and
        Logic Control.
        """

        raise NotImplementedError

    def evaluate(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> ControlResult:
        """
        Evaluate the component.

        The common implementation evaluates outputs.

        Dynamic Control branch contracts may extend this method to
        additionally return state derivatives.

        Logic Control components normally use the common implementation.
        """

        time = self._validate_time(time)

        normalized_state = self.validate_state(state)
        normalized_inputs = self.validate_inputs(inputs)

        outputs = self.output(
            normalized_state,
            normalized_inputs,
            time,
        )

        outputs = self.validate_outputs(outputs)

        return ControlResult(
            outputs=outputs,
            time=time,
        )

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    def reset(
        self,
        inputs: Inputs | None = None,
    ) -> Mapping[str, SignalValue]:
        """
        Return a fresh initial component state.

        This method does not perform numerical integration.
        """

        return self.initial_state(
            inputs or {}
        )

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def validate_state(
        self,
        state: State,
    ) -> dict[str, SignalValue]:
        """
        Validate local component state.

        Stateless components accept only an empty state.
        """

        if state is None:
            raise ControlStateError(
                f"{self.component_id}: state cannot be None."
            )

        expected = set(self.state_names)
        actual = {str(name) for name in state}

        missing = expected - actual
        unknown = actual - expected

        if missing:
            raise ControlStateError(
                f"{self.component_id}: "
                f"missing state values: {sorted(missing)}"
            )

        if unknown:
            raise ControlStateError(
                f"{self.component_id}: "
                f"unknown state values: {sorted(unknown)}"
            )

        result: dict[str, SignalValue] = {}

        for name in self.state_names:
            value = state[name]

            if not isinstance(value, (bool, int, float)):
                raise ControlStateError(
                    f"{self.component_id}: "
                    f"state '{name}' has unsupported value type."
                )

            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if not math.isfinite(float(value)):
                    raise ControlStateError(
                        f"{self.component_id}: "
                        f"state '{name}' must be finite."
                    )

            result[name] = value

        return result

    def validate_inputs(
        self,
        inputs: Inputs,
    ) -> dict[str, SignalValue]:
        """
        Validate component inputs.
        """

        if inputs is None:
            raise ControlInputError(
                f"{self.component_id}: inputs cannot be None."
            )

        definitions = {
            signal.name: signal
            for signal in self.input_definition()
        }

        actual = {str(name) for name in inputs}

        required = {
            name
            for name, signal in definitions.items()
            if signal.required
        }

        missing = required - actual

        if missing:
            raise ControlInputError(
                f"{self.component_id}: "
                f"missing inputs: {sorted(missing)}"
            )

        unknown = actual - set(definitions)

        if unknown:
            raise ControlInputError(
                f"{self.component_id}: "
                f"unknown inputs: {sorted(unknown)}"
            )

        result: dict[str, SignalValue] = {}

        for name, value in inputs.items():
            definition = definitions[name]

            if not isinstance(value, (bool, int, float)):
                raise ControlInputError(
                    f"{self.component_id}: "
                    f"input '{name}' has unsupported value type."
                )

            if definition.value_type is bool:
                if not isinstance(value, bool):
                    raise ControlInputError(
                        f"{self.component_id}: "
                        f"input '{name}' must be Boolean."
                    )

            elif definition.value_type is float:
                if isinstance(value, bool):
                    raise ControlInputError(
                        f"{self.component_id}: "
                        f"input '{name}' must be numeric."
                    )

                if not math.isfinite(float(value)):
                    raise ControlInputError(
                        f"{self.component_id}: "
                        f"input '{name}' must be finite."
                    )

            result[name] = value

        return result

    def validate_outputs(
        self,
        outputs: Outputs,
    ) -> dict[str, SignalValue]:
        """
        Validate component outputs.
        """

        if outputs is None:
            raise ControlOutputError(
                f"{self.component_id}: outputs cannot be None."
            )

        definitions = {
            signal.name: signal
            for signal in self.output_definition()
        }

        expected = set(definitions)
        actual = {str(name) for name in outputs}

        missing = expected - actual

        if missing:
            raise ControlOutputError(
                f"{self.component_id}: "
                f"missing outputs: {sorted(missing)}"
            )

        unknown = actual - expected

        if unknown:
            raise ControlOutputError(
                f"{self.component_id}: "
                f"unknown outputs: {sorted(unknown)}"
            )

        result: dict[str, SignalValue] = {}

        for name, value in outputs.items():
            definition = definitions[name]

            if not isinstance(value, (bool, int, float)):
                raise ControlOutputError(
                    f"{self.component_id}: "
                    f"output '{name}' has unsupported value type."
                )

            if definition.value_type is bool:
                if not isinstance(value, bool):
                    raise ControlOutputError(
                        f"{self.component_id}: "
                        f"output '{name}' must be Boolean."
                    )

            elif definition.value_type is float:
                if isinstance(value, bool):
                    raise ControlOutputError(
                        f"{self.component_id}: "
                        f"output '{name}' must be numeric."
                    )

                if not math.isfinite(float(value)):
                    raise ControlOutputError(
                        f"{self.component_id}: "
                        f"output '{name}' must be finite."
                    )

            result[name] = value

        return result

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def diagnostics(self) -> Mapping[str, Any]:
        """
        Return non-authoritative diagnostic metadata.
        """

        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "control_kind": self.control_kind.value,
            "version": self.version,
            "state_names": self.state_names,
            "input_names": self.input_names,
            "output_names": self.output_names,
        }

    def summary(self) -> Mapping[str, Any]:
        """
        Return a serializable component summary.
        """

        return self.diagnostics()

    # ========================================================================
    # INTERNAL VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_time(time: float) -> float:
        """
        Validate explicit evaluation time.
        """

        try:
            value = float(time)
        except (TypeError, ValueError) as exc:
            raise ControlConfigurationError(
                "Control evaluation time must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ControlConfigurationError(
                "Control evaluation time must be finite."
            )

        return value


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "SignalValue",
    "State",
    "Inputs",
    "Outputs",
    "ControlKind",
    "SignalRole",
    "ControlSignal",
    "ControlResult",
    "ControlError",
    "ControlConfigurationError",
    "ControlStateError",
    "ControlInputError",
    "ControlOutputError",
    "ControlComponent",
]
