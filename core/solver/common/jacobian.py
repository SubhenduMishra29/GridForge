"""Analytical Newton-Raphson Jacobian from numerical contracts only."""

from __future__ import annotations

import numpy as np

from core.solver.common.mismatch import PowerMismatch
from core.solver.power_flow.input import PowerFlowBusType, PowerFlowInput
from core.solver.power_flow.runtime_state import PowerFlowRuntimeState


class JacobianBuilder:
    """Build the AC Newton-Raphson Jacobian without live Core objects."""

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

    def state_indices(self):
        types = self.runtime_state.effective_bus_types
        angle_indices = [i for i, t in enumerate(types) if t is not PowerFlowBusType.SLACK]
        voltage_indices = [i for i, t in enumerate(types) if t is PowerFlowBusType.PQ]
        return angle_indices, voltage_indices

    def build(self):
        y = self._get_ybus_array()
        g, b = y.real, y.imag
        v = self.runtime_state.vm
        theta = self.runtime_state.va
        p, q = PowerMismatch(self.input, self.Ybus, self.runtime_state).compute_power()
        angle_indices, voltage_indices = self.state_indices()
        m, k = len(angle_indices), len(voltage_indices)
        if m + k == 0:
            return np.empty((0, 0), dtype=float)
        j1 = np.empty((m, m), dtype=float)
        j2 = np.empty((m, k), dtype=float)
        j3 = np.empty((k, m), dtype=float)
        j4 = np.empty((k, k), dtype=float)
        for r, i in enumerate(angle_indices):
            for c, j in enumerate(angle_indices):
                if i == j:
                    j1[r, c] = -q[i] - b[i, i] * v[i] ** 2
                else:
                    a = theta[i] - theta[j]
                    j1[r, c] = v[i] * v[j] * (g[i, j] * np.sin(a) - b[i, j] * np.cos(a))
            for c, j in enumerate(voltage_indices):
                if i == j:
                    j2[r, c] = p[i] / v[i] + g[i, i] * v[i]
                else:
                    a = theta[i] - theta[j]
                    j2[r, c] = v[i] * (g[i, j] * np.cos(a) + b[i, j] * np.sin(a))
        for r, i in enumerate(voltage_indices):
            for c, j in enumerate(angle_indices):
                if i == j:
                    j3[r, c] = p[i] - g[i, i] * v[i] ** 2
                else:
                    a = theta[i] - theta[j]
                    j3[r, c] = -v[i] * v[j] * (g[i, j] * np.cos(a) + b[i, j] * np.sin(a))
            for c, j in enumerate(voltage_indices):
                if i == j:
                    j4[r, c] = q[i] / v[i] - b[i, i] * v[i]
                else:
                    a = theta[i] - theta[j]
                    j4[r, c] = v[i] * (g[i, j] * np.sin(a) - b[i, j] * np.cos(a))
        return np.block([[j1, j2], [j3, j4]])

    def summary(self):
        angles, voltages = self.state_indices()
        return {"buses": self.n, "angle_states": len(angles), "voltage_states": len(voltages), "state_size": len(angles) + len(voltages), "ybus_shape": self.Ybus.shape}

    def __repr__(self):
        return f"JacobianBuilder(buses={self.n}, Ybus_shape={self.Ybus.shape})"
