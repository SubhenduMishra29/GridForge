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


@dataclass(frozen=True, slots=True)
class RLPhaseTransient:
    phase: str
    time_constant_s: float
    steady_state_rms_current_a: float
    power_factor_angle_rad: float
    samples: tuple[RLTransientSample, ...]


@dataclass(frozen=True, slots=True)
class RLTransientFaultResult:
    event_id: str
    model_id: str
    phases: Mapping[str, RLPhaseTransient]
    observation_start_s: float
    observation_end_s: float
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must be non-empty.")
        phases = dict(self.phases)
        if not phases or any(key != value.phase for key, value in phases.items()):
            raise ValueError("Phase result keys must match non-empty phase results.")
        object.__setattr__(self, "phases", MappingProxyType(phases))


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
