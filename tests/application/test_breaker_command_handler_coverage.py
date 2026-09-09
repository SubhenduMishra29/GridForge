from core.application.command_handlers import ModelCommandHandlers
from core.application.commands.breaker_commands import (
    CREATE_BREAKER, UPDATE_BREAKER, DELETE_BREAKER,
    OPEN_BREAKER, CLOSE_BREAKER,
    PUT_BREAKER_IN_SERVICE, TAKE_BREAKER_OUT_OF_SERVICE,
)


def test_all_breaker_commands_have_registered_handlers():
    handlers = ModelCommandHandlers(object()).handlers()
    expected = {
        CREATE_BREAKER: "create_breaker",
        UPDATE_BREAKER: "update_breaker",
        DELETE_BREAKER: "delete_breaker",
        OPEN_BREAKER: "open_breaker",
        CLOSE_BREAKER: "close_breaker",
        PUT_BREAKER_IN_SERVICE: "put_breaker_in_service",
        TAKE_BREAKER_OUT_OF_SERVICE: "take_breaker_out_of_service",
    }

    for command_type, method_name in expected.items():
        assert command_type in handlers
        assert getattr(handlers[command_type], "__name__") == method_name
