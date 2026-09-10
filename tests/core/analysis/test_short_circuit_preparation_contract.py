"""Targeted short-circuit preparation boundary tests.

Author: Subhendu Mishra
"""

from types import SimpleNamespace

import numpy as np

from core.analysis.short_circuit_preparation import ShortCircuitPreparation
from core.solver.short_circuit.fault_types import FaultType


def test_short_circuit_preparation_returns_detached_sequence_snapshot():
    buses = (
        SimpleNamespace(id="B1", V=1.0, theta=0.0),
        SimpleNamespace(id="B2", V=1.0, theta=0.0),
    )
    sequence_network = SimpleNamespace(
        positive={"G1": 0.2 + 0.1j},
        negative={"G1": 0.2 + 0.1j},
        zero={"G1": 0.3 + 0.2j},
        has_matrix=lambda name: name == "positive",
        get_matrix=lambda name: np.eye(2, dtype=complex) * (0.1 + 0.05j),
    )
    network = SimpleNamespace(buses=buses)
    preparation = ShortCircuitPreparation(network, sequence_network)

    prepared = preparation.prepare(FaultType.THREE_PHASE, buses[0])
    sequence_network.positive["G1"] = 9.0 + 9.0j

    assert prepared.fault_bus_id == "B1"
    assert prepared.bus_ids == ("B1", "B2")
    assert prepared.sequence_snapshot.get_impedance("G1", "positive") == 0.2 + 0.1j


def test_short_circuit_preparation_requires_sequence_network_for_unbalanced_faults():
    bus = SimpleNamespace(id="B1", V=1.0, theta=0.0)
    preparation = ShortCircuitPreparation(SimpleNamespace(buses=(bus,)), None)

    try:
        preparation.prepare(FaultType.SINGLE_LINE_GROUND, bus)
    except ValueError as exc:
        assert "SequenceNetwork" in str(exc)
    else:
        raise AssertionError("Unbalanced faults must require sequence-network preparation data.")
