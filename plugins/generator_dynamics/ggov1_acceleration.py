"""GGOV1 acceleration-control fuel-stroke sub-block.

Implements the NERC/PSS/E block-diagram topology: a first-order filtered
shaft-acceleration signal and an integral fuel-stroke request FSRA. The host
owns the machine acceleration signal, integration time and state vector.
"""
from __future__ import annotations

from typing import Any, ClassVar

from plugins.dynamics.base import DynamicPlugin

from .controllers import GGOV1Parameters, _number


class GGOV1AccelerationLimiter(DynamicPlugin):
    """Two-state acceleration controller: filtered acceleration and FSRA.

    The reference form is d(FSRA)/dt = Ka * (Aset - filtered_acceleration).
    The selected-command tracking input is optional and explicit so the
    composition root can track the integrator while another limiter wins.
    """

    model_type = "PSS_E_GGOV1_ACCELERATION_LIMITER"
    state_names: ClassVar[tuple[str, ...]] = (
        "filtered_acceleration_pu_per_s",
        "acceleration_fuel_request_pu",
    )

    def __init__(self, parameters: GGOV1Parameters) -> None:
        if not isinstance(parameters, GGOV1Parameters):
            raise TypeError("parameters must be GGOV1Parameters")
        self.parameters = parameters

    def initial_state(
        self,
        *,
        initial_acceleration_pu_per_s: float = 0.0,
        initial_fuel_request_pu: float = 0.0,
        **_: Any,
    ) -> tuple[float, ...]:
        return (
            _number(initial_acceleration_pu_per_s, "initial_acceleration_pu_per_s"),
            _number(initial_fuel_request_pu, "initial_fuel_request_pu"),
        )

    def derivatives(
        self,
        state: tuple[float, ...] | list[float],
        *,
        shaft_acceleration_pu_per_s: float,
        selected_fuel_command_pu: float | None = None,
        tracking_time_constant_s: float | None = None,
        **_: Any,
    ) -> tuple[float, ...]:
        self.validate_state(state)
        p = self.parameters
        measured = _number(shaft_acceleration_pu_per_s, "shaft_acceleration_pu_per_s")
        filtered = _number(state[0], "filtered_acceleration_pu_per_s")
        fsra = _number(state[1], "acceleration_fuel_request_pu")
        d_filtered = (
            0.0 if p.acceleration_filter_time_constant_s == 0.0
            else (measured - filtered) / p.acceleration_filter_time_constant_s
        )
        d_fsra = p.acceleration_limiter_gain * (
            p.acceleration_limit_pu_per_s - (
                measured if p.acceleration_filter_time_constant_s == 0.0 else filtered
            )
        )
        if (selected_fuel_command_pu is None) != (tracking_time_constant_s is None):
            raise ValueError(
                "selected_fuel_command_pu and tracking_time_constant_s must be supplied together"
            )
        if selected_fuel_command_pu is not None:
            tracking_time = _number(tracking_time_constant_s, "tracking_time_constant_s")
            if tracking_time <= 0.0:
                raise ValueError("tracking_time_constant_s must be greater than zero")
            selected = _number(selected_fuel_command_pu, "selected_fuel_command_pu")
            d_fsra += (selected - fsra) / tracking_time
        return (d_filtered, d_fsra)

    def output(
        self,
        state: tuple[float, ...] | list[float],
        **_: Any,
    ) -> float:
        self.validate_state(state)
        return _number(state[1], "acceleration_fuel_request_pu")

    def summary(self) -> dict[str, Any]:
        p = self.parameters
        return {
            "model_type": self.model_type,
            "state_names": self.state_names,
            "parameters": p,
            "equation": "d(FSRA)/dt = Ka * (Aset - filtered_shaft_acceleration)",
            "scope": "PSS/E-derived acceleration-control sub-block; plant validation required",
        }


__all__ = ["GGOV1AccelerationLimiter"]
