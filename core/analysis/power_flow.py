"""Analysis-level orchestration for prepared numerical power-flow studies."""

from __future__ import annotations

from typing import Optional

from core.solver.power_flow.input import PowerFlowInput
from core.solver.power_flow.nr_solver import NewtonRaphsonSolver
from core.solver.power_flow.result import PowerFlowResult


class PowerFlowAnalysis:
    """Coordinate a power-flow execution without exposing live Core objects to it.

    The caller prepares the immutable numerical snapshot and derived YBus at
    the Core/Application boundary. Numerical execution receives only those
    prepared contracts.
    """

    def __init__(self, input_data: PowerFlowInput, ybus, options: Optional[object] = None) -> None:
        if not isinstance(input_data, PowerFlowInput):
            raise TypeError("input_data must be PowerFlowInput.")
        if ybus is None:
            raise ValueError("Power Flow requires a prepared YBus.")
        if getattr(ybus, "shape", None) != (input_data.bus_count, input_data.bus_count):
            raise ValueError("Prepared YBus dimension does not match PowerFlowInput.")
        if not hasattr(ybus, "bus_ids") or tuple(ybus.bus_ids) != input_data.bus_ids:
            raise ValueError("Prepared YBus ordering does not match PowerFlowInput.")
        if options is None:
            from core.solver.power_flow.solver_options import SolverOptions
            options = SolverOptions()
        self.input = input_data
        self.Ybus = ybus
        self.options = options
        self.solver = NewtonRaphsonSolver(input_data, ybus, options)
        self._result: PowerFlowResult | None = None

    def solve(self) -> PowerFlowResult:
        """Execute the numerical study and retain the result at analysis scope."""
        self._result = self.solver.solve()
        return self._result

    @property
    def result(self) -> PowerFlowResult | None:
        """Return the latest result without consulting Core state."""
        return self._result


__all__ = ["PowerFlowAnalysis"]
