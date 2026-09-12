# ============================================================
# File: core/analysis/short_circuit.py
# GridForge V2 — Short Circuit Analysis
# Author: Subhendu Mishra
# ============================================================
"""Public Short-Circuit study facade over detached solver input."""

from __future__ import annotations

from core.solver.short_circuit import FaultType, ShortCircuitSolver
from core.solver.short_circuit.input import ShortCircuitInput
from core.solver.short_circuit.result import ShortCircuitResult
from .short_circuit_configuration import ShortCircuitStudyConfiguration
from .short_circuit_preparation import ShortCircuitPreparation


class ShortCircuitAnalysis:
    """Canonical study facade: consume prepared immutable solver input only."""

    def __init__(self, input_data: ShortCircuitInput) -> None:
        if not isinstance(input_data, ShortCircuitInput):
            raise TypeError("input_data must be ShortCircuitInput.")
        self.input = input_data
        self.result: ShortCircuitResult | None = None

    @classmethod
    def from_prepared(cls, input_data: ShortCircuitInput) -> "ShortCircuitAnalysis":
        """Create analysis directly from one detached solver snapshot."""
        return cls(input_data)

    @classmethod
    def from_network(
        cls,
        network,
        configuration: ShortCircuitStudyConfiguration,
        *,
        sequence_network=None,
        base_mva: float | None = None,
    ) -> "ShortCircuitAnalysis":
        if not isinstance(configuration, ShortCircuitStudyConfiguration):
            raise TypeError("configuration must be ShortCircuitStudyConfiguration.")
        preparation = ShortCircuitPreparation(network, sequence_network, base_mva=base_mva)
        input_data = preparation.prepare(
            configuration.fault_type,
            configuration.fault_bus_id,
            configuration.fault_impedance,
            elements=configuration.element_ids or None,
        )
        return cls.from_prepared(input_data)

    def run(self) -> ShortCircuitResult:
        """Execute the detached Short-Circuit study."""
        self.result = ShortCircuitSolver(self.input).solve()
        return self.result

    def summary(self):
        return {"status": "NOT_RUN"} if self.result is None else self.result


ShortCircuitAnalyzer = ShortCircuitAnalysis

__all__ = [
    "ShortCircuitAnalysis",
    "ShortCircuitAnalyzer",
    "ShortCircuitStudyConfiguration",
    "FaultType",
]
