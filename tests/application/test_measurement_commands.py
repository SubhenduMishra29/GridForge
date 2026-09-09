"""Regression tests for CT/CVT application command contracts."""

from core.application.commands.measurement_commands import (
    CreateCapacitiveVoltageTransformerCommand,
    CreateCurrentTransformerCommand,
    DeleteCapacitiveVoltageTransformerCommand,
    DeleteCurrentTransformerCommand,
    PutCapacitiveVoltageTransformerInServiceCommand,
    PutCurrentTransformerInServiceCommand,
    TakeCapacitiveVoltageTransformerOutOfServiceCommand,
    TakeCurrentTransformerOutOfServiceCommand,
    UpdateCapacitiveVoltageTransformerCommand,
    UpdateCurrentTransformerCommand,
)
from core.application.endpoint_reference import EndpointReference


def test_measurement_commands_keep_endpoints_as_references():
    endpoint = EndpointReference(element_type="bus", element_id="B1")
    command = CreateCurrentTransformerCommand(
        transformer_id="CT1", endpoint=endpoint
    )
    assert command.payload["endpoint"] == endpoint


def test_measurement_lifecycle_commands_are_immutable_intents():
    commands = [
        DeleteCurrentTransformerCommand(transformer_id="CT1"),
        PutCurrentTransformerInServiceCommand(transformer_id="CT1"),
        TakeCurrentTransformerOutOfServiceCommand(transformer_id="CT1"),
        DeleteCapacitiveVoltageTransformerCommand(transformer_id="CVT1"),
        PutCapacitiveVoltageTransformerInServiceCommand(transformer_id="CVT1"),
        TakeCapacitiveVoltageTransformerOutOfServiceCommand(transformer_id="CVT1"),
    ]
    assert all(command.command_id is not None for command in commands)


def test_update_commands_require_a_mutable_field():
    try:
        UpdateCurrentTransformerCommand(transformer_id="CT1")
    except ValueError:
        pass
    else:
        raise AssertionError("CT update command must require a mutable field")

    try:
        UpdateCapacitiveVoltageTransformerCommand(transformer_id="CVT1")
    except ValueError:
        pass
    else:
        raise AssertionError("CVT update command must require a mutable field")
