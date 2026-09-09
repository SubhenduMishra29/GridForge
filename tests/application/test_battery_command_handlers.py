from core.application.command_handlers import ModelCommandHandlers
from core.application.commands.battery_commands import (
    CREATE_BATTERY,
    UPDATE_BATTERY,
    DELETE_BATTERY,
    PUT_BATTERY_IN_SERVICE,
    TAKE_BATTERY_OUT_OF_SERVICE,
    CreateBatteryCommand,
    UpdateBatteryCommand,
    DeleteBatteryCommand,
    PutBatteryInServiceCommand,
    TakeBatteryOutOfServiceCommand,
)


def test_battery_commands_are_registered():
    handlers = ModelCommandHandlers(object()).handlers()
    assert handlers[CREATE_BATTERY] == handlers["model.create_battery"]
    assert UPDATE_BATTERY in handlers
    assert DELETE_BATTERY in handlers
    assert PUT_BATTERY_IN_SERVICE in handlers
    assert TAKE_BATTERY_OUT_OF_SERVICE in handlers


def test_battery_handlers_delegate_to_battery_service():
    class FakeBatteryService:
        def create_battery(self, **kwargs):
            return ("create", kwargs)

        def update_battery(self, **kwargs):
            return ("update", kwargs)

        def delete_battery(self, **kwargs):
            return ("delete", kwargs)

        def put_battery_in_service(self, **kwargs):
            return ("in_service", kwargs)

        def take_battery_out_of_service(self, **kwargs):
            return ("out_of_service", kwargs)

    class FakeModelService:
        battery_service = FakeBatteryService()

    model_handlers = ModelCommandHandlers(FakeModelService())
    transaction = object()

    create = CreateBatteryCommand(battery_id="b1")
    update = UpdateBatteryCommand(battery_id="b1", p_mw=5.0)
    delete = DeleteBatteryCommand(battery_id="b1")
    put_in_service = PutBatteryInServiceCommand(battery_id="b1")
    take_out = TakeBatteryOutOfServiceCommand(battery_id="b1")

    assert model_handlers.create_battery(create, object(), transaction) == (
        "create", {"battery_id": "b1", "transaction": transaction}
    )
    assert model_handlers.update_battery(update, object(), transaction) == (
        "update", {"battery_id": "b1", "p_mw": 5.0, "transaction": transaction}
    )
    assert model_handlers.delete_battery(delete, object(), transaction) == (
        "delete", {"battery_id": "b1", "transaction": transaction}
    )
    assert model_handlers.put_battery_in_service(put_in_service, object(), transaction) == (
        "in_service", {"battery_id": "b1", "transaction": transaction}
    )
    assert model_handlers.take_battery_out_of_service(take_out, object(), transaction) == (
        "out_of_service", {"battery_id": "b1", "transaction": transaction}
    )
