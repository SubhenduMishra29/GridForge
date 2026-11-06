"""Backward-compatible short-circuit facade.

Canonical study orchestration is implemented by
``core.analysis.short_circuit.ShortCircuitAnalysis``.  This module contains
no fault mathematics and no numerical execution state.
"""

from __future__ import annotations

from typing import Any


class ShortCircuit:
    """Compatibility adapter to the canonical analysis facade."""

    def __init__(self, network: Any, impedance_matrix: Any = None, sequence_network: Any = None) -> None:
        if impedance_matrix is not None:
            raise ValueError("Legacy impedance_matrix injection is no longer supported; preparation belongs to ShortCircuitAnalysis.")
        from core.analysis.short_circuit import ShortCircuitAnalysis
        self._analysis = ShortCircuitAnalysis(network, sequence_network)

    def calculate_three_phase_fault(self, bus_index: int, Vprefault: Any = None, Zf: Any = 0.0) -> dict:
        bus = self._analysis.network.buses[bus_index]
        result = self._analysis.run_three_phase_fault(getattr(bus, "id", bus), Zf)
        return result.as_dict()

    def calculate_lg_fault(self, elements, Vprefault: Any = None, Zf: Any = 0.0) -> dict:
        result = self._analysis.run_lg_fault(self._default_bus_id(), Zf, elements=elements)
        return result.as_dict()

    def calculate_ll_fault(self, elements, Vprefault: Any = None, Zf: Any = 0.0) -> dict:
        result = self._analysis.run_ll_fault(self._default_bus_id(), Zf, elements=elements)
        return result.as_dict()

    def calculate_llg_fault(self, elements, Vprefault: Any = None, Zf: Any = 0.0) -> dict:
        result = self._analysis.run_llg_fault(self._default_bus_id(), Zf, elements=elements)
        return result.as_dict()

    def calculate(self, fault_type, bus_index: int, elements=None, Vprefault: Any = None, Zf: Any = 0.0) -> dict:
        bus = self._analysis.network.buses[bus_index]
        result = self._analysis.run(fault_type, getattr(bus, "id", bus), Zf, elements=elements)
        return result.as_dict()

    def build_impedance_matrix(self):
        """Compatibility preparation helper; returns a prepared Zbus copy."""
        self._analysis.network.ensure_bus_index()
        from core.numerical.ybus import YBusBuilder
        from .impedance_matrix import ImpedanceMatrix
        ybus = YBusBuilder(self._analysis.network).build()
        return ImpedanceMatrix(ybus.matrix, tuple(bus.id for bus in self._analysis.network.buses)).build()

    def get_thevenin_impedance(self, bus_index: int):
        bus = self._analysis.network.buses[bus_index]
        prepared = self._analysis.prepare_input("3PH", getattr(bus, "id", bus))
        return prepared.thevenin_impedance

    def summary(self):
        return self._analysis.summary()

    def _default_bus_id(self):
        if not self._analysis.network.buses:
            raise ValueError("Network contains no buses.")
        return self._analysis.network.buses[0].id


__all__ = ["ShortCircuit"]
