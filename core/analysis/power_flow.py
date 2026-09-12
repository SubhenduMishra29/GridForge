"""
GridForge - Power Flow Analysis
================================

Analysis-level orchestration for prepared numerical Power Flow studies.
Numerical execution remains PU-only; engineering result conversion is
performed explicitly at the Analysis boundary.

Author: Subhendu Mishra
"""

from __future__ import annotations

from typing import Optional

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.power_flow_preparation import PreparedPowerFlow, PowerFlowPreparation
from core.solver.power_flow.input import PowerFlowInput
from core.solver.power_flow.nr_solver import NewtonRaphsonSolver
from core.solver.power_flow.result import PowerFlowResult
from core.analysis.power_flow_result_conversion import (
    EngineeringPowerFlowResult,
    PowerFlowResultConverter,
)


class PowerFlowAnalysis:
    """Coordinate preparation, numerical Power Flow execution, and result conversion."""

    def __init__(
        self,
        input_data: PowerFlowInput,
        ybus,
        options: Optional[object] = None,
        *,
        prepared: PreparedPowerFlow | None = None,
    ) -> None:
        if not isinstance(input_data, PowerFlowInput):
            raise TypeError("input_data must be PowerFlowInput.")
        if ybus is None:
            raise ValueError("Power Flow requires a prepared YBus.")
        if getattr(ybus, "shape", None) != (input_data.bus_count, input_data.bus_count):
            raise ValueError("Prepared YBus dimension does not match PowerFlowInput.")
        if not hasattr(ybus, "bus_ids") or tuple(ybus.bus_ids) != input_data.bus_ids:
            raise ValueError("Prepared YBus ordering does not match PowerFlowInput.")
        if prepared is not None:
            if not isinstance(prepared, PreparedPowerFlow):
                raise TypeError("prepared must be a PreparedPowerFlow instance.")
            if prepared.input is not input_data or prepared.ybus is not ybus:
                raise ValueError("Prepared Power Flow must own the supplied input and YBus.")
        if options is None:
            from core.solver.power_flow.solver_options import SolverOptions
            options = SolverOptions()
        self.input = input_data
        self.Ybus = ybus
        self.prepared = prepared
        self.options = options
        self.solver = NewtonRaphsonSolver(input_data, ybus, options)
        self._result: PowerFlowResult | None = None

    @classmethod
    def from_prepared(
        cls,
        prepared: PreparedPowerFlow,
        options: Optional[object] = None,
    ) -> "PowerFlowAnalysis":
        """Create analysis directly from one detached prepared snapshot."""
        if not isinstance(prepared, PreparedPowerFlow):
            raise TypeError("prepared must be a PreparedPowerFlow instance.")
        return cls(prepared.input, prepared.ybus, options, prepared=prepared)

    @classmethod
    def from_network(
        cls,
        network,
        power_flow_configuration: PowerFlowStudyConfiguration,
        options: Optional[object] = None,
    ) -> "PowerFlowAnalysis":
        """Prepare a Network once, then construct analysis from its detached snapshot."""
        prepared = PowerFlowPreparation.prepare(network, power_flow_configuration)
        return cls.from_prepared(prepared, options)

    def solve(self) -> PowerFlowResult:
        """Execute the numerical study and retain the numerical PU result."""
        self._result = self.solver.solve()
        return self._result

    def to_engineering_result(self) -> EngineeringPowerFlowResult:
        """Convert the latest result using only the detached prepared snapshot."""
        if self._result is None:
            raise RuntimeError("Power Flow must be solved before converting its result.")
        if self.prepared is None:
            raise RuntimeError("Engineering conversion requires a prepared Power Flow snapshot.")
        return PowerFlowResultConverter.to_engineering(
            self._result,
            self.prepared.input.bus_ids,
            self.prepared.bus_voltage_bases,
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
