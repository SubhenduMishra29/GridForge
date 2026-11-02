"""Analytical single-phase RL fault-current transient model.

This is a deliberately bounded source-plus-series-RL equivalent. It models
fault-inception DC offset and sinusoidal steady-state current for each
independently supplied phase. It is not a network-wide EMT solver: mutual
coupling, rotating-machine subtransient decay, inverter controls, CT dynamics,
arc impedance variation, and breaker pole mechanics are outside this model.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric, not boolean.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


@dataclass(frozen=True, slots=True)
class RLPhaseEquivalent:
    """Per-phase Thevenin RMS voltage and series R-L equivalent."""

    phase: str
    voltage_rms_v: float
    frequency_hz: float
    resistance_ohm: float
    inductance_h: float
    inception_angle_rad: float
    initial_current_a: float = 0.0

    def __post_init__(self) -> None:
        phase = str(self.phase).strip().upper()
        if phase not in {"A", "B", "C", "N"}:
            raise ValueError("phase must be A, B, C, or N.")
        object.__setattr__(self, "phase", phase)
        for name in ("voltage_rms_v", "frequency_hz", "resistance_ohm",
                     "inductance_h", "inception_angle_rad", "initial_current_a"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if self.voltage_rms_v <= 0 or self.frequency_hz <= 0:
            raise ValueError("Voltage and frequency must be positive.")
        if self.resistance_ohm <= 0 or self.inductance_h <= 0:
            raise ValueError("The bounded RL model requires positive R and L.")
        if len(self.phase) != 1:
            raise ValueError("Invalid phase identifier.")


@dataclass(frozen=True, slots=True)
class RLTransientSample:
    time_s: float
    instantaneous_current_a: float

    def __post_init__(self) -> None:
        time_value = _finite(self.time_s, "time_s")
        current = _finite(self.instantaneous_current_a, "instantaneous_current_a")
        if time_value < 0.0:
            raise ValueError("time_s cannot be negative.")
        object.__setattr__(self, "time_s", time_value)
        object.__setattr__(self, "instantaneous_current_a", current)


@dataclass(frozen=True, slots=True)
class RLPhaseTransient:
    phase: str
    time_constant_s: float
    steady_state_rms_current_a: float
    power_factor_angle_rad: float
    samples: tuple[RLTransientSample, ...]

    def __post_init__(self) -> None:
        phase = str(self.phase).strip().upper()
        if phase not in {"A", "B", "C", "N"}:
            raise ValueError("phase must be A, B, C, or N.")
        for name in ("time_constant_s", "steady_state_rms_current_a"):
            value = _finite(getattr(self, name), name)
            if value <= 0.0:
                raise ValueError(f"{name} must be positive.")
            object.__setattr__(self, name, value)
        angle = _finite(self.power_factor_angle_rad, "power_factor_angle_rad")
        samples = tuple(self.samples)
        if len(samples) < 2 or any(not isinstance(item, RLTransientSample) for item in samples):
            raise ValueError("A phase transient requires at least two typed samples.")
        if samples[0].time_s != 0.0 or any(
            right.time_s <= left.time_s for left, right in zip(samples, samples[1:])
        ):
            raise ValueError("Phase transient samples must start at zero and increase strictly.")
        object.__setattr__(self, "phase", phase)
        object.__setattr__(self, "power_factor_angle_rad", angle)
        object.__setattr__(self, "samples", samples)


@dataclass(frozen=True, slots=True)
class RLTransientFaultResult:
    event_id: str
    model_id: str
    phases: Mapping[str, RLPhaseTransient]
    observation_start_s: float
    observation_end_s: float
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be non-empty.")
        if self.model_id != "INDEPENDENT_PHASE_THEVENIN_SERIES_RL_V1":
            raise ValueError("Unsupported RL transient model_id.")
        start = _finite(self.observation_start_s, "observation_start_s")
        end = _finite(self.observation_end_s, "observation_end_s")
        if start < 0.0 or end <= start:
            raise ValueError("Observation window must be finite, non-negative and increasing.")
        phases = dict(self.phases)
        if not phases or any(
            not isinstance(value, RLPhaseTransient) or key != value.phase
            for key, value in phases.items()
        ):
            raise ValueError("Phase result keys must match typed non-empty phase results.")
        for phase in phases.values():
            if phase.samples[0].time_s != start or phase.samples[-1].time_s != end:
                raise ValueError("Every phase result must cover the declared observation window.")
        limitations = tuple(str(item).strip() for item in self.limitations)
        if not limitations or any(not item for item in limitations):
            raise ValueError("Model limitations must be explicitly listed.")
        object.__setattr__(self, "event_id", self.event_id.strip())
        object.__setattr__(self, "observation_start_s", start)
        object.__setattr__(self, "observation_end_s", end)
        object.__setattr__(self, "phases", MappingProxyType(phases))
        object.__setattr__(self, "limitations", limitations)


def solve_rl_fault_transient(
    *,
    event_id: str,
    equivalents: tuple[RLPhaseEquivalent, ...],
    sample_times_s: tuple[float, ...],
) -> RLTransientFaultResult:
    """Solve exact post-inception current for explicit independent phase RL equivalents.

    Source voltage is v(t)=sqrt(2)*V_rms*sin(omega*t+inception_angle).
    The initial current is the supplied pre-inception instantaneous current.
    Samples are instantaneous signed amperes, not RMS relay measurements.
    """
    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError("event_id must be a non-empty string.")
    phases = tuple(equivalents)
    if not phases or any(not isinstance(item, RLPhaseEquivalent) for item in phases):
        raise TypeError("equivalents must contain RLPhaseEquivalent values.")
    if len({item.phase for item in phases}) != len(phases):
        raise ValueError("Each phase equivalent must be unique.")
    times = tuple(_finite(item, "sample time") for item in sample_times_s)
    if len(times) < 2 or times[0] != 0.0:
        raise ValueError("At least two sample times are required and the first must be 0.")
    if any(t < 0.0 for t in times) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("Sample times must be non-negative and strictly increasing.")

    results: dict[str, RLPhaseTransient] = {}
    for item in phases:
        omega = 2.0 * math.pi * item.frequency_hz
        tau = item.inductance_h / item.resistance_ohm
        impedance = math.hypot(item.resistance_ohm, omega * item.inductance_h)
        angle = math.atan2(omega * item.inductance_h, item.resistance_ohm)
        peak_current = math.sqrt(2.0) * item.voltage_rms_v / impedance
        offset_at_inception = math.sin(item.inception_angle_rad - angle)
        samples = tuple(
            RLTransientSample(
                time_s=t,
                instantaneous_current_a=(
                    peak_current * (
                        math.sin(omega * t + item.inception_angle_rad - angle)
                        - offset_at_inception * math.exp(-t / tau)
                    )
                    + item.initial_current_a * math.exp(-t / tau)
                ),
            )
            for t in times
        )
        results[item.phase] = RLPhaseTransient(
            phase=item.phase,
            time_constant_s=tau,
            steady_state_rms_current_a=item.voltage_rms_v / impedance,
            power_factor_angle_rad=angle,
            samples=samples,
        )
    return RLTransientFaultResult(
        event_id=event_id.strip(),
        model_id="INDEPENDENT_PHASE_THEVENIN_SERIES_RL_V1",
        phases=results,
        observation_start_s=times[0],
        observation_end_s=times[-1],
        limitations=(
            "Independent phase equivalents; no inter-phase or mutual coupling.",
            "No generator subtransient/transient decrement or inverter control response.",
            "No CT saturation, burden, remanence, or secondary circuit model.",
            "No arc nonlinearity, topology switching, or breaker pole sequence.",
            "Samples are instantaneous signed primary currents, not relay RMS samples.",
        ),
    )


__all__ = [
    "RLPhaseEquivalent", "RLTransientSample", "RLPhaseTransient",
    "RLTransientFaultResult", "solve_rl_fault_transient",
]
