from core.application.commands.pt_commands import (
    CREATE_PT, DELETE_PT, PUT_PT_IN_SERVICE, TAKE_PT_OUT_OF_SERVICE, UPDATE_PT,
    CreatePTCommand, UpdatePTCommand, DeletePTCommand, PutPTInServiceCommand, TakePTOutOfServiceCommand,
)
from core.application.endpoint_reference import EndpointReference
from core.application.command_handlers import ModelCommandHandlers


def test_pt_commands_use_endpoint_references_for_create_only():
    a = EndpointReference("bus", "B1")
    b = EndpointReference("bus", "B2")
    create = CreatePTCommand(pt_id="PT1", primary_a=a, primary_b=b)
    update = UpdatePTCommand(pt_id="PT1", burden_va=50.0)
    assert create.command_type == CREATE_PT
    assert create.payload["primary_a"] is a
    assert create.payload["primary_b"] is b
    assert "primary_a" not in update.payload


def test_pt_lifecycle_commands_and_handlers_are_registered():
    commands = (
        CreatePTCommand(pt_id="PT1"), UpdatePTCommand(pt_id="PT1", burden_va=50.0),
        DeletePTCommand(pt_id="PT1"), PutPTInServiceCommand(pt_id="PT1"), TakePTOutOfServiceCommand(pt_id="PT1"),
    )
    assert [command.command_type for command in commands] == [CREATE_PT, UPDATE_PT, DELETE_PT, PUT_PT_IN_SERVICE, TAKE_PT_OUT_OF_SERVICE]
    handlers = ModelCommandHandlers(object()).handlers()
    assert all(command_type in handlers for command_type in (CREATE_PT, UPDATE_PT, DELETE_PT, PUT_PT_IN_SERVICE, TAKE_PT_OUT_OF_SERVICE))
