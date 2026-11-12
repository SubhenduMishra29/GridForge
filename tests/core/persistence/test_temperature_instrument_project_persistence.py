import pytest

from core.model import (
    TemperatureInputMode, TemperatureInstrument, TemperatureInstrumentInventory,
    TemperatureSensorTechnology, TemperatureService,
)
from core.persistence.project_persistence import ProjectPersistenceError, ProjectPersistenceService


def instrument(channel_id):
    return TemperatureInstrument(
        id="temp-1", tag="BTD-001", service=TemperatureService.BTD,
        asset_id="motor-1", location="DE bearing", sensor_equipment_id="rtd-1",
        sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.DIRECT_SENSOR,
        measurement_channel_id=channel_id,
    )


def test_temperature_instrument_channel_must_exist_in_project():
    inventory = TemperatureInstrumentInventory(instruments=(instrument("channel-1"),))
    ProjectPersistenceService._validate_temperature_instrument_channels(
        inventory, ({"channel_id": "channel-1"},)
    )


def test_missing_temperature_measurement_channel_fails_closed():
    inventory = TemperatureInstrumentInventory(instruments=(instrument("missing"),))
    with pytest.raises(ProjectPersistenceError, match="missing MeasurementChannel"):
        ProjectPersistenceService._validate_temperature_instrument_channels(
            inventory, ({"channel_id": "channel-1"},)
        )
