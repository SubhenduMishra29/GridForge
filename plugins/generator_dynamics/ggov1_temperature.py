"""GGOV1 exhaust-temperature measurement chain.

The measurement path models the Tfload sensor lag followed by the
(1+s*Tsa)/(1+s*Tsb) lead/lag conditioner. The host integrator owns both
states and the measurement timestamp; no private clock or sample history is
created here.
"""
from __future__ import annotations

from typing import Any, ClassVar

from plugins.dynamics.base import DynamicPlugin

from .controllers import GGOV1Parameters, _number


class GGOV1TemperatureMeasurement(DynamicPlugin):
    """Two-state Tfload plus Tsa/Tsb exhaust-temperature conditioner."""

    model_type = "PSS_E_GGOV1_TEMPERATURE_MEASUREMENT"
    state_names: ClassVar[tuple[str, ...]] = (
        "filtered_exhaust_temperature_sensor",
        "filtered_exhaust_temperature_lead_lag",
    )

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
        initial = _number(initial_exhaust_temperature, "initial_exhaust_temperature")
        return (initial, initial)

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
        sensor = _number(state[0], "filtered_exhaust_temperature_sensor")
        lead_lag = _number(state[1], "filtered_exhaust_temperature_lead_lag")

        tfload = p.load_filter_time_constant_s
        tsb = p.temperature_lag_time_constant_s
        d_sensor = 0.0 if tfload == 0.0 else (measured - sensor) / tfload
        lead_lag_input = measured if tfload == 0.0 else sensor
        d_lead_lag = (
            0.0 if tsb == 0.0 else (lead_lag_input - lead_lag) / tsb
        )
        return (d_sensor, d_lead_lag)

    def output(
        self,
        state: tuple[float, ...] | list[float],
        *,
        exhaust_temperature: float | None = None,
        **_: Any,
    ) -> float:
        self.validate_state(state)
        p = self.parameters
        sensor = _number(state[0], "filtered_exhaust_temperature_sensor")
        lead_lag = _number(state[1], "filtered_exhaust_temperature_lead_lag")

        if p.load_filter_time_constant_s == 0.0:
            if exhaust_temperature is None:
                raise ValueError("exhaust_temperature is required for the zero-Tfload bypass")
            lead_lag_input = _number(exhaust_temperature, "exhaust_temperature")
        else:
            lead_lag_input = sensor

        if p.temperature_lag_time_constant_s == 0.0:
            if p.temperature_lead_time_constant_s != 0.0:
                raise ValueError("Tsa cannot be positive when Tsb is zero")
            return lead_lag_input

        ratio = (
            p.temperature_lead_time_constant_s
            / p.temperature_lag_time_constant_s
        )
        return lead_lag + ratio * (lead_lag_input - lead_lag)

    def summary(self) -> dict[str, Any]:
        p = self.parameters
        return {
            "model_type": self.model_type,
            "state_names": self.state_names,
            "transfer_function": (
                "(1 / (1 + s*Tfload)) * (1 + s*Tsa) / (1 + s*Tsb)"
            ),
            "time_constants_s": {
                "Tfload": p.load_filter_time_constant_s,
                "Tsa": p.temperature_lead_time_constant_s,
                "Tsb": p.temperature_lag_time_constant_s,
            },
            "scope": (
                "exhaust-temperature sensor lag and lead/lag conditioning; "
                "OEM temperature reference, maps and plant limiter calibration remain separate"
            ),
        }


__all__ = ["GGOV1TemperatureMeasurement"]
