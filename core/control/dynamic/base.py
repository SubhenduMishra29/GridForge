```python
"""
GridForge V2 - Dynamic Control Base Contracts
==============================================

Author:
    Subhendu Mishra

File:
    core/control/dynamic/base.py

Purpose
-------
Defines the Core Control-domain contract for continuous/dynamic
control components.

This contract is the bridge between:

    core/control
        and
    core/solver/dynamics

Concrete implementations such as:

    AVR
    PSS
    Governor
    Exciter controllers
    Turbine/governor controllers
    Inverter controllers

remain outside Core, primarily under:

    plugins/dynamics/

Architectural Rules
-------------------
1. This module defines contracts only.
2. It does not implement AVR/PSS/Governor equations.
3. It does not perform numerical integration.
4. It does not advance simulation time.
5. It does not solve DAEs.
6. It does not access core/model directly.
7. It does not import plugins.
8. Derivatives belong to the dynamic component contract.
9. Integration belongs exclusively to core/solver/dynamics.
10. Dynamic controller state is local control state.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

from ..base import (
    ControlComponent,
    ControlConfigurationError,
    ControlKind,
    ControlResult,
    ControlSignal,
    Inputs,
    Outputs,
    SignalRole,
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


class DynamicControlError(RuntimeError):
    """Base error for Dynamic Control."""


class DynamicConfigurationError(
    DynamicControlError,
):
    """Invalid dynamic-control configuration."""


class DynamicStateError(
    DynamicControlError,
):
    """Invalid dynamic-control state."""


class DynamicDerivativeError(
    DynamicControlError,
):
    """Invalid dynamic derivative result."""


class DynamicInputError(
    DynamicControlError,
):
    """Invalid dynamic-control input."""


# ============================================================================
# STATE DEFINITION
# ============================================================================


@dataclass(frozen=True)
class DynamicStateDefinition:
    """
    Definition of one continuous dynamic-control state.

    This is intentionally separate from the generic StateVariable because
    dynamic states have additional numerical semantics.

    Parameters
    ----------
    name:
        Stable local state name.

    unit:
        Engineering unit.

    description:
        Human-readable description.

    default:
        Initial numerical value.

    """

    name: str
    unit: str = ""
    description: str = ""
    default: float = 0.0

    def __post_init__(self) -> None:
        name = str(
            self.name
        ).strip()

        if not name:
            raise DynamicConfigurationError(
                "Dynamic state name cannot be empty."
            )

        default = _finite_float(
            self.default,
            "default",
        )

        object.__setattr__(
            self,
            "name",
            name,
        )

        object.__setattr__(
            self,
            "default",
            default,
        )


# ============================================================================
# DYNAMIC RESULT
# ============================================================================


@dataclass(frozen=True)
class DynamicControlResult:
    """
    Explicit result of one dynamic-control evaluation.

    This object contains:

        outputs
        derivatives
        time
        diagnostics

    It deliberately does NOT contain:

        integrated state
        time-step information
        solver state
        algebraic solution

    Those belong to the solver boundary.
    """

    outputs: Mapping[str, SignalValue]
    derivatives: Mapping[str, float]
    time: float
    diagnostics: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        time = _finite_float(
            self.time,
            "time",
        )

        outputs = dict(
            self.outputs
        )

        derivatives = {
            str(name): _finite_float(
                value,
                f"derivative '{name}'",
            )
            for name, value
            in self.derivatives.items()
        }

        object.__setattr__(
            self,
            "time",
            time,
        )

        object.__setattr__(
            self,
            "outputs",
            outputs,
        )

        object.__setattr__(
            self,
            "derivatives",
            derivatives,
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
        Convert to the common ControlResult contract.
        """

        return ControlResult(
            outputs=self.outputs,
            derivatives=self.derivatives,
            time=self.time,
            diagnostics=self.diagnostics,
        )


# ============================================================================
# DYNAMIC CONTROL COMPONENT
# ============================================================================


class DynamicControlComponent(
    ControlComponent,
):
    """
    Base contract for all continuous/dynamic Control components.

    Concrete implementations must provide:

        component_id
        component_type
        input_definition()
        output_definition()
        dynamic_state_definition()
        derivatives()
        output()

    The component is evaluated at an explicit time and state.

    No integration occurs here.

    Example conceptual implementation:

        class AVR(DynamicControlComponent):

            def derivatives(...):
                ...

            def output(...):
                ...

    The solver is responsible for consuming the derivatives.
    """

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    def control_kind(
        self,
    ) -> ControlKind:
        """
        Dynamic components always belong to the Dynamic branch.
        """

        return ControlKind.DYNAMIC

    # ========================================================================
    # STATE
    # ========================================================================

    @abstractmethod
    def dynamic_state_definition(
        self,
    ) -> Sequence[
        DynamicStateDefinition
    ]:
        """
        Return the authoritative continuous-state definitions.
        """

        raise NotImplementedError

    @property
    def dynamic_state_names(
        self,
    ) -> tuple[str, ...]:
        """
        Return dynamic-state names in deterministic order.
        """

        return tuple(
            definition.name
            for definition
            in self.dynamic_state_definition()
        )

    @property
    def dynamic_state_size(
        self,
    ) -> int:
        """
        Number of continuous dynamic states.
        """

        return len(
            self.dynamic_state_names
        )

    def state_definition(
        self,
    ) -> Sequence[StateVariable]:
        """
        Adapt dynamic-state definitions to the generic Control state
        contract.

        Dynamic states are always numeric floating-point states.
        """

        return tuple(
            StateVariable(
                name=definition.name,
                unit=definition.unit,
                description=definition.description,
                value_type=float,
                default=definition.default,
            )
            for definition
            in self.dynamic_state_definition()
        )

    def initial_state(
        self,
        inputs: Inputs | None = None,
    ) -> Mapping[str, float]:
        """
        Return initial dynamic state.

        By default this is constructed from the state definitions.

        Concrete controllers may override this when initial conditions
        depend on validated inputs or operating conditions.
        """

        return {
            definition.name:
                definition.default
            for definition
            in self.dynamic_state_definition()
        }

    def control_state(
        self,
        state: State,
    ) -> ControlState:
        """
        Convert a generic State mapping into ControlState using the
        dynamic state definitions.
        """

        definitions = self.state_definition()

        return ControlState(
            definitions=definitions,
            values=state,
        )

    # ========================================================================
    # INPUT CONTRACT
    # ========================================================================

    def validate_dynamic_inputs(
        self,
        inputs: Inputs,
    ) -> dict[str, SignalValue]:
        """
        Validate inputs and enforce numeric dynamic-control inputs.

        Boolean inputs are permitted because dynamic controllers may
        legitimately have enable/status signals.
        """

        normalized = self.validate_inputs(
            inputs
        )

        return dict(
            normalized
        )

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
        Calculate dx/dt for every dynamic state.

        This method must calculate derivatives only.

        It must NOT:

            - integrate
            - update state
            - advance time
            - call a solver
            - mutate network/model objects
        """

        raise NotImplementedError

    def validate_derivatives(
        self,
        derivatives: Mapping[str, float],
    ) -> dict[str, float]:
        """
        Validate derivative names and values.
        """

        if derivatives is None:
            raise DynamicDerivativeError(
                f"{self.component_id}: "
                "derivatives cannot be None."
            )

        expected = set(
            self.dynamic_state_names
        )

        actual = {
            str(name)
            for name in derivatives
        }

        missing = expected - actual

        if missing:
            raise DynamicDerivativeError(
                f"{self.component_id}: "
                f"missing derivatives: {sorted(missing)}"
            )

        unknown = actual - expected

        if unknown:
            raise DynamicDerivativeError(
                f"{self.component_id}: "
                f"unknown derivatives: {sorted(unknown)}"
            )

        result: dict[str, float] = {}

        for name in self.dynamic_state_names:
            value = _finite_float(
                derivatives[name],
                f"derivative '{name}'",
            )

            result[name] = value

        return result

    # ========================================================================
    # OUTPUTS
    # ========================================================================

    @abstractmethod
    def output(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> Outputs:
        """
        Calculate dynamic-controller outputs.

        Output calculation must be side-effect free.
        """

        raise NotImplementedError

    # ========================================================================
    # EVALUATION
    # ========================================================================

    def evaluate_dynamic(
        self,
        *,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> DynamicControlResult:
        """
        Evaluate derivatives and outputs at one explicit time/state point.

        This method performs no integration.
        """

        time = _finite_float(
            time,
            "time",
        )

        normalized_state = self.validate_state(
            state
        )

        normalized_inputs = (
            self.validate_dynamic_inputs(
                inputs
            )
        )

        derivatives = self.derivatives(
            normalized_state,
            normalized_inputs,
            time,
        )

        derivatives = (
            self.validate_derivatives(
                derivatives
            )
        )

        outputs = self.output(
            normalized_state,
            normalized_inputs,
            time,
        )

        outputs = self.validate_outputs(
            outputs
        )

        return DynamicControlResult(
            outputs=outputs,
            derivatives=derivatives,
            time=time,
        )

    def evaluate(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> ControlResult:
        """
        Implement the common ControlComponent evaluation contract.

        The result contains derivatives but no integrated state.
        """

        result = self.evaluate_dynamic(
            state=state,
            inputs=inputs,
            time=time,
        )

        return result.as_control_result()

    # ========================================================================
    # SOLVER BOUNDARY
    # ========================================================================

    def derivative_vector(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> tuple[float, ...]:
        """
        Return derivatives in deterministic state order.

        This is the representation consumed by the numerical solver.

        No integration occurs here.
        """

        result = self.evaluate_dynamic(
            state=state,
            inputs=inputs,
            time=time,
        )

        return tuple(
            result.derivatives[name]
            for name
            in self.dynamic_state_names
        )

    def state_vector(
        self,
        state: State,
    ) -> tuple[float, ...]:
        """
        Convert named dynamic state to deterministic numerical order.

        This performs representation conversion only.
        """

        normalized = self.validate_state(
            state
        )

        return tuple(
            float(
                normalized[name]
            )
            for name
            in self.dynamic_state_names
        )

    def state_from_vector(
        self,
        vector: Sequence[float],
    ) -> dict[str, float]:
        """
        Convert a numerical state vector into named state values.

        No integration occurs here.
        """

        if len(vector) != self.dynamic_state_size:
            raise DynamicStateError(
                f"{self.component_id}: "
                f"expected state vector size "
                f"{self.dynamic_state_size}, "
                f"got {len(vector)}."
            )

        result: dict[str, float] = {}

        for name, value in zip(
            self.dynamic_state_names,
            vector,
        ):
            result[name] = _finite_float(
                value,
                f"state '{name}'",
            )

        return result

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def dynamic_diagnostics(
        self,
    ) -> Mapping[str, Any]:
        """
        Return dynamic-control diagnostic metadata.
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
            "dynamic_state_names":
                self.dynamic_state_names,
            "dynamic_state_size":
                self.dynamic_state_size,
            "input_names":
                self.input_names,
            "output_names":
                self.output_names,
        }


# ============================================================================
# NUMERICAL HELPERS
# ============================================================================


def _finite_float(
    value: float,
    name: str,
) -> float:
    """
    Convert a value to finite float.
    """

    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise DynamicConfigurationError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(
        result
    ):
        raise DynamicConfigurationError(
            f"{name} must be finite."
        )

    return result


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "DynamicStateDefinition",
    "DynamicControlResult",
    "DynamicControlComponent",
    "DynamicControlError",
    "DynamicConfigurationError",
    "DynamicStateError",
    "DynamicDerivativeError",
    "DynamicInputError",
]
