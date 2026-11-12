"""GGOV1 exhaust-temperature lead/lag measurement conditioner.

This is the Tsa/Tsb signal-conditioning element only. It does not infer a
plant temperature limit, derive Ldref, or generate a complete FSRT controller
command; those depend on OEM-specific exhaust-temperature/control logic.
"""
from __future__ import annotations

from typing import Any, ClassVar

from plugins.dynamics.base import DynamicPlugin

from .controllers import GGOV1Parameters, _number


class GGOV1TemperatureMeasurement(DynamicPlugin):
    """One-state (1+s*Tsa)/(1+s*Tsb) exhaust-temperature conditioner."""

    model_type = "PSS_E_GGOV1_TEMPERATURE_MEASUREMENT"
    state_names: ClassVar[tuple[str, ...]] = ("filtered_exhaust_temperature",)

    def __init__(self, parameters: GGOV1Parameters) -> None:
        if not isinstance(parameters, GGOV1Parameters):
            raise TypeError("parameters must be GGOV1Parameters")
        if (
            parameters.temperature_lag_time_constant_s == 0.0
            and parameters.temperature_lead_time_constant_s > 0.0
        ):
            raise ValueError("positive Tsa requires positive Tsb for a proper lead-lag filter")
        self.parameters = parameters

    def initial_state(
        self,
        *,
        initial_exhaust_temperature: float,
        **_: Any,
    ) -> tuple[float, ...]:
        return (_number(initial_exhaust_temperature, "initial_exhaust_temperature"),)

    def derivatives(
        self,
        state: tuple[float, ...] | list[float],
        *,
        exhaust_temperature: float,
        **_: Any,
    ) -> tuple[float, ...]:
        self.validate_state(state)
        p = self.parameters
        measured = _number(exhaust_temperature, "exhaust_temperature")
        filtered = _number(state[0], "filtered_exhaust_temperature")
        if p.temperature_lag_time_constant_s == 0.0:
            return (0.0,)
        return (
            (measured - filtered) / p.temperature_lag_time_constant_s,
        )

    def output(
        self,
        state: tuple[float, ...] | list[float],
        *,
        exhaust_temperature: float | None = None,
        **_: Any,
    ) -> float:
        self.validate_state(state)
        p = self.parameters
        filtered = _number(state[0], "filtered_exhaust_temperature")
        if p.temperature_lag_time_constant_s == 0.0:
            if p.temperature_lead_time_constant_s != 0.0:
                raise ValueError("Tsa cannot be positive when Tsb is zero")
            if exhaust_temperature is None:
                raise ValueError("exhaust_temperature is required for the zero-time bypass")
            return _number(exhaust_temperature, "exhaust_temperature")
        measured = (
            filtered if exhaust_temperature is None
            else _number(exhaust_temperature, "exhaust_temperature")
        )
        ratio = (
            p.temperature_lead_time_constant_s
            / p.temperature_lag_time_constant_s
        )
        return filtered + ratio * (measured - filtered)

    def summary(self) -> dict[str, Any]:
        p = self.parameters
        return {
            "model_type": self.model_type,
            "state_names": self.state_names,
            "transfer_function": (
                "(1 + s*Tsa) / (1 + s*Tsb)"
            ),
            "scope": (
                "exhaust-temperature measurement lead/lag only; OEM temperature "
                "limit logic and FSRT composition remain separate"
            ),
        }


__all__ = ["GGOV1TemperatureMeasurement"]
