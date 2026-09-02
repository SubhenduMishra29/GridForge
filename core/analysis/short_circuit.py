"""Public short-circuit study facade and numerical-input preparation."""

from __future__ import annotations

from typing import Any, Optional

from core.numerical.ybus import YBusBuilder
from core.solver.short_circuit import FaultType, ShortCircuitSolver
from core.solver.short_circuit.impedance_matrix import ImpedanceMatrix
from core.solver.short_circuit.input import ShortCircuitInput
from core.solver.short_circuit.result import ShortCircuitResult
from core.solver.short_circuit.sequence_snapshot import SequenceNetworkSnapshot


class ShortCircuitAnalysis:
    """Canonical study boundary: prepare Core state, then invoke the solver."""

    def __init__(self, network: Any, sequence_network: Optional[Any] = None) -> None:
        self.network = network
        self.sequence_network = sequence_network
        self.result: ShortCircuitResult | None = None
        self._validate_network()

    def run(
        self,
        fault_type: FaultType,
        fault_bus: Any,
        Zf: complex = 0.0,
        elements: Any | None = None,
    ) -> ShortCircuitResult:
        normalized_type = FaultType.from_value(fault_type)
        self._validate_fault_request(normalized_type, fault_bus, Zf)
        input_data = self.prepare_input(normalized_type, fault_bus, Zf, elements=elements)
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
        """Read authoritative Core state once and return a detached numerical input."""
        normalized_type = FaultType.from_value(fault_type)
        self._validate_fault_request(normalized_type, fault_bus, Zf)
        bus_index, bus_id = self._resolve_fault_bus(fault_bus)
        bus_ids = tuple(bus.id for bus in self.network.buses)
        prefault_voltage = self._prepare_prefault_voltage(bus_index)

        thevenin_impedance = None
        zbus = None
        if normalized_type is FaultType.THREE_PHASE:
            self.network.ensure_bus_index()
            ybus = YBusBuilder(self.network).build()
            impedance = ImpedanceMatrix(ybus.matrix, bus_ids)
            zbus = tuple(tuple(complex(value) for value in row) for row in impedance.build().tolist())
            thevenin_impedance = impedance.get_thevenin_impedance(bus_index)

        sequence_snapshot = None
        sequence_elements = ()
        if normalized_type.is_unbalanced:
            if self.sequence_network is None:
                raise ValueError("A SequenceNetwork is required for unsymmetrical fault studies.")
            sequence_snapshot = SequenceNetworkSnapshot.from_sequence_network(self.sequence_network)
            sequence_elements = tuple(elements) if elements is not None else tuple(sequence_snapshot.positive.keys())
            if not sequence_elements:
                raise ValueError("At least one sequence-network element is required for an unsymmetrical fault study.")

        return ShortCircuitInput(
            fault_type=normalized_type,
            fault_bus_index=bus_index,
            fault_bus_id=bus_id,
            prefault_voltage=prefault_voltage,
            fault_impedance=complex(Zf),
            bus_ids=bus_ids,
            thevenin_impedance=thevenin_impedance,
            zbus=zbus,
            sequence_snapshot=sequence_snapshot,
            sequence_elements=sequence_elements,
        )

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

    def _validate_network(self) -> None:
        if self.network is None or not hasattr(self.network, "buses"):
            raise ValueError("Short Circuit Analysis requires a valid Network with buses.")
        if len(self.network.buses) == 0:
            raise ValueError("Short Circuit Analysis requires at least one bus.")

    def _validate_fault_request(self, fault_type: FaultType, fault_bus: Any, Zf: complex) -> None:
        if not isinstance(fault_type, FaultType):
            raise ValueError("fault_type must be a FaultType or supported string.")
        if fault_bus is None:
            raise ValueError("fault_bus cannot be None.")
        try:
            impedance = complex(Zf)
        except (TypeError, ValueError) as exc:
            raise ValueError("Zf must be a numeric fault impedance.") from exc
        if not (impedance.real == impedance.real and impedance.imag == impedance.imag):
            raise ValueError("Zf must contain finite real and imaginary components.")
        self._validate_fault_bus(fault_bus)

    def _resolve_fault_bus(self, fault_bus: Any) -> tuple[int, Any]:
        self.network.ensure_bus_index()
        mapping = self.network.index.mapping
        candidate = getattr(fault_bus, "id", fault_bus)
        if candidate in mapping:
            return mapping[candidate], candidate
        raise ValueError(f"Fault bus '{fault_bus}' was not found in the Network.")

    def _validate_fault_bus(self, fault_bus: Any) -> None:
        self._resolve_fault_bus(fault_bus)

    def _prepare_prefault_voltage(self, bus_index: int) -> complex:
        bus = self.network.buses[bus_index]
        try:
            magnitude = float(bus.V)
            angle = float(bus.theta)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("Bus prefault voltage state must contain numerical V and theta values.") from exc
        if not (magnitude == magnitude and angle == angle) or magnitude < 0.0:
            raise ValueError("Bus prefault voltage state must be finite and non-negative in magnitude.")
        import cmath
        return magnitude * cmath.exp(1j * angle)


ShortCircuitAnalyzer = ShortCircuitAnalysis

__all__ = ["ShortCircuitAnalysis", "ShortCircuitAnalyzer", "FaultType"]
