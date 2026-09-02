"""Reactive-power limit transitions for numerical power-flow execution."""

from __future__ import annotations

from core.solver.common.mismatch import PowerMismatch
from core.solver.power_flow.input import PowerFlowBusType, PowerFlowInput
from core.solver.power_flow.runtime_state import PowerFlowRuntimeState


class QLimitHandler:
    """Detect PV reactive-limit violations and update RuntimeState only."""

    def __init__(self, input_data: PowerFlowInput, runtime_state: PowerFlowRuntimeState, tolerance: float = 1e-8, ybus=None):
        if not isinstance(input_data, PowerFlowInput):
            raise TypeError("input_data must be PowerFlowInput.")
        if not isinstance(runtime_state, PowerFlowRuntimeState):
            raise TypeError("runtime_state must be PowerFlowRuntimeState.")
        self.input = input_data
        self.runtime_state = runtime_state
        self.tolerance = float(tolerance)
        self.ybus = ybus
        self.history: list[dict] = []
        self._validate()

    def _validate(self):
        if self.tolerance < 0.0:
            raise ValueError("tolerance must be non-negative.")
        self.runtime_state.validate(self.input.bus_count)
        if self.ybus is not None and getattr(self.ybus, "shape", None) != (self.input.bus_count, self.input.bus_count):
            raise ValueError("Ybus dimension does not match PowerFlowInput.")

    def reset_history(self):
        self.history = []

    def check_limits(self, q_calculated=None):
        """Return deterministic PV→PQ transitions and mutate only runtime state."""
        if q_calculated is None:
            if self.ybus is None:
                raise ValueError("Ybus is required when q_calculated is not supplied.")
            _, q_calculated = PowerMismatch(self.input, self.ybus, self.runtime_state).compute_power()
        changed = []
        for i, bus_type in enumerate(self.runtime_state.effective_bus_types):
            if bus_type is not PowerFlowBusType.PV:
                continue
            q = float(q_calculated[i])
            q_min = self.input.q_min[i]
            q_max = self.input.q_max[i]
            if q_min is not None and q < q_min - self.tolerance:
                changed.append(self.runtime_state.convert_pv_to_pq(i, q_min, "Qmin", q_calculated=q, bus_id=self.input.bus_ids[i]))
            elif q_max is not None and q > q_max + self.tolerance:
                changed.append(self.runtime_state.convert_pv_to_pq(i, q_max, "Qmax", q_calculated=q, bus_id=self.input.bus_ids[i]))
        self.history.extend(changed)
        return changed

    def summary(self):
        return {"buses": self.input.bus_count, "tolerance": self.tolerance, "conversions": len(self.history)}

    def __repr__(self):
        return f"QLimitHandler(buses={self.input.bus_count}, tolerance={self.tolerance})"
