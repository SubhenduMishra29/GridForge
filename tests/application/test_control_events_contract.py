from core.application.events import ApplicationEvent


def test_control_event_contract_is_exposed_by_application_events():
    from core.application import events

    names = {
        "ControlComponentCreated",
        "ControlComponentUpdated",
        "ControlComponentRemoved",
        "ControlConnectionCreated",
        "ControlConnectionRemoved",
        "ControlProgramChanged",
        "ControlStateChanged",
        "ControlExecutionStarted",
        "ControlExecutionCompleted",
        "ControlExecutionFailed",
    }

    for name in names:
        event_type = getattr(events, name)
        assert issubclass(event_type, ApplicationEvent)


def test_control_component_created_has_stable_semantic_event_type():
    from core.application.events import ControlComponentCreated

    event = ControlComponentCreated(
        component_id="c1",
        component_type="normally_open_contact",
    )

    assert event.event_type == "control.component.created"
    assert event.payload["component_id"] == "c1"
    assert event.payload["component_type"] == "normally_open_contact"
