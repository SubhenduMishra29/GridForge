"""
GridForge V2 - Control Domain Base Contracts
=============================================

Author:
    Subhendu Mishra

File:
    core/control/base.py

Purpose
-------
Defines the authoritative, headless Control-domain contract.

This module does NOT implement AVR, Governor, PSS, inverter control,
or any other concrete controller.

Concrete implementations live in plugins, primarily:

    plugins/dynamics/avr/
    plugins/dynamics/governor/
    plugins/dynamics/pss/

Relationship to DynamicPlugin
-----------------------------
DynamicPlugin defines the generic executable dynamic-component
contract used by the dynamic plugin framework.

ControlComponent adds the semantic contract required by the
GridForge Control domain:

    state
    inputs
    outputs
    references
    derivatives
    time

ControlComponent does not own numerical integration.

The solver remains responsible for numerical integration and global
dynamic-state ownership.

Frozen architectural rule
-------------------------
Core Control defines contracts.

Plugins implement those contracts.

Core Control must never import concrete plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Sequence

import numpy as np


# ============================================================================
# TYPE ALIASES
# ============================================================================

Scalar = float | int | np.floating | np.integer

State = Mapping[str, float]
Inputs = Mapping[str, float]
Outputs = Mapping[str, float]

MutableState = MutableMapping[str, float]


# ============================================================================
# ERRORS
# ============================================================================


class ControlError(RuntimeError):
    """Base exception for Control-domain errors."""


class ControlConfigurationError(ControlError):
    """Invalid controller configuration."""


class ControlStateError(ControlError):
    """Invalid controller state."""


class ControlInputError(ControlError):
    """Invalid controller input."""


class ControlOutputError(ControlError):
    """Invalid controller output."""


# ============================================================================
# SIGNAL / PORT DESCRIPTORS
# ============================================================================


@dataclass(frozen=True)
class ControlSignal:
    """
    Description of one controller signal.

    This is metadata only.

    It does not contain mutable runtime state.
    """

    name: str
    unit: str = ""
    description: str = ""
    required: bool = True

    def __post_init__(self) -> None:
        name = str(self.name).strip()

        if not name:
            raise ValueError(
                "ControlSignal name cannot be empty."
            )

        object.__setattr__(
            self,
            "name",
            name,
        )


# ============================================================================
# CONTROL EVALUATION RESULT
# ============================================================================


@dataclass(frozen=True)
class ControlResult:
    """
    Result produced by one controller evaluation.

    Attributes
    ----------
    derivatives:
        Controller-state derivatives.

    outputs:
        Controller outputs.

    time:
        Evaluation time.

    diagnostics:
        Optional immutable diagnostic values.

    The solver may consume ``derivatives`` while the controlled
    dynamic component consumes ``outputs``.
    """

    derivatives: Mapping[str, float]
    outputs: Mapping[str, float]
    time: float
    diagnostics: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        time = float(self.time)

        if not np.isfinite(time):
            raise ValueError(
                "ControlResult time must be finite."
            )

        derivatives = {
            str(name): float(value)
            for name, value in self.derivatives.items()
        }

        outputs = {
            str(name): float(value)
            for name, value in self.outputs.items()
        }

        for name, value in (
            *derivatives.items(),
            *outputs.items(),
        ):
            if not np.isfinite(value):
                raise ValueError(
                    f"Control result '{name}' "
                    "must be finite."
                )

        object.__setattr__(
            self,
            "derivatives",
            derivatives,
        )

        object.__setattr__(
            self,
            "outputs",
            outputs,
        )

        object.__setattr__(
            self,
            "time",
            time,
        )

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
    Authoritative Control-domain contract.

    A ControlComponent represents an engineering control law.

    Examples
    --------
    - AVR
    - Governor
    - PSS
    - inverter controller
    - plant controller

    It may contain dynamic internal state, but it does not own
    numerical integration.

    State
    -----
    Controller state is represented explicitly as named scalar
    values.

    Inputs
    ------
    Runtime measurements, references and external signals.

    Outputs
    -------
    Commands/signals supplied to controlled dynamic components or
    other controllers.

    Time
    ----
    Evaluation time is always explicit.

    This makes the contract compatible with the frozen dynamic
    solver derivative contract:

        derivative(state, time) -> dx/dt
    """

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    @abstractmethod
    def component_id(self) -> str:
        """
        Stable runtime identifier.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def component_type(self) -> str:
        """
        Engineering controller type.

        Examples:

            "avr"
            "governor"
            "pss"
        """
        raise NotImplementedError

    @property
    def version(self) -> str:
        """
        Controller contract/implementation version.
        """

        return "1.0"

    # ========================================================================
    # STATE DEFINITION
    # ========================================================================

    @abstractmethod
    def state_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Return definitions of all dynamic controller states.
        """
        raise NotImplementedError

    @property
    def state_names(self) -> tuple[str, ...]:
        """Return ordered controller-state names."""

        return tuple(
            signal.name
            for signal in self.state_definition()
        )

    @property
    def state_size(self) -> int:
        """Return number of controller states."""

        return len(self.state_names)

    # ========================================================================
    # INPUT DEFINITION
    # ========================================================================

    @abstractmethod
    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Return definitions of controller inputs.
        """
        raise NotImplementedError

    @property
    def input_names(self) -> tuple[str, ...]:
        """Return ordered input names."""

        return tuple(
            signal.name
            for signal in self.input_definition()
        )

    # ========================================================================
    # OUTPUT DEFINITION
    # ========================================================================

    @abstractmethod
    def output_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Return definitions of controller outputs.
        """
        raise NotImplementedError

    @property
    def output_names(self) -> tuple[str, ...]:
        """Return ordered output names."""

        return tuple(
            signal.name
            for signal in self.output_definition()
        )

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    @abstractmethod
    def initial_state(
        self,
        inputs: Inputs | None = None,
    ) -> Mapping[str, float]:
        """
        Produce the controller's initial dynamic state.

        Initialization does not advance time.
        """

        raise NotImplementedError

    # ========================================================================
    # DERIVATIVES
    # ========================================================================

    @abstractmethod
    def derivatives(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> Mapping[str, float]:
        """
        Evaluate controller-state derivatives.

        Contract:

            derivatives(state, inputs, time)
                -> dstate/dt

        Numerical integration is NOT performed here.
        """

        raise NotImplementedError

    # ========================================================================
    # OUTPUT
    # ========================================================================

    @abstractmethod
    def output(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> Mapping[str, float]:
        """
        Evaluate controller outputs.
        """

        raise NotImplementedError

    # ========================================================================
    # COMPLETE EVALUATION
    # ========================================================================

    def evaluate(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> ControlResult:
        """
        Evaluate derivatives and outputs together.

        Concrete implementations may override this if their
        evaluation can be optimized, but the semantic contract
        remains unchanged.
        """

        time = self._validate_time(time)

        normalized_state = self.validate_state(
            state
        )

        normalized_inputs = self.validate_inputs(
            inputs
        )

        derivatives = self.derivatives(
            normalized_state,
            normalized_inputs,
            time,
        )

        outputs = self.output(
            normalized_state,
            normalized_inputs,
            time,
        )

        return ControlResult(
            derivatives=derivatives,
            outputs=outputs,
            time=time,
        )

    # ========================================================================
    # RESET
    # ========================================================================

    def reset(
        self,
        inputs: Inputs | None = None,
    ) -> Mapping[str, float]:
        """
        Return a fresh initialized controller state.

        Controllers must not silently retain numerical state here.
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
    ) -> dict[str, float]:
        """
        Validate and normalize controller state.
        """

        if state is None:
            raise ControlStateError(
                f"{self.component_id}: "
                "state cannot be None."
            )

        expected = set(
            self.state_names
        )

        actual = {
            str(name)
            for name in state
        }

        missing = expected - actual
        unknown = actual - expected

        if missing:
            raise ControlStateError(
                f"{self.component_id}: "
                f"missing state values: "
                f"{sorted(missing)}"
            )

        if unknown:
            raise ControlStateError(
                f"{self.component_id}: "
                f"unknown state values: "
                f"{sorted(unknown)}"
            )

        result: dict[str, float] = {}

        for name in self.state_names:
            try:
                value = float(
                    state[name]
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ControlStateError(
                    f"{self.component_id}: "
                    f"state '{name}' must be numeric."
                ) from exc

            if not np.isfinite(value):
                raise ControlStateError(
                    f"{self.component_id}: "
                    f"state '{name}' must be finite."
                )

            result[name] = value

        return result

    def validate_inputs(
        self,
        inputs: Inputs,
    ) -> dict[str, float]:
        """
        Validate and normalize controller inputs.
        """

        if inputs is None:
            raise ControlInputError(
                f"{self.component_id}: "
                "inputs cannot be None."
            )

        definitions = {
            signal.name: signal
            for signal
            in self.input_definition()
        }

        actual = {
            str(name)
            for name in inputs
        }

        required = {
            name
            for name, signal
            in definitions.items()
            if signal.required
        }

        missing = required - actual

        if missing:
            raise ControlInputError(
                f"{self.component_id}: "
                f"missing inputs: "
                f"{sorted(missing)}"
            )

        unknown = (
            actual
            - set(definitions)
        )

        if unknown:
            raise ControlInputError(
                f"{self.component_id}: "
                f"unknown inputs: "
                f"{sorted(unknown)}"
            )

        result: dict[str, float] = {}

        for name in actual:
            try:
                value = float(
                    inputs[name]
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ControlInputError(
                    f"{self.component_id}: "
                    f"input '{name}' must be numeric."
                ) from exc

            if not np.isfinite(value):
                raise ControlInputError(
                    f"{self.component_id}: "
                    f"input '{name}' must be finite."
                )

            result[name] = value

        return result

    def validate_outputs(
        self,
        outputs: Outputs,
    ) -> dict[str, float]:
        """
        Validate controller outputs.
        """

        if outputs is None:
            raise ControlOutputError(
                f"{self.component_id}: "
                "outputs cannot be None."
            )

        expected = set(
            self.output_names
        )

        actual = {
            str(name)
            for name in outputs
        }

        missing = expected - actual

        if missing:
            raise ControlOutputError(
                f"{self.component_id}: "
                f"missing outputs: "
                f"{sorted(missing)}"
            )

        unknown = actual - expected

        if unknown:
            raise ControlOutputError(
                f"{self.component_id}: "
                f"unknown outputs: "
                f"{sorted(unknown)}"
            )

        result: dict[str, float] = {}

        for name in self.output_names:
            try:
                value = float(
                    outputs[name]
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ControlOutputError(
                    f"{self.component_id}: "
                    f"output '{name}' must be numeric."
                ) from exc

            if not np.isfinite(value):
                raise ControlOutputError(
                    f"{self.component_id}: "
                    f"output '{name}' must be finite."
                )

            result[name] = value

        return result

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def diagnostics(
        self,
    ) -> Mapping[str, Any]:
        """
        Return non-authoritative diagnostic metadata.
        """

        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "version": self.version,
            "state_names": self.state_names,
            "input_names": self.input_names,
            "output_names": self.output_names,
        }

    # ========================================================================
    # SUMMARY
    # ========================================================================

    def summary(
        self,
    ) -> Mapping[str, Any]:
        """
        Return a serializable controller summary.
        """

        return self.diagnostics()

    # ========================================================================
    # VALIDATION HELPERS
    # ========================================================================

    @staticmethod
    def _validate_time(
        time: float,
    ) -> float:
        """Validate explicit evaluation time."""

        try:
            value = float(time)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ControlConfigurationError(
                "Controller time must be numeric."
            ) from exc

        if not np.isfinite(value):
            raise ControlConfigurationError(
                "Controller time must be finite."
            )

        return value


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "Scalar",
    "State",
    "Inputs",
    "Outputs",
    "MutableState",
    "ControlSignal",
    "ControlResult",
    "ControlError",
    "ControlConfigurationError",
    "ControlStateError",
    "ControlInputError",
    "ControlOutputError",
    "ControlComponent",
]
