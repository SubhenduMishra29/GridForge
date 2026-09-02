"""Numerical AC power mismatch evaluation."""

from __future__ import annotations

import numpy as np

from core.solver.power_flow.input import PowerFlowBusType, PowerFlowInput
from core.solver.power_flow.runtime_state import PowerFlowRuntimeState


class PowerMismatch:
    """Calculate injections and Newton mismatch from numerical contracts only."""

    def __init__(self, input_data: PowerFlowInput, ybus, runtime_state: PowerFlowRuntimeState):
        if not isinstance(input_data, PowerFlowInput):
            raise TypeError("input_data must be PowerFlowInput.")
        if not isinstance(runtime_state, PowerFlowRuntimeState):
            raise TypeError("runtime_state must be PowerFlowRuntimeState.")
        self.input = input_data
        self.Ybus = ybus
        self.runtime_state = runtime_state
        self.n = input_data.bus_count
        if getattr(ybus, "shape", None) != (self.n, self.n):
            raise ValueError("Ybus dimension does not match PowerFlowInput.")
        if hasattr(ybus, "bus_ids") and tuple(ybus.bus_ids) != input_data.bus_ids:
            raise ValueError("PowerFlowInput bus ordering does not match Ybus bus ordering.")
        runtime_state.validate(self.n)

    def _get_ybus_array(self):
        y = self.Ybus.toarray() if hasattr(self.Ybus, "toarray") else np.asarray(self.Ybus, dtype=complex)
        if y.shape != (self.n, self.n) or not np.all(np.isfinite(y.real)) or not np.all(np.isfinite(y.imag)):
            raise ValueError("Ybus contains invalid numerical data.")
        return y

    def compute_power(self):
        v = self.runtime_state.vm
        theta = self.runtime_state.va
        y = self._get_ybus_array()
        g, b = y.real, y.imag
        p = np.zeros(self.n, dtype=float)
        q = np.zeros(self.n, dtype=float)
        for i in range(self.n):
            for j in range(self.n):
                angle = theta[i] - theta[j]
                vp = v[i] * v[j]
                p[i] += vp * (g[i, j] * np.cos(angle) + b[i, j] * np.sin(angle))
                q[i] += vp * (g[i, j] * np.sin(angle) - b[i, j] * np.cos(angle))
        return p, q

    def compute(self):
        p_calc, q_calc = self.compute_power()
        p = [self.input.p_spec[i] - p_calc[i] for i, t in enumerate(self.runtime_state.effective_bus_types) if t is not PowerFlowBusType.SLACK]
        q = [self.runtime_state.effective_q_spec[i] - q_calc[i] for i, t in enumerate(self.runtime_state.effective_bus_types) if t is PowerFlowBusType.PQ]
        return np.concatenate((np.asarray(p, dtype=float), np.asarray(q, dtype=float)))

    def max_mismatch(self):
        m = self.compute()
        return 0.0 if m.size == 0 else float(np.max(np.abs(m)))

    def summary(self):
        types = self.runtime_state.effective_bus_types
        return {
            "buses": self.n,
            "ybus_shape": self.Ybus.shape,
            "slack_buses": sum(t is PowerFlowBusType.SLACK for t in types),
            "pv_buses": sum(t is PowerFlowBusType.PV for t in types),
            "pq_buses": sum(t is PowerFlowBusType.PQ for t in types),
            "mismatch_size": sum(t is not PowerFlowBusType.SLACK for t in types) + sum(t is PowerFlowBusType.PQ for t in types),
        }

    def __repr__(self):
        return f"PowerMismatch(buses={self.n}, Ybus_shape={self.Ybus.shape})"
