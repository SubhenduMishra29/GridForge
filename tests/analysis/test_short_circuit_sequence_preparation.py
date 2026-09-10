import numpy as np
import pytest

from core.analysis.sequence_network_preparation import SequenceNetworkPreparation
from core.analysis.short_circuit_preparation import ShortCircuitPreparation
from core.model.bus import Bus
from core.model.grid import Grid
from core.model.generator import Generator
from core.network.network import Network
from core.solver.short_circuit.short_circuit_solver import ShortCircuitSolver
from core.solver.short_circuit.fault_types import FaultType


def _single_source_network():
    network = Network()
    bus = Bus("B1", nominal_voltage_kv=11.0)
    network.add_bus(bus)
    grid = Grid("G1", endpoint=bus, z1_pu=0.1j, z2_pu=0.1j, z0_pu=0.2j)
    network.add_grid(grid)
    return network, bus


def test_grid_source_builds_all_sequence_matrices():
    network, _ = _single_source_network()
    prepared = SequenceNetworkPreparation(network).prepare()
    assert prepared.has_matrix("positive")
    assert prepared.has_matrix("negative")
    assert prepared.has_matrix("zero")
    assert prepared.get_driving_point_impedance("positive", 0) == pytest.approx(0.1j)
    assert prepared.get_driving_point_impedance("zero", 0) == pytest.approx(0.2j)


def test_short_circuit_preparation_creates_network_driving_point_data():
    network, bus = _single_source_network()
    input_data = ShortCircuitPreparation(network).prepare(FaultType.THREE_PHASE, bus)
    assert input_data.fault_bus_id == "B1"
    assert input_data.fault_bus_index == 0
    assert input_data.thevenin_impedance == pytest.approx(0.1j)
    assert input_data.zbus == ((pytest.approx(0.1j),),)


def test_unsymmetrical_solver_uses_fault_bus_sequence_matrices():
    network, bus = _single_source_network()
    input_data = ShortCircuitPreparation(network).prepare(FaultType.SINGLE_LINE_GROUND, bus)
    result = ShortCircuitSolver(input_data).solve()
    assert result.success
    assert result.values["Z1"] == pytest.approx(0.1j)
    assert result.values["Z2"] == pytest.approx(0.1j)
    assert result.values["Z0"] == pytest.approx(0.2j)


def test_fault_bus_identity_is_explicit():
    network, bus = _single_source_network()
    bus2 = Bus("B2", nominal_voltage_kv=11.0)
    network.add_bus(bus2)
    with pytest.raises(ValueError, match="singular"):
        SequenceNetworkPreparation(network).prepare(("positive",))


def test_connected_rotating_machine_requires_explicit_sequence_data():
    network, bus = _single_source_network()
    generator = Generator("GEN1", endpoint=bus)
    network.add_generator(generator)
    with pytest.raises(ValueError, match="lacks explicit short-circuit sequence data"):
        SequenceNetworkPreparation(network).prepare(("positive",))


def test_snapshot_is_detached_from_sequence_network():
    network, _ = _single_source_network()
    sequence = SequenceNetworkPreparation(network).prepare(("positive",))
    snapshot = __import__("core.solver.short_circuit.sequence_snapshot", fromlist=["SequenceNetworkSnapshot"]).SequenceNetworkSnapshot.from_sequence_network(sequence)
    before = snapshot.get_driving_point_impedance("positive", 0)
    sequence.set_matrix("positive", np.array([[0.25j]], dtype=complex))
    assert snapshot.get_driving_point_impedance("positive", 0) == before
