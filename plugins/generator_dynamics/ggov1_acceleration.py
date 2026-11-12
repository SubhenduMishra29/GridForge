"""GGOV1 reduced acceleration limiter fuel-request sub-block.

The host machine model supplies shaft acceleration in pu/s at each integrator
stage. This block filters that signal and forms a proportional fuel reduction
above Aset. It is intentionally a transparent reduced approximation: the
available public component contract identifies Ka, Ta, Aset and the FSRA
output, but does not fully specify every vendor/PSS-E internal realization.
"""
from __future__ import annotations

from typing import Any, ClassVar

from plugins.dynamics.base import DynamicPlugin

from .controllers import GGOV1Parameters, _number


class GGOV1AccelerationLimiter(DynamicPlugin):
    """One-state filtered-acceleration proportional limiter candidate.

    State: filtered shaft acceleration (pu/s).

    The host supplies the physical/model acceleration signal; this class does
    not numerically differentiate speed or own a simulation clock. Its output
    is a competing fuel-stroke candidate for GGOV1LowValueSelector, not the
    final actuator command.
    """

    model_type = "PSS_E_GGOV1_REDUCED_ACCELERATION_LIMITER"
    state_names: ClassVar[tuple[str, ...]] = ("filtered_acceleration_pu_per_s",)

    def __init__(self, parameters: GGOV1Parameters) -> None:
        if not isinstance(parameters, GGOV1Parameters):
            raise TypeError("parameters must be GGOV1Parameters")
        self.parameters = parameters

    def initial_state(
        self,
        *,
        initial_acceleration_pu_per_s: float = 0.0,
        **_: Any,
    ) -> tuple[float, ...]:
        return (_number(initial_acceleration_pu_per_s, "initial_acceleration_pu_per_s"),)

    def derivatives(
        self,
        state: tuple[float, ...] | list[float],
        *,
        shaft_acceleration_pu_per_s: float,
        **_: Any,
    ) -> tuple[float, ...]:
        self.validate_state(state)
        p = self.parameters
        measured = _number(shaft_acceleration_pu_per_s, "shaft_acceleration_pu_per_s")
        filtered = _number(state[0], "filtered_acceleration_pu_per_s")
        if p.acceleration_filter_time_constant_s == 0.0:
            return (0.0,)
        return ((measured - filtered) / p.acceleration_filter_time_constant_s,)

    def output(
        self,
        state: tuple[float, ...] | list[float],
        *,
        governor_fuel_command_pu: float,
        **_: Any,
    ) -> float:
        self.validate_state(state)
        p = self.parameters
        governor_command = _number(governor_fuel_command_pu, "governor_fuel_command_pu")
        acceleration = _number(state[0], "filtered_acceleration_pu_per_s")
        if p.acceleration_limiter_gain == 0.0:
            return governor_command
        excess_acceleration = max(
            0.0, acceleration - p.acceleration_limit_pu_per_s
        )
        reduction = p.acceleration_limiter_gain * excess_acceleration
        return max(p.valve_min_pu, governor_command - reduction)

    def summary(self) -> dict[str, Any]:
        p = self.parameters
        return {
            "model_type": self.model_type,
            "state_names": self.state_names,
            "parameters": p,
            "acceleration_setpoint_pu_per_s": p.acceleration_limit_pu_per_s,
            "acceleration_filter_time_constant_s": p.acceleration_filter_time_constant_s,
            "acceleration_gain": p.acceleration_limiter_gain,
            "scope": (
                "reduced proportional acceleration limiter candidate; "
                "host-supplied shaft acceleration; not a full PSS/E GGOV1 limiter"
            ),
        }


__all__ = ["GGOV1AccelerationLimiter"]
