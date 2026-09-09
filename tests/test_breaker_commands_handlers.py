"""Regression tests for Breaker Application command/handler coverage."""

import inspect

from core.application.commands.breaker_commands import (
    CLOSE_BREAKER,
    CREATE_BREAKER,
    DELETE_BREAKER,
    OPEN_BREAKER,
    PUT_BREAKER_IN_SERVICE,
    TAKE_BREAKER_OUT_OF_SERVICE,
    UPDATE_BREAKER,
    CloseBreakerCommand,
    CreateBreakerCommand,
    DeleteBreakerCommand,
    OpenBreakerCommand,
    PutBreakerInServiceCommand,
    TakeBreakerOutOfServiceCommand,
    UpdateBreakerCommand,
)
from core.application.commands import (
    CloseBreakerCommand as ExportedCloseBreakerCommand,
    CreateBreakerCommand as ExportedCreateBreakerCommand,
    DeleteBreakerCommand as ExportedDeleteBreakerCommand,
    OpenBreakerCommand as ExportedOpenBreakerCommand,
    PutBreakerInServiceCommand as ExportedPutBreakerInServiceCommand,
    TakeBreakerOutOfServiceCommand as ExportedTakeBreakerOutOfServiceCommand,
    UpdateBreakerCommand as ExportedUpdateBreakerCommand,
)
from core.application.command_handlers import ModelCommandHandlers


def test_breaker_commands_have_canonical_types_and_payloads() -> None:
    create = CreateBreakerCommand(
        breaker_id="BRK-1",
        name="Breaker 1",
        closed=True,
        in_service=True,
        voltage_kv=11.0,
        current_a=630.0,
        interrupting_ka=25.0,
    )
    update = UpdateBreakerCommand(breaker_id="BRK-1", closed=False)

    assert create.command_type == CREATE_BREAKER
    assert create.payload["breaker_id"] == "BRK-1"
    assert update.command_type == UPDATE_BREAKER
    assert update.payload["closed"] is False


def test_breaker_operational_commands_are_identifier_only() -> None:
    commands = (
        OpenBreakerCommand(breaker_id="BRK-1"),
        CloseBreakerCommand(breaker_id="BRK-1"),
        PutBreakerInServiceCommand(breaker_id="BRK-1"),
        TakeBreakerOutOfServiceCommand(breaker_id="BRK-1"),
    )
    assert [command.command_type for command in commands] == [
        OPEN_BREAKER,
        CLOSE_BREAKER,
        PUT_BREAKER_IN_SERVICE,
        TAKE_BREAKER_OUT_OF_SERVICE,
    ]
    assert all(set(command.payload) == {"breaker_id"} for command in commands)


def test_breaker_commands_are_publicly_exported() -> None:
    assert ExportedCreateBreakerCommand is CreateBreakerCommand
    assert ExportedUpdateBreakerCommand is UpdateBreakerCommand
    assert ExportedDeleteBreakerCommand is DeleteBreakerCommand
    assert ExportedOpenBreakerCommand is OpenBreakerCommand
    assert ExportedCloseBreakerCommand is CloseBreakerCommand
    assert ExportedPutBreakerInServiceCommand is PutBreakerInServiceCommand
    assert ExportedTakeBreakerOutOfServiceCommand is TakeBreakerOutOfServiceCommand


def test_model_command_handlers_register_all_breaker_commands() -> None:
    handlers = ModelCommandHandlers(object()).handlers()
    assert {
        CREATE_BREAKER,
        UPDATE_BREAKER,
        DELETE_BREAKER,
        OPEN_BREAKER,
        CLOSE_BREAKER,
        PUT_BREAKER_IN_SERVICE,
        TAKE_BREAKER_OUT_OF_SERVICE,
    }.issubset(handlers)


def test_breaker_handlers_delegate_to_switching_service() -> None:
    source = inspect.getsource(ModelCommandHandlers)
    assert "switching_service" in source
    assert "create_breaker" in source
    assert "update_breaker" in source
    assert "delete_breaker" in source
    assert "open_breaker" in source
    assert "close_breaker" in source
    assert "put_breaker_in_service" in source
    assert "take_breaker_out_of_service" in source


def test_breaker_create_handler_uses_canonical_endpoint_resolver() -> None:
    source = inspect.getsource(ModelCommandHandlers.create_breaker)
    assert "EndpointResolver.resolve" in source
    assert "endpoint_from" in source
    assert "endpoint_to" in source
