from core.application.events import ApplicationEvent


def test_control_event_contract_is_exposed_by_application_events():
    from core.application import events

    names = {
        "ControlComponentCreated", "ControlComponentUpdated", "ControlComponentRemoved",
        "ControlConnectionCreated", "ControlConnectionRemoved", "ControlProgramChanged",
        "ControlStateChanged", "ControlExecutionStarted", "ControlExecutionCompleted",
        "ControlExecutionFailed",
    }
    for name in names:
        event_type = getattr(events, name)
        assert issubclass(event_type, ApplicationEvent)


def test_control_component_created_has_stable_semantic_event_type():
    from core.application.events import ControlComponentCreated
    event = ControlComponentCreated(component_id="c1", component_type="normally_open_contact")
    assert event.event_type == "control.component.created"
    assert event.payload["component_id"] == "c1"
    assert event.payload["component_type"] == "normally_open_contact"


def _manager_for(handler):
    from core.application.command_manager import CommandManager
    from core.application.context import ApplicationContext
    return CommandManager(context=ApplicationContext(network=object()), handlers={"control.add_component": handler})


def _add_command():
    from core.application.command import Command
    return Command(command_type="control.add_component", payload={
        "component_id": "c1", "component_type": "normally_open_contact", "rung_id": "r1",
    })


def test_successful_control_command_publishes_control_event_after_commit():
    from core.application.application import Application
    from core.application.event_bus import ApplicationEventBus
    from core.application.results import ApplicationResult

    def handler(command, context, transaction):
        return ApplicationResult.success_result(
            message="created",
            metadata={"component_id": "c1", "component_type": "normally_open_contact"},
        )

    bus = ApplicationEventBus()
    received = []
    bus.subscribe(lambda event: received.append(event))
    application = Application(_manager_for(handler), event_bus=bus)

    result = application.execute(_add_command())
    assert result.success
    control_events = [e for e in received if e.event_type == "control.component.created"]
    assert len(control_events) == 1
    assert control_events[0].payload["component_id"] == "c1"


def test_failed_control_command_does_not_publish_control_event():
    from core.application.application import Application
    from core.application.event_bus import ApplicationEventBus
    from core.application.results import ApplicationResult

    def handler(command, context, transaction):
        return ApplicationResult(False, None, "rejected", {})

    bus = ApplicationEventBus()
    received = []
    bus.subscribe(lambda event: received.append(event))
    application = Application(_manager_for(handler), event_bus=bus)

    result = application.execute(_add_command())
    assert not result.success
    assert not [e for e in received if e.event_type == "control.component.created"]
