from uuid import uuid4

from core.application.events import ApplicationEvent, AddControlComponent


def test_control_event_contract_is_exposed_by_application_events():
    from core.application import events
    names = {
        "ControlComponentCreated", "ControlComponentUpdated", "ControlComponentRemoved",
        "ControlConnectionCreated", "ControlConnectionRemoved", "ControlProgramChanged",
        "ControlStateChanged", "ControlExecutionStarted", "ControlExecutionCompleted",
        "ControlExecutionFailed",
    }
    for name in names:
        assert issubclass(getattr(events, name), ApplicationEvent)


def test_control_component_created_has_stable_semantic_event_type():
    from core.application.events import ControlComponentCreated
    event = ControlComponentCreated(component_id="c1", component_type="normally_open_contact")
    assert event.event_type == "control.component.created"
    assert event.payload["component_id"] == "c1"
    assert event.payload["component_type"] == "normally_open_contact"


def _application():
    from core.application.bootstrap import create_application
    from core.network.network import Network
    application = create_application(Network())
    application.new_project("Control Test")
    return application


def _add_command():
    from core.application.command import Command
    return Command(
        command_type="control.add_component",
        command_id=uuid4(),
        payload={"component_id": "c1", "component_type": "normally_open_contact", "rung_id": "r1"},
    )


def test_successful_control_command_publishes_control_event_after_commit():
    from core.application.application import Application
    from core.application.event_bus import ApplicationEventBus
    received = []
    application = _application()
    application.event_bus.subscribe(ApplicationEvent, received.append)
    result = application.execute(_add_command())
    assert result.success
    control_events = [e for e in received if e.event_type == "control.component.created"]
    assert len(control_events) == 1
    assert control_events[0].payload["component_id"] == "c1"


def test_failed_control_command_does_not_publish_control_event():
    from core.application.application import Application
    from core.application.event_bus import ApplicationEventBus
    received = []
    application = _application()
    application.event_bus.subscribe(ApplicationEvent, received.append)
    try:
        application.execute(AddControlComponent(component_id="c1", component_type="", rung_id="r1"))
    except Exception:
        pass
    else:
        raise AssertionError("invalid control command must be rejected")
    assert not result.success
    assert not [e for e in received if e.event_type == "control.component.created"]
