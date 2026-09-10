from core.application.application import Application
from core.application.command_manager import CommandManager
from core.application.control_dispatch import ControlCommandDispatcher
from core.application.control_execution import ControlExecutionService
from core.application.control_cycle import ControlCycleService
from core.application.results import ApplicationResult
from core.control.decision import ControlActionType, ControlDecision
from core.control.engine import ControlEngine, ControlEvaluationResult


class _StubEngine(ControlEngine):
    def __init__(self, evaluation: ControlEvaluationResult) -> None:
        self.evaluation = evaluation

    def evaluate(self, **kwargs) -> ControlEvaluationResult:
        return self.evaluation


def _decision(control_id: str) -> ControlDecision:
    return ControlDecision(
        control_id=control_id,
        action_type=ControlActionType.TRIP,
        target_equipment_id="BRK-1",
        reason="test action",
        simulation_time=1.0,
    )


def test_control_cycle_evaluates_then_executes_through_application_boundary() -> None:
    evaluation = ControlEvaluationResult(
        simulation_time=1.0,
        decisions=(_decision("trip"),),
    )
    engine = _StubEngine(evaluation)
    manager = CommandManager(context=object())
    dispatcher = ControlCommandDispatcher(manager)
    calls: list[str] = []

    def execute(decision: ControlDecision) -> ApplicationResult:
        calls.append(decision.control_id)
        return ApplicationResult.success_result(value=decision.control_id)

    dispatcher.execute = execute  # type: ignore[method-assign]
    service = ControlCycleService(engine, ControlExecutionService(dispatcher))

    result = service.execute(simulation_time=1.0)

    assert result.evaluation is evaluation
    assert result.execution.executed_decisions == evaluation.decisions
    assert calls == ["trip"]


def test_application_facade_owns_control_cycle_orchestration() -> None:
    evaluation = ControlEvaluationResult(
        simulation_time=2.0,
        decisions=(_decision("trip"),),
    )
    engine = _StubEngine(evaluation)
    manager = CommandManager(context=object())
    application = Application(manager)
    calls: list[str] = []

    def execute(decision: ControlDecision) -> ApplicationResult:
        calls.append(decision.control_id)
        return ApplicationResult.success_result(value=decision.control_id)

    application.control_execution.dispatcher.execute = execute  # type: ignore[method-assign]

    result = application.execute_control_cycle(engine, simulation_time=2.0)

    assert result.simulation_time == 2.0
    assert result.execution.executed_decisions == (evaluation.decisions[0],)
    assert calls == ["trip"]
