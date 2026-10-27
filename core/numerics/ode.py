"""Backend-neutral ordinary differential equation integration primitives.

This module is a headless numerical utility: it has no GridForge domain,
plugin, Qt, GPU, or accelerator-runtime dependencies. Domain plugins supply
their own derivative function and state vector. CPU RK4 is the deterministic
reference implementation; accelerator-specific implementations must preserve
the same input, state-layout, and failure contracts.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import ceil, isfinite
from typing import Any

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]
Derivative = Callable[[FloatArray, Any], npt.ArrayLike]


def _is_numeric_scalar(value: Any) -> bool:
    """Accept Python/NumPy real scalars but reject booleans and arrays."""
    return isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(
        value, (bool, np.bool_)
    )


@dataclass(frozen=True)
class ODESolution:
    """Immutable time grid and contiguous step-major state history."""

    time_s: FloatArray
    state_data: FloatArray
    state_count: int
    sample_period_s: float
    integrator: str = "classical_rk4"

    @property
    def sample_count(self) -> int:
        return int(self.time_s.size)

    def states(self) -> FloatArray:
        """Return a read-only (sample, state) view of the flat state buffer."""
        view = self.state_data.reshape(self.sample_count, self.state_count).view()
        view.setflags(write=False)
        return view


def uniform_time_grid(duration_s: float, maximum_step_s: float) -> tuple[FloatArray, float]:
    """Build a grid ending exactly at duration, without exceeding maximum step."""
    for name, value in (("duration_s", duration_s), ("maximum_step_s", maximum_step_s)):
        if not _is_numeric_scalar(value):
            raise TypeError(f"{name} must be numeric")
        if not isfinite(float(value)) or float(value) <= 0.0:
            raise ValueError(f"{name} must be finite and positive")
    intervals = int(ceil(float(duration_s) / float(maximum_step_s)))
    if intervals < 1:
        raise ValueError("integration requires at least one interval")
    times = np.linspace(0.0, float(duration_s), intervals + 1, dtype=np.float64)
    times.setflags(write=False)
    return times, float(times[1] - times[0])


def solve_rk4(
    derivative: Derivative,
    initial_state: npt.ArrayLike,
    duration_s: float,
    maximum_step_s: float,
    *,
    input_at: Callable[[int, float], Any] | None = None,
) -> ODESolution:
    """Integrate a state vector with classical fixed-step RK4.

    derivative(state, input) receives a read-only stage state and interval input.
    input_at is evaluated once per interval, so sampled inputs use an explicit
    zero-order-hold contract. Derivatives must return the initial state's shape.
    """
    if not callable(derivative):
        raise TypeError("derivative must be callable")
    initial = np.asarray(initial_state, dtype=np.float64)
    if initial.ndim != 1 or initial.size == 0:
        raise ValueError("initial_state must be a non-empty one-dimensional vector")
    if not np.isfinite(initial).all():
        raise ValueError("initial_state must contain only finite values")
    times, h = uniform_time_grid(duration_s, maximum_step_s)
    states = np.empty((times.size, initial.size), dtype=np.float64)
    states[0] = initial

    def evaluate(y: FloatArray, u: Any, index: int) -> FloatArray:
        stage = y.view()
        stage.setflags(write=False)
        raw = np.asarray(derivative(stage, u), dtype=np.float64)
        if raw.shape != initial.shape:
            raise ValueError(
                f"derivative at interval {index} returned shape {raw.shape}; "
                f"expected {initial.shape}"
            )
        if not np.isfinite(raw).all():
            raise FloatingPointError(f"derivative produced non-finite values at interval {index}")
        return raw

    for index in range(times.size - 1):
        u = input_at(index, float(times[index])) if input_at is not None else None
        y = states[index]
        k1 = evaluate(y, u, index)
        k2 = evaluate(y + 0.5 * h * k1, u, index)
        k3 = evaluate(y + 0.5 * h * k2, u, index)
        k4 = evaluate(y + h * k3, u, index)
        next_state = y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        if not np.isfinite(next_state).all():
            raise FloatingPointError(f"ODE integration diverged at sample {index + 1}")
        states[index + 1] = next_state

    flat = np.ascontiguousarray(states.reshape(-1))
    flat.setflags(write=False)
    return ODESolution(times, flat, int(initial.size), h)
