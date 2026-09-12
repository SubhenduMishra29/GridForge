"""Regression coverage for the Logic comparator Control-domain imports."""

from core.control.logic.comparators import UndervoltageComparator


def test_undervoltage_comparator_uses_logic_control_base_contract() -> None:
    comparator = UndervoltageComparator("uv-1", pickup=0.95)

    result = comparator.evaluate(
        comparator.initial_state(),
        {"VALUE": 0.90},
        0.0,
    )

    assert result.outputs == {"TRIP": True}
    assert result.time == 0.0
