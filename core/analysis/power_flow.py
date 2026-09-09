"""
GridForge - Power Flow Analysis
================================

Analysis-level orchestration for prepared numerical Power Flow studies.
Numerical execution remains PU-only; engineering result conversion is
performed explicitly at the Analysis boundary.

Author: Subhendu Mishra
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from core.solver.power_flow.input import PowerFlowInput
from core.solver.power_flow.nr_solver import NewtonRaphsonSolver
from core.solver.power_flow.result import PowerFlowResult
from core.analysis.power_flow_result_conversion import (
    EngineeringPowerFlowResult,
    PowerFlowResultConverter,
)


class PowerFlowAnalysis:
    """Coordinate numerical Power Flow execution and result conversion."""

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
        """Execute the numerical study and retain the numerical PU result."""
        self._result = self.solver.solve()
        return self._result

    def to_engineering_result(
        self,
        buses: Iterable[Any],
    ) -> EngineeringPowerFlowResult:
        """Convert the latest numerical result into structured engineering quantities."""
        if self._result is None:
            raise RuntimeError("Power Flow must be solved before converting its result.")
        return PowerFlowResultConverter.to_engineering(
            self._result,
            buses,
        )

    @property
    def result(self) -> PowerFlowResult | None:
        """Return the latest numerical result without consulting Core state."""
        return self._result


__all__ = [
    "PowerFlowAnalysis",
    "EngineeringPowerFlowResult",
    "PowerFlowResultConverter",
]
