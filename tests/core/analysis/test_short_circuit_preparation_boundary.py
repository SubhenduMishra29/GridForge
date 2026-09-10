"""Regression contracts for detached Short Circuit preparation."""

import pytest

from core.analysis.short_circuit import ShortCircuitAnalysis
from core.solver.short_circuit import FaultType


class _Bus:
    def __init__(self, bus_id):
        self.id = bus_id
        self.V = 1.0
        self.theta = 0.0


class _Network:
    def __init__(self):
        self.buses = [_Bus("bus-1"), _Bus("bus-2")]

    def ensure_bus_index(self):
        raise AssertionError("Short Circuit preparation must not mutate or index Network state.")


class _SequenceNetwork:
    positive = {"line-1": 0.1 + 0.2j}
    negative = {"line-1": 0.1 + 0.2j}
    zero = {"line-1": 0.3 + 0.4j}

    def has_matrix(self, sequence):
        return sequence == "positive"

    def get_matrix(self, sequence):
        if sequence != "positive":
            raise ValueError(sequence)
        return ((10 + 0j, -10 + 0j), (-10 + 0j, 10 + 0j))


def test_fault_bus_resolution_is_local_and_does_not_require_network_indexing():
    analysis = ShortCircuitAnalysis(_Network(), _SequenceNetwork())
    prepared = analysis.prepare_input(FaultType.THREE_PHASE, "bus-2")

    assert prepared.fault_bus_id == "bus-2"
    assert prepared.fault_bus_index == 1
    assert prepared.bus_ids == ("bus-1", "bus-2")


def test_three_phase_preparation_requires_declared_positive_sequence_matrix():
    network = _Network()
    analysis = ShortCircuitAnalysis(network, None)

    with pytest.raises(ValueError, match="positive-sequence impedance matrix"):
        analysis.prepare_input(FaultType.THREE_PHASE, "bus-1")
