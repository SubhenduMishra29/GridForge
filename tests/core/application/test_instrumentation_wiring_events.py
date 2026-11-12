from types import SimpleNamespace
from uuid import uuid4

import pytest

from core.application.application import Application
from core.application.event_bus import ApplicationEventBus
from core.application.events import InstrumentationWiringChanged
from core.model.instrument_wiring import (
    CableAssembly,
    InstrumentationWiringInventory,
)


def _application_with_event_bus():
    application = Application.__new__(Application)
    application._event_bus = ApplicationEventBus()
    application._project_scope_metadata = lambda: {
        "project_id": "project-1",
        "activation_generation": 4,
    }
    return application


def _command(expected, replacement):
    return SimpleNamespace(
        command_type="instrumentation_wiring.set_inventory",
        command_id=uuid4(),
        correlation_id=None,
        causation_id=None,
        payload={
            "expected_inventory": expected,
            "replacement_inventory": replacement,
        },
    )


def test_inventory_command_publishes_semantic_event_for_execute_undo_and_redo():
    cable = CableAssembly(
        id="cable-1", tag="CAB-001", service="instrument", core_count=1,
    )
    empty = InstrumentationWiringInventory()
    populated = InstrumentationWiringInventory(cables=(cable,))
    application = _application_with_event_bus()
    received = []
    application._event_bus.subscribe(InstrumentationWiringChanged, received.append)
    result = SimpleNamespace(
        metadata={"project_id": "project-1", "activation_generation": 4},
        message="Instrumentation wiring inventory updated.",
    )

    for operation in ("execute", "undo", "redo"):
        application._publish_semantic_events(
            _command(empty, populated), result, operation=operation,
        )

    assert [event.payload["operation"] for event in received] == [
        "execute", "undo", "redo",
    ]
    assert all(event.payload["project_id"] == "project-1" for event in received)
    assert all(event.payload["activation_generation"] == 4 for event in received)
    assert all(event.payload["changed_collections"] == ("cables",) for event in received)
    assert all(event.event_type == "instrumentation.wiring.changed" for event in received)


def test_instrumentation_wiring_event_rejects_unknown_collection_names():
    with pytest.raises(ValueError, match="canonical inventory collection"):
        InstrumentationWiringChanged(
            operation="execute",
            project_id="project-1",
            activation_generation=1,
            changed_collections=("unknown",),
        )


def test_instrumentation_wiring_event_rejects_boolean_activation_generation():
    with pytest.raises(ValueError, match="positive integer"):
        InstrumentationWiringChanged(
            operation="execute",
            project_id="project-1",
            activation_generation=True,
            changed_collections=("cables",),
        )
