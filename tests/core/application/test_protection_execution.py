from core.application.command_manager import CommandManager
from core.application.context import ApplicationContext
from core.application.control_dispatch import ControlCommandDispatcher
from core.application.protection_execution import ProtectionExecutionService
from core.application.results import ApplicationResult
from core.control.decision import ControlDecision
from core.protection.decision import ProtectionDecision


def _decision(*, trip: bool) -> ProtectionDecision:
    return ProtectionDecision(
        relay_id="R1", element_id="OC50", function_code="50",
        pickup=trip, operate=trip, trip_request=trip, valid=True,
    )


def _service(executor):
    manager = CommandManager(context=ApplicationContext(network=object()), handlers={})
    dispatcher = ControlCommandDispatcher(manager, command_executor=executor)
    return ProtectionExecutionService(
        dispatcher,
        action_resolver=lambda decision: ControlDecision.trip(
            control_id="CTRL-1",
            target_equipment_id="BRK-1",
            reason="Protection trip",
            simulation_time=1.0,
            triggered_by=decision.element_id,
        ),
    )


def test_actionable_decision_is_translated_to_existing_trip_command():
    calls = []
    service = _service(lambda command: calls.append(command) or ApplicationResult.success_result(message="tripped"))
    result = service.execute([_decision(trip=True)])
    assert len(result.commands) == 1
    assert result.commands[0].payload["breaker_id"] == "BRK-1"
    assert len(calls) == 1
    assert calls[0].command_type == result.commands[0].command_type
    assert calls[0].payload == result.commands[0].payload


def test_non_actionable_decision_never_creates_application_command():
    calls = []
    service = _service(lambda command: calls.append(command) or ApplicationResult.success_result())
    result = service.execute([_decision(trip=False)])
    assert result.commands == ()
    assert calls == []


def test_missing_action_target_is_reported_without_application_bypass():
    manager = CommandManager(context=ApplicationContext(network=object()), handlers={})
    dispatcher = ControlCommandDispatcher(manager, command_executor=lambda command: ApplicationResult.success_result())
    service = ProtectionExecutionService(dispatcher, action_resolver=lambda _: None)
    result = service.execute([_decision(trip=True)])
    assert result.commands == ()
    assert "no configured action target" in result.diagnostics[0]


def test_trip_execution_failure_is_reported_without_bypassing_application():
    service = _service(lambda command: (_ for _ in ()).throw(RuntimeError("command failure")))
    result = service.execute([_decision(trip=True)])
    assert result.commands == ()
    assert "execution failed" in result.diagnostics[0]


def test_decision_input_is_strictly_typed():
    service = _service(lambda command: ApplicationResult.success_result())
    try:
        service.execute([object()])
    except TypeError as exc:
        assert "ProtectionDecision" in str(exc)
    else:
        raise AssertionError("ProtectionExecutionService must reject non-ProtectionDecision inputs")
