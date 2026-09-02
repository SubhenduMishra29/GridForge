"""Solver-local mutable runtime state for AC power flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .input import PowerFlowBusType, PowerFlowInput


@dataclass(slots=True)
class PowerFlowRuntimeState:
    """Mutable numerical state owned exclusively by one solver execution."""

    vm: np.ndarray
    va: np.ndarray
    effective_bus_types: list[PowerFlowBusType]
    effective_q_spec: np.ndarray
    iteration: int = 0
    mismatch: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=float))
    residual: float = np.inf
    converged: bool = False
    message: str = ""
    q_limit_transitions: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_input(cls, input_data: PowerFlowInput):
        return cls(np.asarray(input_data.initial_vm, dtype=float).copy(), np.asarray(input_data.initial_va, dtype=float).copy(), list(input_data.bus_types), np.asarray(input_data.q_spec, dtype=float).copy())

    def validate(self, expected_size: int) -> None:
        if self.vm.shape != (expected_size,) or self.va.shape != (expected_size,) or self.effective_q_spec.shape != (expected_size,) or len(self.effective_bus_types) != expected_size:
            raise ValueError("Runtime state dimension does not match PowerFlowInput.")
        if not np.all(np.isfinite(self.vm)) or np.any(self.vm <= 0.0) or not np.all(np.isfinite(self.va)) or not np.all(np.isfinite(self.effective_q_spec)):
            raise ValueError("Runtime state contains invalid numerical values.")

    def set_iteration(self, iteration: int) -> None:
        self.iteration = int(iteration)

    def set_mismatch(self, mismatch: np.ndarray) -> float:
        self.mismatch = np.asarray(mismatch, dtype=float).reshape(-1).copy()
        self.residual = 0.0 if self.mismatch.size == 0 else float(np.max(np.abs(self.mismatch)))
        return self.residual

    def apply_correction(self, angle_indices, voltage_indices, dx, damping: float) -> None:
        dx = np.asarray(dx, dtype=float).reshape(-1)
        expected = len(angle_indices) + len(voltage_indices)
        if dx.size != expected:
            raise ValueError(f"Newton correction dimension must be {expected}; received {dx.size}.")
        damping = float(damping)
        if not np.isfinite(damping) or damping <= 0.0:
            raise ValueError("damping must be finite and positive.")
        split = len(angle_indices)
        self.va[np.asarray(angle_indices, dtype=int)] += damping * dx[:split]
        self.vm[np.asarray(voltage_indices, dtype=int)] += damping * dx[split:]
        if np.any(self.vm <= 0.0) or not np.all(np.isfinite(self.vm)) or not np.all(np.isfinite(self.va)):
            raise ValueError("Newton correction produced an invalid voltage state.")

    def convert_pv_to_pq(self, index: int, q_limit: float, limit_type: str, *, q_calculated=None, bus_id=None):
        if self.effective_bus_types[index] is not PowerFlowBusType.PV:
            raise ValueError("Only a PV runtime state can be converted to PQ.")
        if limit_type not in ("Qmin", "Qmax"):
            raise ValueError("limit_type must be 'Qmin' or 'Qmax'.")
        record = {"bus_index": int(index), "bus_id": bus_id if bus_id is not None else index, "q_calculated": None if q_calculated is None else float(q_calculated), "q_limit": float(q_limit), "limit": limit_type, "from_type": "PV", "to_type": "PQ"}
        self.effective_bus_types[index] = PowerFlowBusType.PQ
        self.effective_q_spec[index] = float(q_limit)
        self.q_limit_transitions.append(record)
        return record


__all__ = ["PowerFlowRuntimeState"]
