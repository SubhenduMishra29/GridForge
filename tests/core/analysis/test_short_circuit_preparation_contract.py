"""Targeted short-circuit preparation boundary tests.

Author: Subhendu Mishra
"""

from types import SimpleNamespace

import numpy as np

from core.analysis.short_circuit_preparation import ShortCircuitPreparation
from core.model.bus import Bus
from core.network.network import Network
from core.solver.short_circuit.fault_types import FaultType


def test_short_circuit_preparation_returns_detached_sequence_snapshot():
    buses = (Bus("B1", voltage_pu=1.0), Bus("B2", voltage_pu=1.0))
    sequence_network = SimpleNamespace(
        positive={"G1": 0.2 + 0.1j},
        negative={"G1": 0.2 + 0.1j},
        zero={"G1": 0.3 + 0.2j},
        has_matrix=lambda name: name == "positive",
        get_matrix=lambda name: np.eye(2, dtype=complex) * (0.1 + 0.05j),
    )
    network = Network()
    network.add_bus(buses[0])
    network.add_bus(buses[1])
    network.rebuild_topology()
    preparation = ShortCircuitPreparation(network, sequence_network)

    prepared = preparation.prepare(FaultType.THREE_PHASE, buses[0])
    sequence_network.positive["G1"] = 9.0 + 9.0j

    assert prepared.fault_bus_id == "B1"
    assert prepared.bus_ids == ("B1", "B2")
    assert prepared.sequence_snapshot.get_impedance("G1", "positive") == 0.2 + 0.1j


def test_short_circuit_preparation_requires_sequence_network_for_unbalanced_faults():
    bus = Bus("B1", voltage_pu=1.0)
    network = Network()
    network.add_bus(bus)
    network.rebuild_topology()
    preparation = ShortCircuitPreparation(network, None)

    try:
        preparation.prepare(FaultType.SINGLE_LINE_GROUND, bus)
    except ValueError as exc:
        assert "sequence" in str(exc).lower()
    else:
        raise AssertionError("Unbalanced faults must require sequence-network preparation data.")


def test_phase_domain_coverage_rejects_active_line_without_conductor_system():
    network = SimpleNamespace(
        lines=[SimpleNamespace(id="L1", in_service=True)],
        cables=[],
    )
    topology = SimpleNamespace(branches=())

    try:
        ShortCircuitPreparation._require_complete_physical_conductor_coverage(
            network, topology
        )
    except ValueError as exc:
        assert "L1" in str(exc)
        assert "physical conductor system" in str(exc)
    else:
        raise AssertionError(
            "Phase-domain preparation must reject an active Line omitted from physical conductor data."
        )


def test_phase_domain_coverage_allows_inactive_scalar_branch():
    network = SimpleNamespace(
        lines=[SimpleNamespace(id="L1", in_service=False)],
        cables=[],
    )
    topology = SimpleNamespace(branches=())

    ShortCircuitPreparation._require_complete_physical_conductor_coverage(
        network, topology
    )


def test_phase_domain_coverage_accepts_explicitly_configured_active_branches():
    network = SimpleNamespace(
        lines=[SimpleNamespace(id="L1", in_service=True)],
        cables=[SimpleNamespace(id="C1", in_service=True)],
    )
    topology = SimpleNamespace(branches=(
        SimpleNamespace(equipment_id="L1", in_service=True),
        SimpleNamespace(equipment_id="C1", in_service=True),
    ))

    ShortCircuitPreparation._require_complete_physical_conductor_coverage(
        network, topology
    )
