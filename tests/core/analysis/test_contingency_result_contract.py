"""Targeted regression specifications for contingency result interpretation."""

from types import SimpleNamespace

import pytest

from core.analysis.contingency import ContingencyAnalysis
from core.solver.power_flow.result import PowerFlowResult


def test_contingency_uses_power_flow_success_and_voltage_magnitudes_by_stable_id():
    result = PowerFlowResult(
        success=True,
        iterations=3,
        error=1.0e-8,
        pv_to_pq=(),
        history=(1.0, 1.0e-8),
        message="converged",
        voltage_magnitudes=(0.94, 1.06),
        voltage_angles=(0.0, 0.0),
    )
    network = SimpleNamespace(
        buses=(SimpleNamespace(id="B-20"), SimpleNamespace(id="B-10")),
        lines=(),
        transformers=(),
        generators=(),
        loads=(),
        shunts=(),
    )
    analysis = ContingencyAnalysis.__new__(ContingencyAnalysis)

    violations = analysis._detect_voltage_violations(
        ("B-20", "B-10"),
        result.voltage_magnitudes,
        0.95,
        1.05,
    )

    assert analysis._result_converged(result) is True
    assert [item.element_id for item in violations] == ["B-20", "B-10"]
    assert [item.category for item in violations] == ["voltage_low", "voltage_high"]


def test_legacy_converged_field_is_only_a_compatibility_fallback():
    legacy = SimpleNamespace(converged=True)
    modern = SimpleNamespace(success=False, converged=True)
    analysis = ContingencyAnalysis.__new__(ContingencyAnalysis)

    assert analysis._result_converged(legacy) is True
    assert analysis._result_converged(modern) is False


def test_missing_power_flow_voltage_identity_is_rejected():
    analysis = ContingencyAnalysis.__new__(ContingencyAnalysis)
    prepared = SimpleNamespace(bus_ids=("B1", "B2"))
    result = SimpleNamespace(voltage_magnitudes=(1.0,))
    with pytest.raises(ValueError, match="identity ordering"):
        analysis._detect_violations(
            SimpleNamespace(lines=(), transformers=()),
            prepared,
            result,
            voltage_min=0.95,
            voltage_max=1.05,
            thermal_limit=100.0,
        )
