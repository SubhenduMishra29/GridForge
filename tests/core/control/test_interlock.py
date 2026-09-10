from __future__ import annotations

import pytest

from core.control.interlock import ControlInterlock


def test_interlock_allows_when_all_permissives_are_true() -> None:
    result = ControlInterlock("INT-101", required_inputs=("PERMIT",)).evaluate(
        {"PERMIT": True}, 5.0
    )
    assert result.allowed is True


def test_interlock_blocks_when_permissive_is_missing_or_false() -> None:
    result = ControlInterlock("INT-101", required_inputs=("PERMIT", "SAFE")).evaluate(
        {"PERMIT": True, "SAFE": False}, 5.0
    )
    assert result.allowed is False
    assert "SAFE" in result.diagnostic


def test_interlock_rejects_nonfinite_simulation_time() -> None:
    with pytest.raises(ValueError, match="finite"):
        ControlInterlock("INT-101").evaluate({}, float("nan"))
