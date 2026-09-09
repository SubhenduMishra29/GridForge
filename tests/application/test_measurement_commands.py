"""Regression tests for CT/CVT application command contracts."""

import pytest

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


def test_create_commands_keep_endpoint_references_and_domain_ids():
    endpoint = EndpointReference(element_type="bus", element_id="B1")
    ct = CreateCurrentTransformerCommand(transformer_id="CT1", p1_endpoint=endpoint)
    cvt = CreateCapacitiveVoltageTransformerCommand(transformer_id="CVT1", h1_endpoint=endpoint)

    assert ct.payload["transformer_id"] == "CT1"
    assert ct.payload["p1_endpoint"] == endpoint
    assert cvt.payload["transformer_id"] == "CVT1"
    assert cvt.payload["h1_endpoint"] == endpoint


def test_update_commands_match_measurement_service_mutable_fields():
    ct = UpdateCurrentTransformerCommand(
        transformer_id="CT1", primary_rated_current_a=200.0
    )
    cvt = UpdateCapacitiveVoltageTransformerCommand(
        transformer_id="CVT1", rated_primary_voltage_kv=245.0
    )

    assert ct.payload["transformer_id"] == "CT1"
    assert ct.payload["primary_rated_current_a"] == 200.0
    assert "p1_endpoint" not in ct.payload
    assert cvt.payload["transformer_id"] == "CVT1"
    assert cvt.payload["rated_primary_voltage_kv"] == 245.0
    assert "h1_endpoint" not in cvt.payload

    with pytest.raises(ValueError):
        UpdateCurrentTransformerCommand(transformer_id="CT1")
    with pytest.raises(ValueError):
        UpdateCapacitiveVoltageTransformerCommand(transformer_id="CVT1")


def test_measurement_lifecycle_commands_use_domain_specific_ids():
    commands = [
        DeleteCurrentTransformerCommand(transformer_id="CT1"),
        PutCurrentTransformerInServiceCommand(transformer_id="CT1"),
        TakeCurrentTransformerOutOfServiceCommand(transformer_id="CT1"),
        DeleteCapacitiveVoltageTransformerCommand(transformer_id="CVT1"),
        PutCapacitiveVoltageTransformerInServiceCommand(transformer_id="CVT1"),
        TakeCapacitiveVoltageTransformerOutOfServiceCommand(transformer_id="CVT1"),
    ]
    assert all(command.command_id is not None for command in commands)
    assert all("transformer_id" in command.payload for command in commands)
