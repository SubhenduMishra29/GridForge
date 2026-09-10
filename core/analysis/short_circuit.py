"""Public Short-Circuit study facade.

Author: Subhendu Mishra

The facade owns study orchestration only. Numerical input preparation is
performed by ``ShortCircuitPreparation`` and solver execution consumes its
detached ``ShortCircuitInput``.
"""

from __future__ import annotations

from typing import Any, Optional

from core.solver.short_circuit import FaultType, ShortCircuitSolver
from core.solver.short_circuit.input import ShortCircuitInput
from core.solver.short_circuit.result import ShortCircuitResult
from .short_circuit_preparation import ShortCircuitPreparation


class ShortCircuitAnalysis:
    """Canonical study facade: prepare detached data, then invoke the solver."""

    def __init__(self, network: Any, sequence_network: Optional[Any] = None) -> None:
        self.network = network
        self.sequence_network = sequence_network
        self.preparation = ShortCircuitPreparation(network, sequence_network)
        self.result: ShortCircuitResult | None = None

    def run(
        self,
        fault_type: FaultType,
        fault_bus: Any,
        Zf: complex = 0.0,
        elements: Any | None = None,
    ) -> ShortCircuitResult:
        input_data = self.prepare_input(fault_type, fault_bus, Zf, elements=elements)
        self.result = ShortCircuitSolver(input_data).solve()
        return self.result

    def prepare_input(
        self,
        fault_type: FaultType,
        fault_bus: Any,
        Zf: complex = 0.0,
        *,
        elements: Any | None = None,
    ) -> ShortCircuitInput:
        """Return detached solver input produced by the canonical preparation boundary."""
        return self.preparation.prepare(fault_type, fault_bus, Zf, elements=elements)

    def run_three_phase_fault(self, fault_bus: Any, Zf: complex = 0.0) -> ShortCircuitResult:
        return self.run(FaultType.THREE_PHASE, fault_bus, Zf)

    def run_lg_fault(self, fault_bus: Any, Zf: complex = 0.0, elements: Any | None = None) -> ShortCircuitResult:
        return self.run(FaultType.SINGLE_LINE_GROUND, fault_bus, Zf, elements=elements)

    def run_ll_fault(self, fault_bus: Any, Zf: complex = 0.0, elements: Any | None = None) -> ShortCircuitResult:
        return self.run(FaultType.LINE_LINE, fault_bus, Zf, elements=elements)

    def run_llg_fault(self, fault_bus: Any, Zf: complex = 0.0, elements: Any | None = None) -> ShortCircuitResult:
        return self.run(FaultType.DOUBLE_LINE_GROUND, fault_bus, Zf, elements=elements)

    def summary(self) -> Any:
        return {"status": "NOT_RUN"} if self.result is None else self.result


ShortCircuitAnalyzer = ShortCircuitAnalysis

__all__ = ["ShortCircuitAnalysis", "ShortCircuitAnalyzer", "FaultType"]
