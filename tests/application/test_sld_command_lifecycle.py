from __future__ import annotations

import pytest

from core.application.application import Application
from core.application.command_manager import CommandManager
from core.application.commands.sld_commands import AddSLDNodeCommand, SetSLDNodePositionCommand
from core.application.events import SLDPresentationChanged
from core.application.errors import ExecutionError
from core.application.services.sld_service import SLDService
from ui.sld.sld_document import SLDDocument


def _application() -> tuple[Application, SLDDocument]:
    document = SLDDocument("project-a:sld", project_id="project-a")
    service = SLDService(document)
    application = Application(CommandManager(context=object()), sld_service=service)
    return application, document


def test_sld_command_uses_application_history_and_undo_redo() -> None:
    application, document = _application()

    result = application.execute(AddSLDNodeCommand(node_id="bus-1", equipment_id="bus-1", x=10, y=20))

    assert result.success
    assert document.model.get_node("bus-1").position == (10.0, 20.0)
    assert application.undo_count() == 1

    application.undo()
    assert not document.model.has_node("bus-1")
    assert application.redo_count() == 1

    application.redo()
    assert document.model.get_node("bus-1").position == (10.0, 20.0)
    assert application.undo_count() == 1


def test_failed_sld_command_does_not_create_history_or_change_state() -> None:
    application, document = _application()

    with pytest.raises(ExecutionError):
        application.execute(SetSLDNodePositionCommand(node_id="missing", x=1, y=2))

    assert document.model.node_count == 0
    assert application.undo_count() == 0
    assert application.redo_count() == 0


def test_successful_sld_mutation_publishes_semantic_presentation_event() -> None:
    application, _ = _application()
    events: list[SLDPresentationChanged] = []
    application.event_bus.subscribe(SLDPresentationChanged, events.append)

    application.execute(AddSLDNodeCommand(node_id="bus-1", x=10, y=20))

    assert len(events) == 1
    assert events[0].event_type == "sld.presentation.changed"
    assert events[0].payload["operation"] == "execute"
    assert events[0].payload["presentation_operation"] == "add_node"


def test_undo_and_redo_publish_presentation_events() -> None:
    application, _ = _application()
    events: list[SLDPresentationChanged] = []
    application.event_bus.subscribe(SLDPresentationChanged, events.append)

    application.execute(AddSLDNodeCommand(node_id="bus-1", x=10, y=20))
    application.undo()
    application.redo()

    assert [event.payload["operation"] for event in events] == ["execute", "undo", "redo"]
