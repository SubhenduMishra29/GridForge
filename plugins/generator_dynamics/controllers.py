"""Executable first-order generator control models.

These models implement transparent continuous-time blocks that can be
embedded by the transient solver. They deliberately do not own a time loop,
persist runtime state, dispatch protection, or claim a specific IEEE model
certification. The host integrator must evaluate derivatives at every actual
integration stage time.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, ClassVar

from plugins.dynamics.base import DynamicPlugin

from .catalog import GovernorParameters, PrimeMoverParameters


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _clip(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def _deadband(value: float, width: float) -> float:
    if abs(value) <= width:
        return 0.0
    return value - (width if value > 0.0 else -width)


@dataclass(frozen=True, slots=True)
class FirstOrderAVRParameters:
    """Generic transducer/regulator/exciter block; all values are per-unit or seconds."""
    regulator_gain: float
    transducer_time_constant_s: float
    regulator_time_constant_s: float
    exciter_time_constant_s: float
    regulator_min_pu: float
    regulator_max_pu: float
    field_min_pu: float
    field_max_pu: float

    def __post_init__(self) -> None:
        for name in ("regulator_gain", "transducer_time_constant_s",
                     "regulator_time_constant_s", "exciter_time_constant_s"):
            value = _number(getattr(self, name), name)
            if value <= 0.0:
                raise ValueError(f"{name} must be greater than zero")
            object.__setattr__(self, name, value)
        for name in ("regulator_min_pu", "regulator_max_pu", "field_min_pu", "field_max_pu"):
            object.__setattr__(self, name, _number(getattr(self, name), name))
        if self.regulator_min_pu >= self.regulator_max_pu:
            raise ValueError("regulator output limits must be ordered")
        if self.field_min_pu < 0.0 or self.field_min_pu >= self.field_max_pu:
            raise ValueError("field limits must satisfy 0 <= minimum < maximum")


class FirstOrderAVR(DynamicPlugin):
    """Three-state AVR: terminal transducer, regulator output, and field voltage."""
    model_type = "GENERIC_AVR_3STATE"
    state_names: ClassVar[tuple[str, ...]] = (
        "terminal_voltage_filtered_pu", "regulator_output_pu", "field_voltage_pu",
    )

    def __init__(self, parameters: FirstOrderAVRParameters) -> None:
        if not isinstance(parameters, FirstOrderAVRParameters):
            raise TypeError("parameters must be FirstOrderAVRParameters")
        self.parameters = parameters

    def initial_state(self, *, terminal_voltage_pu: float, field_voltage_pu: float,
                      regulator_output_pu: float | None = None, **_: Any) -> tuple[float, ...]:
        vt = _number(terminal_voltage_pu, "terminal_voltage_pu")
        efd = _clip(_number(field_voltage_pu, "field_voltage_pu"),
                    self.parameters.field_min_pu, self.parameters.field_max_pu)
        regulator = efd if regulator_output_pu is None else _clip(
            _number(regulator_output_pu, "regulator_output_pu"),
            self.parameters.regulator_min_pu, self.parameters.regulator_max_pu,
        )
        return (vt, regulator, efd)

    def derivatives(self, state: tuple[float, ...] | list[float], *,
                    terminal_voltage_pu: float, voltage_reference_pu: float,
                    stabilizing_signal_pu: float = 0.0, **_: Any) -> tuple[float, ...]:
        self.validate_state(state)
        vf, regulator, efd = (_number(value, "AVR state") for value in state)
        vt = _number(terminal_voltage_pu, "terminal_voltage_pu")
        reference = _number(voltage_reference_pu, "voltage_reference_pu")
        pss = _number(stabilizing_signal_pu, "stabilizing_signal_pu")
        p = self.parameters
        dvf = (vt - vf) / p.transducer_time_constant_s
        target = _clip(p.regulator_gain * (reference + pss - vf),
                       p.regulator_min_pu, p.regulator_max_pu)
        dreg = (target - regulator) / p.regulator_time_constant_s
        if (regulator >= p.regulator_max_pu and dreg > 0.0) or (
            regulator <= p.regulator_min_pu and dreg < 0.0
        ):
            dreg = 0.0
        field_target = _clip(regulator, p.field_min_pu, p.field_max_pu)
        defd = (field_target - efd) / p.exciter_time_constant_s
        if (efd >= p.field_max_pu and defd > 0.0) or (efd <= p.field_min_pu and defd < 0.0):
            defd = 0.0
        return (dvf, dreg, defd)

    def output(self, state: tuple[float, ...] | list[float], **_: Any) -> float:
        self.validate_state(state)
        return _clip(_number(state[2], "field_voltage_pu"),
                     self.parameters.field_min_pu, self.parameters.field_max_pu)

    def summary(self) -> dict[str, Any]:
        return {"model_type": self.model_type, "state_names": self.state_names,
                "parameters": self.parameters}


class TGOV1Governor(DynamicPlugin):
    """Two-state droop governor and turbine lag with rate/position limits."""
    model_type = "TGOV1_STYLE_GOVERNOR"
    state_names: ClassVar[tuple[str, ...]] = ("valve_position_pu", "mechanical_power_pu")

    def __init__(self, governor: GovernorParameters, prime_mover: PrimeMoverParameters,
                 *, speed_deadband_pu: float = 0.0) -> None:
        if not isinstance(governor, GovernorParameters) or not isinstance(prime_mover, PrimeMoverParameters):
            raise TypeError("governor and prime_mover must use their typed parameter contracts")
        self.governor = governor
        self.prime_mover = prime_mover
        self.speed_deadband_pu = _number(speed_deadband_pu, "speed_deadband_pu")
        if self.speed_deadband_pu < 0.0:
            raise ValueError("speed_deadband_pu must be non-negative")

    def initial_state(self, *, mechanical_power_pu: float,
                      valve_position_pu: float | None = None, **_: Any) -> tuple[float, ...]:
        pm = _number(mechanical_power_pu, "mechanical_power_pu")
        valve = pm if valve_position_pu is None else _number(valve_position_pu, "valve_position_pu")
        if not self.governor.valve_or_gate_min_pu <= valve <= self.governor.valve_or_gate_max_pu:
            raise ValueError("initial valve position is outside configured limits")
        if not self.prime_mover.minimum_output_pu <= pm <= self.prime_mover.maximum_output_pu:
            raise ValueError("initial mechanical power is outside prime-mover limits")
        return (valve, pm)

    def derivatives(self, state: tuple[float, ...] | list[float], *,
                    speed_deviation_pu: float, power_reference_pu: float,
                    **_: Any) -> tuple[float, ...]:
        self.validate_state(state)
        valve, pm = (_number(value, "governor state") for value in state)
        speed = _deadband(_number(speed_deviation_pu, "speed_deviation_pu"), self.speed_deadband_pu)
        reference = _number(power_reference_pu, "power_reference_pu")
        p = self.governor
        droop_fraction = p.droop_percent / 100.0
        target = _clip(reference - speed / droop_fraction,
                       p.valve_or_gate_min_pu, p.valve_or_gate_max_pu)
        dvalve = p.governor_gain * (target - valve) / p.governor_time_constant_s
        if p.rate_limit_pu_per_s is not None:
            dvalve = _clip(dvalve, -p.rate_limit_pu_per_s, p.rate_limit_pu_per_s)
        if (valve >= p.valve_or_gate_max_pu and dvalve > 0.0) or (
            valve <= p.valve_or_gate_min_pu and dvalve < 0.0
        ):
            dvalve = 0.0
        turbine_target = _clip(valve, self.prime_mover.minimum_output_pu,
                               self.prime_mover.maximum_output_pu)
        dpm = (turbine_target - pm) / self.prime_mover.response_time_s
        if (pm >= self.prime_mover.maximum_output_pu and dpm > 0.0) or (
            pm <= self.prime_mover.minimum_output_pu and dpm < 0.0
        ):
            dpm = 0.0
        return (dvalve, dpm)

    def output(self, state: tuple[float, ...] | list[float], **_: Any) -> float:
        self.validate_state(state)
        return _number(state[1], "mechanical_power_pu")

    def summary(self) -> dict[str, Any]:
        return {"model_type": self.model_type, "state_names": self.state_names,
                "governor": self.governor, "prime_mover": self.prime_mover,
                "speed_deadband_pu": self.speed_deadband_pu}


@dataclass(frozen=True, slots=True)
class PSSParameters:
    """Washout plus one lead-lag stabilizer stage."""
    gain: float
    washout_time_constant_s: float
    lead_time_constant_s: float
    lag_time_constant_s: float
    output_min_pu: float
    output_max_pu: float

    def __post_init__(self) -> None:
        for name in ("gain", "washout_time_constant_s", "lead_time_constant_s", "lag_time_constant_s"):
            value = _number(getattr(self, name), name)
            if value <= 0.0:
                raise ValueError(f"{name} must be greater than zero")
            object.__setattr__(self, name, value)
        object.__setattr__(self, "output_min_pu", _number(self.output_min_pu, "output_min_pu"))
        object.__setattr__(self, "output_max_pu", _number(self.output_max_pu, "output_max_pu"))
        if self.output_min_pu >= self.output_max_pu:
            raise ValueError("PSS output limits must be ordered")


class WashoutLeadLagPSS(DynamicPlugin):
    """Two-state speed washout and lead-lag PSS; output is a bounded AVR input."""
    model_type = "WASHOUT_LEAD_LAG_PSS"
    state_names: ClassVar[tuple[str, ...]] = ("washout_state_pu", "lead_lag_state_pu")

    def __init__(self, parameters: PSSParameters) -> None:
        if not isinstance(parameters, PSSParameters):
            raise TypeError("parameters must be PSSParameters")
        self.parameters = parameters

    def initial_state(self, *, speed_deviation_pu: float = 0.0, **_: Any) -> tuple[float, ...]:
        speed = _number(speed_deviation_pu, "speed_deviation_pu")
        return (speed, 0.0)

    def derivatives(self, state: tuple[float, ...] | list[float], *,
                    speed_deviation_pu: float, **_: Any) -> tuple[float, ...]:
        self.validate_state(state)
        washout_state, lead_lag_state = (_number(value, "PSS state") for value in state)
        speed = _number(speed_deviation_pu, "speed_deviation_pu")
        p = self.parameters
        washout_derivative = (speed - washout_state) / p.washout_time_constant_s
        washout_output = p.gain * (speed - washout_state)
        lead_lag_derivative = (washout_output - lead_lag_state) / p.lag_time_constant_s
        return (washout_derivative, lead_lag_derivative)

    def output(self, state: tuple[float, ...] | list[float], *,
               speed_deviation_pu: float, **_: Any) -> float:
        self.validate_state(state)
        washout_state, lead_lag_state = (_number(value, "PSS state") for value in state)
        speed = _number(speed_deviation_pu, "speed_deviation_pu")
        p = self.parameters
        washout_output = p.gain * (speed - washout_state)
        ratio = p.lead_time_constant_s / p.lag_time_constant_s
        raw = ratio * washout_output + (1.0 - ratio) * lead_lag_state
        return _clip(raw, p.output_min_pu, p.output_max_pu)

    def summary(self) -> dict[str, Any]:
        return {"model_type": self.model_type, "state_names": self.state_names,
                "parameters": self.parameters}


@dataclass(frozen=True, slots=True)
class TGOV1Parameters:
    """IEEE TGOV1 steam-governor parameters on the connected machine base.

    T1 is the steam-bowl/governor time constant, T2 the reheater numerator
    time constant, and T3 the reheater lag time constant. All power and
    speed quantities are per-unit on the same declared base.
    """
    droop_pu: float
    t1_s: float
    t2_s: float
    t3_s: float
    valve_min_pu: float = 0.0
    valve_max_pu: float = 1.0
    turbine_damping_pu: float = 0.0

    def __post_init__(self) -> None:
        for name in ("droop_pu", "t1_s", "t3_s"):
            value = _number(getattr(self, name), name)
            if value <= 0.0:
                raise ValueError(f"{name} must be greater than zero")
            object.__setattr__(self, name, value)
        t2 = _number(self.t2_s, "t2_s")
        if t2 < 0.0:
            raise ValueError("t2_s must be non-negative")
        object.__setattr__(self, "t2_s", t2)
        low = _number(self.valve_min_pu, "valve_min_pu")
        high = _number(self.valve_max_pu, "valve_max_pu")
        if low >= high:
            raise ValueError("valve limits must satisfy minimum < maximum")
        object.__setattr__(self, "valve_min_pu", low)
        object.__setattr__(self, "valve_max_pu", high)
        damping = _number(self.turbine_damping_pu, "turbine_damping_pu")
        if damping < 0.0:
            raise ValueError("turbine_damping_pu must be non-negative")
        object.__setattr__(self, "turbine_damping_pu", damping)


class TGOV1SteamGovernor(DynamicPlugin):
    """Two-state IEEE TGOV1 steam governor/reheater block.

    States are valve position Pv and reheater/turbine power Pt. The output
    Pm = Pt - Dt*speed_deviation. The caller supplies the reference and
    speed at every integrator stage; this object owns no simulation clock.
    """
    model_type = "IEEE_TGOV1_STEAM_GOVERNOR"
    state_names: ClassVar[tuple[str, ...]] = (
        "valve_position_pu", "turbine_power_pu",
    )

    def __init__(self, parameters: TGOV1Parameters) -> None:
        if not isinstance(parameters, TGOV1Parameters):
            raise TypeError("parameters must be TGOV1Parameters")
        self.parameters = parameters

    def initial_state(self, *, mechanical_power_pu: float,
                      speed_deviation_pu: float = 0.0,
                      power_reference_pu: float | None = None,
                      **_: Any) -> tuple[float, ...]:
        pm = _number(mechanical_power_pu, "mechanical_power_pu")
        speed = _number(speed_deviation_pu, "speed_deviation_pu")
        valve = pm + self.parameters.turbine_damping_pu * speed
        if not self.parameters.valve_min_pu <= valve <= self.parameters.valve_max_pu:
            raise ValueError("steady-state valve position is outside TGOV1 limits")
        expected_reference = speed + self.parameters.droop_pu * valve
        if power_reference_pu is not None:
            supplied = _number(power_reference_pu, "power_reference_pu")
            if abs(supplied - expected_reference) > 1e-8:
                raise ValueError(
                    "power reference is inconsistent with the requested TGOV1 steady state"
                )
        return (valve, valve)

    def derivatives(self, state: tuple[float, ...] | list[float], *,
                    speed_deviation_pu: float, power_reference_pu: float,
                    **_: Any) -> tuple[float, ...]:
        self.validate_state(state)
        valve, turbine_power = (_number(value, "TGOV1 state") for value in state)
        speed = _number(speed_deviation_pu, "speed_deviation_pu")
        reference = _number(power_reference_pu, "power_reference_pu")
        p = self.parameters

        governor_error = (reference - speed) / p.droop_pu - valve
        d_valve = governor_error / p.t1_s
        if (valve >= p.valve_max_pu and d_valve > 0.0) or (
            valve <= p.valve_min_pu and d_valve < 0.0
        ):
            d_valve = 0.0

        d_turbine = (valve + p.t2_s * d_valve - turbine_power) / p.t3_s
        if not all(isfinite(value) for value in (d_valve, d_turbine)):
            raise ValueError("TGOV1 derivative contains non-finite values")
        return (d_valve, d_turbine)

    def output(self, state: tuple[float, ...] | list[float], *,
               speed_deviation_pu: float, **_: Any) -> float:
        self.validate_state(state)
        speed = _number(speed_deviation_pu, "speed_deviation_pu")
        return _number(state[1], "turbine_power_pu") - self.parameters.turbine_damping_pu * speed

    def summary(self) -> dict[str, Any]:
        return {
            "model_type": self.model_type,
            "state_names": self.state_names,
            "parameters": self.parameters,
            "power_base": "connected_machine_base",
        }


__all__ = [
    "FirstOrderAVRParameters", "FirstOrderAVR", "TGOV1Governor",
    "PSSParameters", "WashoutLeadLagPSS", "TGOV1Parameters", "TGOV1SteamGovernor",
]
