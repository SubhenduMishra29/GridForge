"""GGOV1 fuel-flow load-limiter PI sub-block.

This implementation follows the explicit load/fuel-flow PI form documented by
NumaSim. It is kept separate from the PSS/E exhaust-temperature detector and
does not claim that the fuel-flow approximation alone reproduces OEM FSRT.
"""
from __future__ import annotations

from typing import Any, ClassVar

from plugins.dynamics.base import DynamicPlugin

from .controllers import GGOV1Parameters, _number


class GGOV1LoadLimiter(DynamicPlugin):
    """Two-state fuel-flow measurement lag and load-limiter PI controller.

    State order: filtered fuel flow, integral fuel-command contribution.
    The returned output is a candidate for the combined load/temperature
    input to GGOV1LowValueSelector; the host decides whether this sub-block
    is enabled and how a plant-specific temperature path is combined.
    """

    model_type = "GGOV1_FUEL_FLOW_LOAD_LIMITER_SUBBLOCK"
    state_names: ClassVar[tuple[str, ...]] = (
        "filtered_fuel_flow_pu",
        "load_limiter_integral_output_pu",
    )

    def __init__(self, parameters: GGOV1Parameters) -> None:
        if not isinstance(parameters, GGOV1Parameters):
            raise TypeError("parameters must be GGOV1Parameters")
        self.parameters = parameters

    def initial_state(
        self,
        *,
        initial_fuel_flow_pu: float,
        initial_integral_output_pu: float = 0.0,
        **_: Any,
    ) -> tuple[float, ...]:
        return (
            _number(initial_fuel_flow_pu, "initial_fuel_flow_pu"),
            _number(initial_integral_output_pu, "initial_integral_output_pu"),
        )

    def _error(
        self,
        state: tuple[float, ...] | list[float],
        *,
        fuel_flow_pu: float | None = None,
    ) -> float:
        p = self.parameters
        measured = (
            _number(fuel_flow_pu, "fuel_flow_pu")
            if p.load_filter_time_constant_s == 0.0
            else _number(state[0], "filtered_fuel_flow_pu")
        )
        return p.load_limit_reference_pu - measured

    def derivatives(
        self,
        state: tuple[float, ...] | list[float],
        *,
        fuel_flow_pu: float,
        selected_fuel_command_pu: float | None = None,
        tracking_time_constant_s: float | None = None,
        **_: Any,
    ) -> tuple[float, ...]:
        self.validate_state(state)
        p = self.parameters
        fuel = _number(fuel_flow_pu, "fuel_flow_pu")
        filtered = _number(state[0], "filtered_fuel_flow_pu")
        integral = _number(state[1], "load_limiter_integral_output_pu")
        d_filtered = (
            0.0 if p.load_filter_time_constant_s == 0.0
            else (fuel - filtered) / p.load_filter_time_constant_s
        )
        error = self._error(state, fuel_flow_pu=fuel)
        d_integral = p.load_integral_gain_per_s * error
        if (selected_fuel_command_pu is None) != (tracking_time_constant_s is None):
            raise ValueError(
                "selected_fuel_command_pu and tracking_time_constant_s must be supplied together"
            )
        if selected_fuel_command_pu is not None:
            tracking_time = _number(tracking_time_constant_s, "tracking_time_constant_s")
            if tracking_time <= 0.0:
                raise ValueError("tracking_time_constant_s must be greater than zero")
            requested = p.load_proportional_gain * error + integral
            selected = _number(selected_fuel_command_pu, "selected_fuel_command_pu")
            d_integral += (selected - requested) / tracking_time
        return (d_filtered, d_integral)

    def output(
        self,
        state: tuple[float, ...] | list[float],
        *,
        fuel_flow_pu: float | None = None,
        **_: Any,
    ) -> float:
        self.validate_state(state)
        p = self.parameters
        error = self._error(state, fuel_flow_pu=fuel_flow_pu)
        integral = _number(state[1], "load_limiter_integral_output_pu")
        from .controllers import _clip\n        return _clip(\n            p.load_proportional_gain * error + integral,\n            p.valve_min_pu,\n            p.valve_max_pu,\n        )

    def summary(self) -> dict[str, Any]:
        p = self.parameters
        return {
            "model_type": self.model_type,
            "state_names": self.state_names,
            "parameters": p,
            "equation": (
                "error = Ldref - filtered_fuel_flow; "
                "FSRT = Kpload * error + load_integral"
            ),
            "scope": (
                "fuel-flow PI load-limiter sub-block; not the full PSS/E "
                "exhaust-temperature controller"
            ),
        }


__all__ = ["GGOV1LoadLimiter"]
