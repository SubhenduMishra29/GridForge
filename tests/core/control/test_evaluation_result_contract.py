import pytest

from core.control.decision import ControlActionType, ControlDecision
from core.control.engine import ControlEvaluationResult


def _decision(control_id: str, *, valid: bool = True) -> ControlDecision:
    return ControlDecision(
        control_id=control_id,
        action_type=ControlActionType.TRIP,
        target_equipment_id="BRK-1",
        reason="test action",
        simulation_time=1.0,
        valid=valid,
        diagnostic=None if valid else "blocked",
    )


def test_evaluation_result_rejects_invalid_decision_in_executable_decisions() -> None:
    with pytest.raises(ValueError, match="decisions must contain only valid"):
        ControlEvaluationResult(
            simulation_time=1.0,
            decisions=(_decision("blocked", valid=False),),
        )


def test_evaluation_result_requires_blocked_actions_to_be_invalid() -> None:
    with pytest.raises(ValueError, match="blocked_actions must contain only invalid"):
        ControlEvaluationResult(
            simulation_time=1.0,
            blocked_actions=(_decision("accepted"),),
        )


def test_evaluation_result_rejects_decision_present_in_both_outcome_sets() -> None:
    blocked = _decision("blocked", valid=False)
    with pytest.raises(ValueError, match="cannot appear in both"):
        ControlEvaluationResult(
            simulation_time=1.0,
            decisions=(),
            blocked_actions=(blocked,),
            diagnostics=("blocked",),
        )
