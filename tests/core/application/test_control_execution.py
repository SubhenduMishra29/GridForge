from core.application.command_manager import CommandManager
from core.application.control_dispatch import ControlCommandDispatcher
from core.application.control_execution import ControlExecutionService
from core.application.results import ApplicationResult
from core.control.decision import ControlActionType, ControlDecision
from core.control.engine import ControlEvaluationResult


def _decision(control_id: str, action: ControlActionType, valid: bool = True) -> ControlDecision:
    return ControlDecision(
        control_id=control_id,
        action_type=action,
        target_equipment_id="BRK-1",
        reason="test action",
        simulation_time=1.0,
        valid=valid,
    )


def _service_with_recorder(calls: list[str]) -> ControlExecutionService:
    dispatcher = ControlCommandDispatcher(CommandManager(context=object()))

    def execute(decision: ControlDecision) -> ApplicationResult:
        calls.append(decision.control_id)
        if decision.control_id == "fail":
            raise RuntimeError("dispatch failed")
        return ApplicationResult.success_result(value=decision.control_id)

    dispatcher.execute = execute  # type: ignore[method-assign]
    return ControlExecutionService(dispatcher)


def test_execution_dispatches_only_valid_decisions_in_evaluation_order() -> None:
    calls: list[str] = []
    service = _service_with_recorder(calls)
    evaluation = ControlEvaluationResult(
        simulation_time=1.0,
        decisions=(_decision("trip", ControlActionType.TRIP), _decision("blocked", ControlActionType.OPEN, False)),
        blocked_actions=(_decision("interlock", ControlActionType.CLOSE, False),),
    )

    result = service.execute(evaluation)

    assert calls == ["trip"]
    assert result.executed_decisions == evaluation.decisions[:1]
    assert result.failed_decisions == ()
    assert result.application_results[0].success is True


def test_execution_records_dispatch_failure_and_continues_deterministically() -> None:
    calls: list[str] = []
    service = _service_with_recorder(calls)
    evaluation = ControlEvaluationResult(
        simulation_time=1.0,
        decisions=(
            _decision("first", ControlActionType.TRIP),
            _decision("fail", ControlActionType.OPEN),
            _decision("last", ControlActionType.CLOSE),
        ),
    )

    result = service.execute(evaluation)

    assert calls == ["first", "fail", "last"]
    assert tuple(item.control_id for item in result.executed_decisions) == ("first", "last")
    assert tuple(item.control_id for item in result.failed_decisions) == ("fail",)
    assert "fail" in result.diagnostics[0]
