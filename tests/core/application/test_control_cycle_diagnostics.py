import pytest

from core.application.control_cycle import ControlCycleResult
from core.application.control_execution import ControlExecutionResult
from core.control.decision import ControlActionType, ControlDecision
from core.control.engine import ControlEvaluationResult


def _decision(
    control_id: str,
    *,
    valid: bool = True,
    diagnostic: str | None = None,
) -> ControlDecision:
    return ControlDecision(
        control_id=control_id,
        action_type=ControlActionType.TRIP,
        target_equipment_id="BRK-1",
        reason="test action",
        simulation_time=1.0,
        valid=valid,
        diagnostic=diagnostic,
    )


def test_cycle_keeps_evaluation_and_execution_diagnostics_separate() -> None:
    evaluation = ControlEvaluationResult(
        simulation_time=1.0,
        diagnostics=("evaluation failed: missing input",),
    )
    failed = _decision("failed")
    execution = ControlExecutionResult(
        failed_decisions=(failed,),
        diagnostics=("Control 'failed' execution failed: dispatch failed",),
    )

    result = ControlCycleResult(evaluation=evaluation, execution=execution)

    assert result.evaluation_diagnostics == ("evaluation failed: missing input",)
    assert result.execution_diagnostics == (
        "Control 'failed' execution failed: dispatch failed",
    )
    assert result.diagnostics == (
        "evaluation failed: missing input",
        "Control 'failed' execution failed: dispatch failed",
    )


def test_cycle_attributes_blocked_diagnostics_to_originating_decision() -> None:
    blocked = _decision(
        "blocked",
        valid=False,
        diagnostic="Interlock not permissive.",
    )
    evaluation = ControlEvaluationResult(
        simulation_time=1.0,
        blocked_actions=(blocked,),
        diagnostics=(blocked.diagnostic or "",),
    )

    result = ControlCycleResult(
        evaluation=evaluation,
        execution=ControlExecutionResult(blocked_decisions=(blocked,)),
    )

    assert result.blocked_diagnostics == (
        ("blocked", "Interlock not permissive."),
    )


def test_cycle_attributes_execution_failure_to_originating_decision() -> None:
    failed = _decision("failed")
    execution = ControlExecutionResult(
        failed_decisions=(failed,),
        diagnostics=("Control 'failed' execution failed: dispatch failed",),
    )
    result = ControlCycleResult(
        evaluation=ControlEvaluationResult(simulation_time=1.0),
        execution=execution,
    )

    assert result.execution_failure_diagnostics == (
        ("failed", "Control 'failed' execution failed: dispatch failed"),
    )


def test_cycle_rejects_mismatched_blocked_decision_provenance() -> None:
    blocked = _decision("blocked", valid=False, diagnostic="blocked")
    other = _decision("other", valid=False, diagnostic="other")

    with pytest.raises(ValueError, match="blocked_decisions must match evaluation"):
        ControlCycleResult(
            evaluation=ControlEvaluationResult(
                simulation_time=1.0,
                blocked_actions=(blocked,),
            ),
            execution=ControlExecutionResult(blocked_decisions=(other,)),
        )
