from core.application.command_handlers import ModelCommandHandlers
from core.application.commands.measurement_commands import (
    CREATE_CURRENT_TRANSFORMER,
    CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER,
    DELETE_CURRENT_TRANSFORMER,
    PUT_CURRENT_TRANSFORMER_IN_SERVICE,
    TAKE_CURRENT_TRANSFORMER_OUT_OF_SERVICE,
    DELETE_CAPACITIVE_VOLTAGE_TRANSFORMER,
    PUT_CAPACITIVE_VOLTAGE_TRANSFORMER_IN_SERVICE,
    TAKE_CAPACITIVE_VOLTAGE_TRANSFORMER_OUT_OF_SERVICE,
    CreateCurrentTransformerCommand,
    CreateCapacitiveVoltageTransformerCommand,
    DeleteCurrentTransformerCommand,
    PutCurrentTransformerInServiceCommand,
    TakeCurrentTransformerOutOfServiceCommand,
    DeleteCapacitiveVoltageTransformerCommand,
    PutCapacitiveVoltageTransformerInServiceCommand,
    TakeCapacitiveVoltageTransformerOutOfServiceCommand,
)
from core.application.transaction import Transaction


class FakeMeasurementService:
    def __init__(self):
        self.calls = []

    def create_current_transformer(self, **kwargs):
        self.calls.append(("create_ct", kwargs)); return "ct-created"

    def delete_current_transformer(self, **kwargs):
        self.calls.append(("delete_ct", kwargs)); return "ct-deleted"

    def put_current_transformer_in_service(self, **kwargs):
        self.calls.append(("put_ct", kwargs)); return "ct-in"

    def take_current_transformer_out_of_service(self, **kwargs):
        self.calls.append(("take_ct", kwargs)); return "ct-out"

    def create_capacitive_voltage_transformer(self, **kwargs):
        self.calls.append(("create_cvt", kwargs)); return "cvt-created"

    def delete_capacitive_voltage_transformer(self, **kwargs):
        self.calls.append(("delete_cvt", kwargs)); return "cvt-deleted"

    def put_capacitive_voltage_transformer_in_service(self, **kwargs):
        self.calls.append(("put_cvt", kwargs)); return "cvt-in"

    def take_capacitive_voltage_transformer_out_of_service(self, **kwargs):
        self.calls.append(("take_cvt", kwargs)); return "cvt-out"

    def update_current_transformer(self, **kwargs):
        self.calls.append(("update_ct", kwargs)); return "ct-updated"

    def update_capacitive_voltage_transformer(self, **kwargs):
        self.calls.append(("update_cvt", kwargs)); return "cvt-updated"


def test_measurement_commands_are_registered():
    measurement = FakeMeasurementService()
    model_service = type("ModelService", (), {"measurement_service": measurement})()
    handlers = ModelCommandHandlers(model_service).handlers()

    expected = {
        CREATE_CURRENT_TRANSFORMER, "model.update_current_transformer", DELETE_CURRENT_TRANSFORMER,
        PUT_CURRENT_TRANSFORMER_IN_SERVICE, TAKE_CURRENT_TRANSFORMER_OUT_OF_SERVICE,
        CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER, "model.update_capacitive_voltage_transformer",
        DELETE_CAPACITIVE_VOLTAGE_TRANSFORMER, PUT_CAPACITIVE_VOLTAGE_TRANSFORMER_IN_SERVICE,
        TAKE_CAPACITIVE_VOLTAGE_TRANSFORMER_OUT_OF_SERVICE,
    }
    assert expected.issubset(handlers)


def test_create_ct_handler_resolves_none_endpoints_and_delegates():
    measurement = FakeMeasurementService()
    model_service = type("ModelService", (), {"measurement_service": measurement})()
    command = CreateCurrentTransformerCommand(transformer_id="CT1")
    result = ModelCommandHandlers(model_service).create_current_transformer(command, object(), Transaction())

    assert result == "ct-created"
    assert measurement.calls[0][0] == "create_ct"
    assert measurement.calls[0][1]["ct_id"] == "CT1"
    assert measurement.calls[0][1]["p1_endpoint"] is None


def test_ct_and_cvt_lifecycle_handlers_delegate():
    measurement = FakeMeasurementService()
    model_service = type("ModelService", (), {"measurement_service": measurement})()
    handlers = ModelCommandHandlers(model_service)
    tx = Transaction()

    handlers.delete_current_transformer(DeleteCurrentTransformerCommand(transformer_id="CT1"), None, tx)
    handlers.put_current_transformer_in_service(PutCurrentTransformerInServiceCommand(transformer_id="CT1"), None, tx)
    handlers.take_current_transformer_out_of_service(TakeCurrentTransformerOutOfServiceCommand(transformer_id="CT1"), None, tx)
    handlers.delete_capacitive_voltage_transformer(DeleteCapacitiveVoltageTransformerCommand(transformer_id="CVT1"), None, tx)
    handlers.put_capacitive_voltage_transformer_in_service(PutCapacitiveVoltageTransformerInServiceCommand(transformer_id="CVT1"), None, tx)
    handlers.take_capacitive_voltage_transformer_out_of_service(TakeCapacitiveVoltageTransformerOutOfServiceCommand(transformer_id="CVT1"), None, tx)

    assert [name for name, _ in measurement.calls] == ["delete_ct", "put_ct", "take_ct", "delete_cvt", "put_cvt", "take_cvt"]
