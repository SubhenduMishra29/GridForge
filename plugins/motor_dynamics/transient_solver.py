"""Headless induction-motor electromechanical and lumped-thermal transient solver.

CPU/NumPy is the numerical reference. Optional Numba-CUDA batch execution maps
independent motor trajectories to GPU threads; it never imports Qt or mutates
GridForge Core/Application state. NPU execution is not selected for this
state-recurrent integration kernel: no compatible general-purpose NPU runtime
contract is currently defined for this numerical workload.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite
from typing import Any, Mapping, Sequence

import numpy as np

_STATE_COUNT = 6
_PSI_DS, _PSI_QS, _PSI_DR, _PSI_QR, _OMEGA_M, _TEMP_C = range(_STATE_COUNT)
_STATE_NAMES = (
    "psi_stator_d_wb",
    "psi_stator_q_wb",
    "psi_rotor_d_wb",
    "psi_rotor_q_wb",
    "rotor_speed_rad_s",
    "winding_temperature_c",
)


@dataclass(frozen=True)
class MotorParameters:
    """SI machine parameters for a balanced, squirrel-cage induction motor.

    Inductances are per-phase equivalent values. The model uses a synchronous
    dq reference frame, constant load torque, linear magnetic parameters, and
    one lumped winding thermal state. Saturation, skin effect, unbalance,
    converter switching, and separate stator/rotor thermal nodes are outside
    this model's present fidelity boundary.
    """

    stator_resistance_ohm: float
    rotor_resistance_ohm: float
    stator_leakage_inductance_h: float
    rotor_leakage_inductance_h: float
    magnetizing_inductance_h: float
    pole_pairs: int
    inertia_kg_m2: float
    friction_n_m_s: float = 0.0
    thermal_capacity_j_k: float = 12000.0
    thermal_conductance_w_k: float = 35.0
    ambient_temperature_c: float = 25.0
    resistance_temp_coefficient_per_k: float = 0.00393
    initial_speed_rad_s: float = 0.0
    initial_temperature_c: float = 25.0

    def __post_init__(self) -> None:
        positive = (
            "stator_resistance_ohm", "rotor_resistance_ohm",
            "stator_leakage_inductance_h", "rotor_leakage_inductance_h",
            "magnetizing_inductance_h", "inertia_kg_m2",
            "thermal_capacity_j_k",
        )
        for name in positive:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be numeric")
            if not isfinite(float(value)) or float(value) <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        for name in (
            "friction_n_m_s", "thermal_conductance_w_k",
            "resistance_temp_coefficient_per_k", "ambient_temperature_c",
            "initial_speed_rad_s", "initial_temperature_c",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be numeric")
            if not isfinite(float(value)) or (name in ("friction_n_m_s", "thermal_conductance_w_k") and value < 0):
                raise ValueError(f"{name} must be finite and non-negative" if name in ("friction_n_m_s", "thermal_conductance_w_k") else f"{name} must be finite")
        if isinstance(self.pole_pairs, bool) or not isinstance(self.pole_pairs, int) or self.pole_pairs < 1:
            raise ValueError("pole_pairs must be a positive integer")
        determinant = (
            (self.stator_leakage_inductance_h + self.magnetizing_inductance_h)
            * (self.rotor_leakage_inductance_h + self.magnetizing_inductance_h)
            - self.magnetizing_inductance_h ** 2
        )
        if determinant <= 0.0 or not isfinite(determinant):
            raise ValueError("machine inductance matrix must be positive and nonsingular")


@dataclass(frozen=True)
class MotorSimulationResult:
    """Immutable result metadata around a flat, contiguous state buffer."""

    motor_id: str
    time_s: np.ndarray
    state_data: np.ndarray
    sample_period_s: float
    backend: str
    diagnostics: Mapping[str, Any]

    @property
    def sample_count(self) -> int:
        return int(self.time_s.size)

    @property
    def state_names(self) -> tuple[str, ...]:
        return _STATE_NAMES

    def state(self, name: str) -> np.ndarray:
        """Return a read-only state channel view."""
        try:
            index = _STATE_NAMES.index(name)
        except ValueError as exc:
            raise KeyError(name) from exc
        matrix = self.state_data.reshape(self.sample_count, _STATE_COUNT)
        view = matrix[:, index].view()
        view.setflags(write=False)
        return view

    def publish_to(
        self,
        read_model_store: Any,
        parameters: MotorParameters,
        electrical_frequency_hz: float,
        load_torque_nm: float,
        *,
        study_id: str | None = None,
    ) -> None:
        """Publish a computed snapshot; caller owns StudyCompleted event timing.

        This method never dispatches UI events or mutates Core. The caller
        should emit the canonical StudyCompleted event only after its study
        orchestration commits successfully.
        """
        publish = getattr(read_model_store, "publish", None)
        if not callable(publish):
            raise TypeError("read_model_store must expose publish(...)")
        if (
            isinstance(electrical_frequency_hz, bool)
            or not isinstance(electrical_frequency_hz, (int, float))
            or not isfinite(float(electrical_frequency_hz))
            or electrical_frequency_hz < 0
        ):
            raise ValueError("electrical_frequency_hz must be finite and non-negative")
        publish(
            self.motor_id,
            self.channels(
                parameters,
                2.0 * np.pi * float(electrical_frequency_hz),
                float(load_torque_nm),
            ),
            self.sample_period_s,
            status="completed",
            study_id=study_id,
        )

    def channels(self, parameters: MotorParameters, electrical_rad_s: float,
                 load_torque_nm: float) -> dict[str, np.ndarray]:
        """Derive read-model channels from the integrated state trajectory."""
        matrix = self.state_data.reshape(self.sample_count, _STATE_COUNT)
        ps, qs, pr, qr, speed, temp = (matrix[:, i] for i in range(_STATE_COUNT))
        lm = parameters.magnetizing_inductance_h
        ls = parameters.stator_leakage_inductance_h + lm
        lr = parameters.rotor_leakage_inductance_h + lm
        det = ls * lr - lm * lm
        ids = (lr * ps - lm * pr) / det
        iqs = (lr * qs - lm * qr) / det
        idr = (ls * pr - lm * ps) / det
        iqr = (ls * qr - lm * qs) / det
        torque = 1.5 * parameters.pole_pairs * (ps * iqs - qs * ids)
        sync_mech = electrical_rad_s / parameters.pole_pairs
        slip_hz = (electrical_rad_s - parameters.pole_pairs * speed) / (2.0 * np.pi)
        values = {
            "stator_current_a": np.hypot(ids, iqs),
            "stator_current_d_a": ids,
            "stator_current_q_a": iqs,
            "rotor_current_d_a": idr,
            "rotor_current_q_a": iqr,
            "electromagnetic_torque_nm": torque,
            "rotor_speed_rad_s": speed,
            "rotor_speed_rpm": speed * 60.0 / (2.0 * np.pi),
            "slip_hz": slip_hz,
            "winding_temperature_c": temp,
            "load_torque_nm": np.full(self.sample_count, float(load_torque_nm)),
            "synchronous_speed_rad_s": np.full(self.sample_count, sync_mech),
        }
        for value in values.values():
            value.setflags(write=False)
        return values


def _validate_time(duration_s: float, step_s: float) -> tuple[int, np.ndarray]:
    for name, value in (("duration_s", duration_s), ("step_s", step_s)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be numeric")
        if not isfinite(float(value)) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    intervals = int(ceil(float(duration_s) / float(step_s)))
    count = intervals + 1
    if count < 2:
        raise ValueError("simulation requires at least two samples")
    # Keep a uniform integration grid that ends exactly at duration_s. The
    # effective step is <= the requested maximum step, avoiding hidden overshoot.
    time = np.linspace(0.0, float(duration_s), count, dtype=np.float64)
    time.setflags(write=False)
    return count, time


def _voltage_profile(value: float | Sequence[float] | np.ndarray, count: int, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim == 0:
        arr = np.full(count, float(arr), dtype=np.float64)
    else:
        arr = arr.reshape(-1)
        if arr.size != count:
            raise ValueError(f"{name} profile must contain exactly {count} samples")
        arr = arr.copy()
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} profile must be finite")
    return arr


def _derivative(state: np.ndarray, p: MotorParameters, vds: float, vqs: float,
                omega_e: float, load_torque: float) -> np.ndarray:
    ps, qs, pr, qr, omega_m, temp = state
    lm = p.magnetizing_inductance_h
    ls = p.stator_leakage_inductance_h + lm
    lr = p.rotor_leakage_inductance_h + lm
    det = ls * lr - lm * lm
    ids, iqs = (lr * ps - lm * pr) / det, (lr * qs - lm * qr) / det
    idr, iqr = (ls * pr - lm * ps) / det, (ls * qr - lm * qs) / det
    temp_delta = temp - p.ambient_temperature_c
    rs = p.stator_resistance_ohm * max(0.05, 1.0 + p.resistance_temp_coefficient_per_k * temp_delta)
    rr = p.rotor_resistance_ohm * max(0.05, 1.0 + p.resistance_temp_coefficient_per_k * temp_delta)
    omega_slip = omega_e - p.pole_pairs * omega_m
    torque = 1.5 * p.pole_pairs * (ps * iqs - qs * ids)
    copper_loss = 1.5 * (rs * (ids * ids + iqs * iqs) + rr * (idr * idr + iqr * iqr))
    out = np.empty(_STATE_COUNT, dtype=np.float64)
    out[_PSI_DS] = vds - rs * ids + omega_e * qs
    out[_PSI_QS] = vqs - rs * iqs - omega_e * ps
    out[_PSI_DR] = -rr * idr + omega_slip * qr
    out[_PSI_QR] = -rr * iqr - omega_slip * pr
    out[_OMEGA_M] = (torque - load_torque - p.friction_n_m_s * omega_m) / p.inertia_kg_m2
    out[_TEMP_C] = (copper_loss - p.thermal_conductance_w_k * temp_delta) / p.thermal_capacity_j_k
    return out


def solve_transient_cpu(
    motor_id: str,
    parameters: MotorParameters,
    duration_s: float,
    step_s: float,
    *,
    stator_voltage_d_v: float | Sequence[float] | np.ndarray,
    stator_voltage_q_v: float | Sequence[float] | np.ndarray = 0.0,
    electrical_frequency_hz: float = 50.0,
    load_torque_nm: float = 0.0,
) -> MotorSimulationResult:
    """Integrate the coupled dq electrical, rotor mechanical, and thermal ODEs.

    Uses fixed-step classical RK4. The voltage profiles are dq components in
    the synchronous reference frame; supply frequency is electrical Hz.
    """
    if not isinstance(motor_id, str) or not motor_id.strip():
        raise ValueError("motor_id must be a non-empty string")
    if not isinstance(parameters, MotorParameters):
        raise TypeError("parameters must be MotorParameters")
    for name, value in (("electrical_frequency_hz", electrical_frequency_hz), ("load_torque_nm", load_torque_nm)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
            raise ValueError(f"{name} must be finite and numeric")
    if electrical_frequency_hz < 0:
        raise ValueError("electrical_frequency_hz must be non-negative")
    count, times = _validate_time(duration_s, step_s)
    vd = _voltage_profile(stator_voltage_d_v, count, "stator_voltage_d_v")
    vq = _voltage_profile(stator_voltage_q_v, count, "stator_voltage_q_v")
    h = float(times[1] - times[0])
    omega_e = 2.0 * np.pi * float(electrical_frequency_hz)
    states = np.zeros((count, _STATE_COUNT), dtype=np.float64)
    states[0, _OMEGA_M] = parameters.initial_speed_rad_s
    states[0, _TEMP_C] = parameters.initial_temperature_c

    for i in range(count - 1):
        y = states[i]
        # Use the interval's left-end input for all RK stages. For a sampled
        # waveform, this is zero-order hold and avoids inventing interpolation.
        args = (parameters, float(vd[i]), float(vq[i]), omega_e, float(load_torque_nm))
        k1 = _derivative(y, *args)
        k2 = _derivative(y + 0.5 * h * k1, *args)
        k3 = _derivative(y + 0.5 * h * k2, *args)
        k4 = _derivative(y + h * k3, *args)
        states[i + 1] = y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        if not np.isfinite(states[i + 1]).all():
            raise FloatingPointError(
                f"motor transient diverged at sample {i + 1}; reduce step_s or check machine parameters"
            )
    flat = np.ascontiguousarray(states.reshape(-1))
    flat.setflags(write=False)
    return MotorSimulationResult(
        motor_id=motor_id.strip(), time_s=times, state_data=flat,
        sample_period_s=h, backend="cpu-rk4",
        diagnostics={
            "integrator": "classical_rk4",
            "state_layout": "flat_motor_major_step_major_state_minor",
            "state_count": _STATE_COUNT,
            "model": "induction_motor_dq_electromechanical_lumped_thermal",
            "electrical_frequency_hz": float(electrical_frequency_hz),
            "load_torque_nm": float(load_torque_nm),
            "voltage_profile": "zero_order_hold",
            "requested_max_step_s": float(step_s),
            "effective_step_s": h,
        },
    )


def cuda_available() -> bool:
    """Return whether Numba can initialize a CUDA device; never require it."""
    try:
        from numba import cuda
        return bool(cuda.is_available())
    except Exception:
        return False


def solve_transient_batch(
    motor_ids: Sequence[str],
    parameter_sets: Sequence[MotorParameters],
    duration_s: float,
    step_s: float,
    *,
    stator_voltage_d_v: Sequence[float],
    stator_voltage_q_v: Sequence[float],
    electrical_frequency_hz: float,
    load_torque_nm: Sequence[float],
    backend: str = "auto",
) -> tuple[MotorSimulationResult, ...]:
    """Solve independent motors, using an optional CUDA kernel for a batch.

    The GPU path is selected only for constant dq voltage profiles and only
    when CUDA is usable. The CPU path is the fallback and reference. A requested
    unavailable 'cuda' backend falls back to CPU and records that decision.
    """
    n = len(motor_ids)
    if n == 0 or len(parameter_sets) != n or len(load_torque_nm) != n:
        raise ValueError("motor_ids, parameter_sets and load_torque_nm must have the same non-zero length")
    if any(not isinstance(mid, str) or not mid.strip() for mid in motor_ids):
        raise ValueError("every motor_id must be a non-empty string")
    if any(not isinstance(p, MotorParameters) for p in parameter_sets):
        raise TypeError("every parameter_sets entry must be MotorParameters")
    if backend not in ("auto", "cpu", "cuda"):
        raise ValueError("backend must be 'auto', 'cpu', or 'cuda'")
    vd, vq = np.asarray(stator_voltage_d_v, dtype=np.float64), np.asarray(stator_voltage_q_v, dtype=np.float64)
    if vd.ndim != 0 or vq.ndim != 0:
        raise ValueError("batched accelerator API currently requires constant dq voltage inputs")
    selected = backend
    if selected == "auto":
        selected = "cuda" if n >= 8 and cuda_available() else "cpu"
    if selected == "cuda" and cuda_available():
        try:
            return _solve_batch_cuda(
                motor_ids, parameter_sets, duration_s, step_s, float(vd), float(vq),
                electrical_frequency_hz, load_torque_nm,
            )
        except Exception:
            # Optional acceleration must never prevent a valid CPU computation.
            return tuple(
                _with_backend_note(solve_transient_cpu(
                    mid, p, duration_s, step_s, stator_voltage_d_v=float(vd),
                    stator_voltage_q_v=float(vq), electrical_frequency_hz=electrical_frequency_hz,
                    load_torque_nm=float(torque),
                ), "cuda_failed_cpu_fallback")
                for mid, p, torque in zip(motor_ids, parameter_sets, load_torque_nm)
            )
    fallback = backend == "cuda"
    results = tuple(
        solve_transient_cpu(
            mid, p, duration_s, step_s, stator_voltage_d_v=float(vd),
            stator_voltage_q_v=float(vq), electrical_frequency_hz=electrical_frequency_hz,
            load_torque_nm=float(torque),
        ) for mid, p, torque in zip(motor_ids, parameter_sets, load_torque_nm)
    )
    if fallback:
        return tuple(_with_backend_note(r, "cuda_unavailable_cpu_fallback") for r in results)
    return results


def _with_backend_note(result: MotorSimulationResult, note: str) -> MotorSimulationResult:
    diagnostics = dict(result.diagnostics)
    diagnostics["requested_backend_note"] = note
    return MotorSimulationResult(
        result.motor_id, result.time_s, result.state_data, result.sample_period_s,
        result.backend, diagnostics,
    )


def _solve_batch_cuda(
    motor_ids: Sequence[str], parameter_sets: Sequence[MotorParameters],
    duration_s: float, step_s: float, vds: float, vqs: float,
    electrical_frequency_hz: float, load_torques: Sequence[float],
) -> tuple[MotorSimulationResult, ...]:
    """Optional Numba CUDA implementation; one CUDA thread integrates one motor."""
    from numba import cuda

    count, times = _validate_time(duration_s, step_s)
    if isinstance(electrical_frequency_hz, bool) or not isinstance(electrical_frequency_hz, (int, float)) or not isfinite(float(electrical_frequency_hz)) or electrical_frequency_hz < 0:
        raise ValueError("electrical_frequency_hz must be finite, numeric and non-negative")
    omega_e = 2.0 * np.pi * float(electrical_frequency_hz)
    n = len(motor_ids)
    # Packed numeric contract: Rs,Rr,Lls,Llr,Lm,p,J,B,Cth,Gth,Tamb,alpha,
    # initial speed, initial temperature, load torque.
    packed = np.asarray([[
        p.stator_resistance_ohm, p.rotor_resistance_ohm,
        p.stator_leakage_inductance_h, p.rotor_leakage_inductance_h,
        p.magnetizing_inductance_h, p.pole_pairs, p.inertia_kg_m2,
        p.friction_n_m_s, p.thermal_capacity_j_k, p.thermal_conductance_w_k,
        p.ambient_temperature_c, p.resistance_temp_coefficient_per_k,
        p.initial_speed_rad_s, p.initial_temperature_c, float(t),
    ] for p, t in zip(parameter_sets, load_torques)], dtype=np.float64)
    output = np.zeros((n * count * _STATE_COUNT,), dtype=np.float64)
    dt = float(times[1] - times[0])

    @cuda.jit(device=True)
    def deriv(y, p, vd0, vq0, we, out):
        ps, qs, pr, qr, wm, temp = y[0], y[1], y[2], y[3], y[4], y[5]
        lm = p[4]
        ls, lr = p[2] + lm, p[3] + lm
        det = ls * lr - lm * lm
        ids, iqs = (lr * ps - lm * pr) / det, (lr * qs - lm * qr) / det
        idr, iqr = (ls * pr - lm * ps) / det, (ls * qr - lm * qs) / det
        td = temp - p[10]
        rs = p[0] * max(0.05, 1.0 + p[11] * td)
        rr = p[1] * max(0.05, 1.0 + p[11] * td)
        slip = we - p[5] * wm
        torque = 1.5 * p[5] * (ps * iqs - qs * ids)
        loss = 1.5 * (rs * (ids * ids + iqs * iqs) + rr * (idr * idr + iqr * iqr))
        out[0] = vd0 - rs * ids + we * qs
        out[1] = vq0 - rs * iqs - we * ps
        out[2] = -rr * idr + slip * qr
        out[3] = -rr * iqr - slip * pr
        out[4] = (torque - p[14] - p[7] * wm) / p[6]
        out[5] = (loss - p[9] * td) / p[8]

    @cuda.jit
    def integrate(params, result, motor_count, steps, h, vd0, vq0, we):
        m = cuda.grid(1)
        if m >= motor_count:
            return
        p = params[m]
        y = cuda.local.array(_STATE_COUNT, dtype=np.float64)
        a = cuda.local.array(_STATE_COUNT, dtype=float64)
        b = cuda.local.array(_STATE_COUNT, dtype=float64)
        c = cuda.local.array(_STATE_COUNT, dtype=float64)
        d = cuda.local.array(_STATE_COUNT, dtype=float64)
        tmp = cuda.local.array(_STATE_COUNT, dtype=float64)
        for j in range(_STATE_COUNT):
            y[j] = 0.0
        y[4], y[5] = p[12], p[13]
        base = m * steps * _STATE_COUNT
        for j in range(_STATE_COUNT):
            result[base + j] = y[j]
        for step in range(steps - 1):
            deriv(y, p, vd0, vq0, we, a)
            for j in range(_STATE_COUNT): tmp[j] = y[j] + 0.5 * h * a[j]
            deriv(tmp, p, vd0, vq0, we, b)
            for j in range(_STATE_COUNT): tmp[j] = y[j] + 0.5 * h * b[j]
            deriv(tmp, p, vd0, vq0, we, c)
            for j in range(_STATE_COUNT): tmp[j] = y[j] + h * c[j]
            deriv(tmp, p, vd0, vq0, we, d)
            for j in range(_STATE_COUNT):
                y[j] = y[j] + (h / 6.0) * (a[j] + 2.0*b[j] + 2.0*c[j] + d[j])
                result[base + (step + 1) * _STATE_COUNT + j] = y[j]

    d_params = cuda.to_device(packed)
    d_output = cuda.to_device(output)
    integrate[(n + 31) // 32, 32](
        d_params, d_output, n, count, dt, float(vds), float(vqs), omega_e
    )
    cuda.synchronize()
    states = d_output.copy_to_host().reshape(n, count, _STATE_COUNT)
    if not np.isfinite(states).all():
        raise FloatingPointError("CUDA motor transient produced non-finite states")
    results = []
    for i, (mid, p, torque) in enumerate(zip(motor_ids, parameter_sets, load_torques)):
        flat = np.ascontiguousarray(states[i].reshape(-1))
        flat.setflags(write=False)
        results.append(MotorSimulationResult(
            str(mid).strip(), times, flat, float(step_s), "cuda-numba-rk4",
            {"integrator": "classical_rk4", "state_layout": "flat_motor_major_step_major_state_minor",
             "state_count": _STATE_COUNT, "model": "induction_motor_dq_electromechanical_lumped_thermal",
             "electrical_frequency_hz": float(electrical_frequency_hz), "load_torque_nm": float(torque),
             "voltage_profile": "constant_dq", "precision": "float64",
             "requested_max_step_s": float(step_s), "effective_step_s": dt},
        ))
    return tuple(results)


__all__ = [
    "MotorParameters", "MotorSimulationResult", "solve_transient_cpu",
    "solve_transient_batch", "cuda_available",
]
