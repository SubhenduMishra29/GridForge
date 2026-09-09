from core.application.command_handlers import ModelCommandHandlers
from core.application.commands.model_commands import (
    CREATE_GENERATOR, UPDATE_GENERATOR, DELETE_GENERATOR,
    CREATE_SHUNT, UPDATE_SHUNT, DELETE_SHUNT,
    CREATE_CABLE, UPDATE_CABLE, DELETE_CABLE,
    CREATE_SWITCH, UPDATE_SWITCH, DELETE_SWITCH,
    OPEN_SWITCH, CLOSE_SWITCH, PUT_SWITCH_IN_SERVICE, TAKE_SWITCH_OUT_OF_SERVICE,
    CREATE_DISCONNECTOR, UPDATE_DISCONNECTOR, DELETE_DISCONNECTOR,
    OPEN_DISCONNECTOR, CLOSE_DISCONNECTOR,
    PUT_DISCONNECTOR_IN_SERVICE, TAKE_DISCONNECTOR_OUT_OF_SERVICE,
    CREATE_FUSE, UPDATE_FUSE, DELETE_FUSE,
    BLOW_FUSE, RESET_FUSE, PUT_FUSE_IN_SERVICE, TAKE_FUSE_OUT_OF_SERVICE,
)


MISSING_PIPELINE_COMMANDS = {
    CREATE_GENERATOR: "create_generator", UPDATE_GENERATOR: "update_generator", DELETE_GENERATOR: "delete_generator",
    CREATE_SHUNT: "create_shunt", UPDATE_SHUNT: "update_shunt", DELETE_SHUNT: "delete_shunt",
    CREATE_CABLE: "create_cable", UPDATE_CABLE: "update_cable", DELETE_CABLE: "delete_cable",
    CREATE_SWITCH: "create_switch", UPDATE_SWITCH: "update_switch", DELETE_SWITCH: "delete_switch",
    OPEN_SWITCH: "open_switch", CLOSE_SWITCH: "close_switch", PUT_SWITCH_IN_SERVICE: "put_switch_in_service",
    TAKE_SWITCH_OUT_OF_SERVICE: "take_switch_out_of_service", CREATE_DISCONNECTOR: "create_disconnector",
    UPDATE_DISCONNECTOR: "update_disconnector", DELETE_DISCONNECTOR: "delete_disconnector", OPEN_DISCONNECTOR: "open_disconnector",
    CLOSE_DISCONNECTOR: "close_disconnector", PUT_DISCONNECTOR_IN_SERVICE: "put_disconnector_in_service",
    TAKE_DISCONNECTOR_OUT_OF_SERVICE: "take_disconnector_out_of_service", CREATE_FUSE: "create_fuse",
    UPDATE_FUSE: "update_fuse", DELETE_FUSE: "delete_fuse", BLOW_FUSE: "blow_fuse", RESET_FUSE: "reset_fuse",
    PUT_FUSE_IN_SERVICE: "put_fuse_in_service", TAKE_FUSE_OUT_OF_SERVICE: "take_fuse_out_of_service",
}


def test_all_missing_model_commands_have_registered_handlers():
    handlers = ModelCommandHandlers(object()).handlers()

    for command_type, method_name in MISSING_PIPELINE_COMMANDS.items():
        assert command_type in handlers
        assert getattr(handlers[command_type], "__name__") == method_name
