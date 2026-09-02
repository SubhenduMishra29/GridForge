"""Numerical short-circuit execution boundary."""

from __future__ import annotations

from .fault_types import FaultType
from .input import ShortCircuitInput
from .result import ShortCircuitResult
from .symmetrical_fault import SymmetricalFault
from .unsymmetrical_fault import UnsymmetricalFault


class ShortCircuitSolver:
    """Execute a prepared short-circuit problem without live Core access."""

    def __init__(self, input_data: ShortCircuitInput) -> None:
        if not isinstance(input_data, ShortCircuitInput):
            raise TypeError("ShortCircuitSolver requires a ShortCircuitInput.")
        self.input = input_data
        self.last_result: ShortCircuitResult | None = None

    def _execute(self) -> dict:
        data = self.input
        if data.fault_type is FaultType.THREE_PHASE:
            if data.thevenin_impedance is None:
                raise ValueError("Three-phase short-circuit input requires a Thevenin impedance.")
            return SymmetricalFault(data.thevenin_impedance).calculate_three_phase_fault(
                bus_index=data.fault_bus_index,
                Vprefault=data.prefault_voltage,
                Zf=data.fault_impedance,
            )

        if data.sequence_snapshot is None:
            raise ValueError("Unsymmetrical short-circuit input requires a sequence snapshot.")
        if not data.sequence_elements:
            raise ValueError("Unsymmetrical short-circuit input requires sequence elements.")

        return UnsymmetricalFault(data.sequence_snapshot).calculate(
            fault_type=data.fault_type,
            elements=data.sequence_elements,
            Vprefault=data.prefault_voltage,
            Zf=data.fault_impedance,
        )

    def solve(self) -> ShortCircuitResult:
        """Execute exactly once from the immutable input contract."""
        values = self._execute()
        result = ShortCircuitResult(
            fault_type=self.input.fault_type,
            fault_bus_index=self.input.fault_bus_index,
            fault_bus_id=self.input.fault_bus_id,
            success=True,
            values=values,
        )
        self.last_result = result
        return result

    def calculate(self) -> ShortCircuitResult:
        """Explicit alias for the solver execution operation."""
        return self.solve()

    def reset(self) -> None:
        self.last_result = None

    def summary(self) -> dict:
        return {
            "solver": "ShortCircuitSolver",
            "version": "2.0",
            "fault_type": self.input.fault_type.value,
            "bus_index": self.input.fault_bus_index,
            "sequence_data_available": self.input.sequence_snapshot is not None,
            "last_result_available": self.last_result is not None,
        }

    def __repr__(self) -> str:
        return (
            "ShortCircuitSolver("
            f"fault_type={self.input.fault_type.value}, "
            f"bus_index={self.input.fault_bus_index}"
            ")"
        )


__all__ = ["ShortCircuitSolver"]
