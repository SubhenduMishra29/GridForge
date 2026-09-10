import pytest

from core.application.control_cycle import ControlCycleResult
from core.application.control_execution import ControlExecutionResult
from core.control.decision import ControlActionType, ControlDecision
from core.control.engine import ControlEvaluationResult


def _decision(control_id: str, *, time: float = 1.0, valid: bool = True) -> ControlDecision:
    return ControlDecision(
        control_id=control_id,
        action_type=ControlActionType.TRIP,
        target_equipment_id="BRK-1",
        reason="test action",
        simulation_time=time,
        valid=valid,
        diagnostic=None if valid else "blocked",
    )


def _evaluation(*decisions: ControlDecision, time: float = 1.0) -> ControlEvaluationResult:
    return ControlEvaluationResult(simulation_time=time, decisions=decisions)


def test_cycle_rejects_mismatched_simulation_times() -> None:
    evaluation = _evaluation(_decision("trip", time=1.0), time=1.0)
    execution = ControlExecutionResult(
        executed_decisions=evaluation.decisions,
    )
    # The execution result has no time field, so the cycle contract derives
    # temporal consistency from each originating decision as well.
    mismatched = _decision("trip", time=2.0)
    with pytest.raises(ValueError, match="simulation_time"):
        ControlCycleResult(
            evaluation=evaluation,
            execution=ControlExecutionResult(executed_decisions=(mismatched,)),
        )


def test_cycle_accepts_execution_outcomes_from_evaluation_decisions() -> None:
    trip = _decision("trip")
    evaluation = _evaluation(trip)
    execution = ControlExecutionResult(executed_decisions=(trip,))

    result = ControlCycleResult(evaluation=evaluation, execution=execution)

    assert result.execution.executed_decisions == evaluation.decisions


def test_cycle_rejects_execution_decision_not_originating_from_evaluation() -> None:
    evaluation = _evaluation(_decision("trip"))
    foreign = _decision("foreign")

    with pytest.raises(ValueError, match="originate from evaluation"):
        ControlCycleResult(
            evaluation=evaluation,
            execution=ControlExecutionResult(executed_decisions=(foreign,)),
        )


def test_cycle_rejects_decision_in_multiple_execution_outcome_categories() -> None:
    trip = _decision("trip")
    evaluation = _evaluation(trip)

    with pytest.raises(ValueError, match="multiple execution outcome"):
        ControlCycleResult(
            evaluation=evaluation,
            execution=ControlExecutionResult(
                executed_decisions=(trip,),
                failed_decisions=(trip,),
            ),
        )


def test_cycle_preserves_blocked_decisions_as_non_executable_outcomes() -> None:
    blocked = _decision("blocked", valid=False)
    evaluation = ControlEvaluationResult(
        simulation_time=1.0,
        blocked_actions=(blocked,),
    )
    execution = ControlExecutionResult(blocked_decisions=(blocked,))

    result = ControlCycleResult(evaluation=evaluation, execution=execution)

    assert result.execution.executed_decisions == ()
    assert result.execution.failed_decisions == ()
    assert result.execution.blocked_decisions == (blocked,)
