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
from core.application.commands.endpoint_reference import EndpointReference


def test_battery_create_command_preserves_application_payload():
    endpoint = EndpointReference("bus", "b1")
    command = CreateBatteryCommand(
        battery_id="bat1", name="Battery 1", endpoint=endpoint,
        p_mw=2.0, q_mvar=0.5, max_charge_mw=3.0,
        max_discharge_mw=4.0, energy_capacity_mwh=10.0,
        soc=0.7, soc_min=0.1, soc_max=0.9, in_service=True,
    )
    assert command.command_type == CREATE_BATTERY
    assert command.payload["battery_id"] == "bat1"
    assert command.payload["endpoint"] == endpoint
    assert command.payload["energy_capacity_mwh"] == 10.0


def test_battery_update_requires_mutable_field_and_excludes_endpoint():
    command = UpdateBatteryCommand(battery_id="bat1", p_mw=2.0, soc=0.8)
    assert command.command_type == UPDATE_BATTERY
    assert command.payload["p_mw"] == 2.0
    assert "endpoint" not in command.payload

    try:
        UpdateBatteryCommand(battery_id="bat1")
    except ValueError:
        pass
    else:
        raise AssertionError("UpdateBatteryCommand must reject an empty update")


def test_battery_delete_and_lifecycle_commands_keep_ids():
    assert DeleteBatteryCommand(battery_id="bat1").command_type == DELETE_BATTERY
    assert PutBatteryInServiceCommand(battery_id="bat1").command_type == PUT_BATTERY_IN_SERVICE
    assert TakeBatteryOutOfServiceCommand(battery_id="bat1").command_type == TAKE_BATTERY_OUT_OF_SERVICE
