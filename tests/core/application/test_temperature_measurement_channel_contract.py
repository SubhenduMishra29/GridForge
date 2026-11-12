from types import SimpleNamespace

import pytest

from core.application.services.temperature_instrument_service import TemperatureInstrumentService
from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementPhase,
    MeasurementQuality,
    MeasurementSignalType,
)
from core.model.instrument_wiring import WiringTerminalReference
from core.model.temperature_instrument import (
    TemperatureInstrument,
    TemperatureInstrumentInventory,
    TemperatureSensorTechnology,
    TemperatureService,
    TemperatureInputMode,
)


def _instrument(*, unit="degC", channel_id="temp-channel"):
    return TemperatureInstrument(
        id="temp-1",
        tag="BTD-1",
        service=TemperatureService.BTD,
        asset_id="motor-1",
        location="drive-end bearing",
        sensor_equipment_id="rtd-1",
        sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.DIRECT_SENSOR,
        measurement_channel_id=channel_id,
        unit=unit,
        sensor_terminals=(WiringTerminalReference("rtd-1", "A", "A"),),
    )


def _channel(*, signal_type=MeasurementSignalType.TEMPERATURE, unit="degC", source_id="rtd-1", terminal_role="A"):
    return SimpleNamespace(
        signal_type=signal_type,
        unit=unit,
        source_id=source_id,
        source_terminal=SimpleNamespace(terminal_role=terminal_role),
    )


def test_temperature_measurement_signal_type_is_first_class():
    channel = MeasurementChannel(
        id="temperature-1",
        signal_type=MeasurementSignalType.TEMPERATURE,
        phase=MeasurementPhase.NONE,
        unit="degC",
        nominal_value=0.0,
        raw_value=24.5,
        quality=MeasurementQuality.GOOD,
    )
    assert channel.signal_type is MeasurementSignalType.TEMPERATURE
    assert channel.engineering_value == pytest.approx(24.5)


def test_temperature_instrument_requires_temperature_channel_with_matching_unit_and_source():
    service = TemperatureInstrumentService()
    service._inventory = TemperatureInstrumentInventory(instruments=(_instrument(),))
    service.validate_measurement_channels({"temp-channel": _channel()})


@pytest.mark.parametrize(
    "channel, message",
    [
        (_channel(signal_type=MeasurementSignalType.CURRENT), "TEMPERATURE"),
        (_channel(unit="K"), "unit"),
        (_channel(source_id="wrong-rtd"), "source"),
        (_channel(terminal_role="B"), "terminal"),
    ],
)
def test_temperature_instrument_rejects_incompatible_measurement_channel(channel, message):
    service = TemperatureInstrumentService()
    service._inventory = TemperatureInstrumentInventory(instruments=(_instrument(),))
    with pytest.raises(ValueError, match=message):
        service.validate_measurement_channels({"temp-channel": channel})


def test_measurement_channel_service_temperature_contract_requires_explicit_provenance_and_scaling():
    from core.application.services.measurement_channel_service import MeasurementChannelService

    service = MeasurementChannelService(clock_domain="plant-clock")
    channel = MeasurementChannel(
        id="temp-channel",
        signal_type=MeasurementSignalType.TEMPERATURE,
        phase=MeasurementPhase.NONE,
        unit="degC",
        nominal_value=0.0,
        scale=1.0,
        polarity=1.0,
        stale_after=5.0,
    )
    definition = {
        "producer_id": "temperature-acquisition-1",
        "timestamp_domain": "plant-clock",
        "scale": 1.0,
        "polarity": 1.0,
        "stale_after": 5.0,
    }
    service._validate_temperature_channel_definition(definition, channel)

    for missing in ("producer_id", "timestamp_domain", "scale", "polarity", "stale_after"):
        invalid = dict(definition)
        invalid.pop(missing)
        with pytest.raises((TypeError, ValueError)):
            service._validate_temperature_channel_definition(invalid, channel)
