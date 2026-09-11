"""Targeted regression specifications for short-circuit contribution completeness."""

from types import SimpleNamespace

from core.solver.short_circuit.fault_types import FaultType
from core.solver.short_circuit.input import ShortCircuitInput
from core.solver.short_circuit.sequence_snapshot import (
    SequenceBranchSnapshot,
    SequenceNetworkSnapshot,
    SequenceSourceSnapshot,
)
from core.solver.short_circuit.short_circuit_solver import ShortCircuitSolver
from core.solver.short_circuit.result import ContributionStatus, ShortCircuitBranchCurrent


def _input(snapshot):
    return ShortCircuitInput(
        fault_type=FaultType.LINE_LINE,
        fault_bus_index=0,
        fault_bus_id="B1",
        prefault_voltage=1 + 0j,
        fault_impedance=0j,
        bus_ids=("B1", "B2"),
        thevenin_impedance=0.1j,
        zbus=((0.1j, 0j), (0j, 0.1j)),
        sequence_snapshot=snapshot,
        sequence_elements=("BR1",),
        prefault_voltages=(1 + 0j, 1 + 0j),
    )


def test_incomplete_prepared_branch_contribution_is_reported_as_partial():
    snapshot = SequenceNetworkSnapshot(
        positive={"BR1": 0.1j},
        negative={"BR1": 0.1j},
        zero={},
        bus_ids=("B1", "B2"),
        branches=(SequenceBranchSnapshot("BR1", "B1", "B2", 0, 1, 0.1j, None, None, "Line"),),
        sources=(),
        positive_matrix=((0.1j, 0j), (0j, 0.1j)),
        negative_matrix=((0.1j, 0j), (0j, 0.1j)),
    )
    solver = ShortCircuitSolver(_input(snapshot))
    branch = ShortCircuitBranchCurrent(
        branch_id="BR1",
        from_bus_id="B1",
        to_bus_id="B2",
        current=1 + 0j,
        magnitude=1.0,
        angle_deg=0.0,
    )

    status, diagnostics = solver._contribution_status({}, {}, {})

    assert status is ContributionStatus.PARTIAL
    assert "BR1" in " ".join(diagnostics)


def test_no_prepared_contribution_records_are_explicitly_unavailable():
    snapshot = SequenceNetworkSnapshot(
        positive={},
        negative={},
        zero={},
        bus_ids=("B1", "B2"),
        branches=(),
        sources=(),
    )
    solver = ShortCircuitSolver(_input(snapshot))

    status, diagnostics = solver._contribution_status({}, {}, {})

    assert status is ContributionStatus.UNAVAILABLE
    assert diagnostics
