from core.model import (
    TemperatureAlarmTripBinding, TemperatureConsumerKind, TemperatureInputMode,
    TemperatureInstrument, TemperatureInstrumentInventory, TemperatureInterfaceDevice,
    TemperatureSensorTechnology, TemperatureService, WiringTerminalReference,
)
from core.persistence.temperature_instrument_serializer import (
    deserialize_temperature_instruments, serialize_temperature_instruments,
)


def terminal(equipment_id: str, role: str) -> WiringTerminalReference:
    return WiringTerminalReference(equipment_id, role, role)


def test_btd_service_is_distinct_from_rtd_sensor_technology():
    item = TemperatureInstrument(
        id="temp-1", tag="BTD-001", service=TemperatureService.BTD,
        asset_id="motor-1", location="DE bearing", sensor_equipment_id="rtd-1",
        sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.DIRECT_SENSOR,
        sensor_configuration="3-wire",
        sensor_terminals=(terminal("rtd-1", "A"), terminal("rtd-1", "B1"), terminal("rtd-1", "B2")),
    )
    inventory = TemperatureInstrumentInventory(instruments=(item,))
    restored = deserialize_temperature_instruments(serialize_temperature_instruments(inventory))
    assert restored == inventory
    assert restored.instruments[0].service is TemperatureService.BTD
    assert restored.instruments[0].sensor_technology is TemperatureSensorTechnology.RTD


def test_otd_transmitter_requires_declared_sensor_and_output_contract():
    interface = TemperatureInterfaceDevice(
        id="tx-1", tag="TT-001", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 3-wire",),
        input_terminals=(terminal("tx-1", "SENSOR_A"), terminal("tx-1", "SENSOR_B1"), terminal("tx-1", "SENSOR_B2")),
        output_terminals=(terminal("tx-1", "+"), terminal("tx-1", "-")),
        output_signal_kind="4-20mA", output_unit="degC",
    )
    instrument = TemperatureInstrument(
        id="temp-2", tag="OTD-001", service=TemperatureService.OTD,
        asset_id="transformer-1", location="main tank oil",
        sensor_equipment_id="rtd-2", sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.TRANSMITTER, interface_equipment_id="tx-1",
        sensor_configuration="Pt100 3-wire",
    )
    assert TemperatureInstrumentInventory((instrument,), (interface,)).instruments


def test_interface_rejects_incompatible_sensor_configuration():
    interface = TemperatureInterfaceDevice(
        id="monitor-1", tag="TM-1", equipment_kind=TemperatureInputMode.TEMPERATURE_MONITOR,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 4-wire",),
        input_terminals=(terminal("monitor-1", "A1"), terminal("monitor-1", "A2")),
        output_terminals=(terminal("monitor-1", "OUT"),),
        output_signal_kind="DIGITAL", output_unit="degC",
    )
    instrument = TemperatureInstrument(
        id="temp-3", tag="WTD-001", service=TemperatureService.WTD,
        asset_id="transformer-1", location="phase-A winding",
        sensor_equipment_id="rtd-3", sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.TEMPERATURE_MONITOR, interface_equipment_id="monitor-1",
        sensor_configuration="Pt100 3-wire",
    )
    try:
        TemperatureInstrumentInventory((instrument,), (interface,))
    except ValueError as exc:
        assert "does not support" in str(exc)
    else:
        raise AssertionError("Incompatible RTD configuration must fail closed.")


def test_thermal_image_is_explicit_wtd_only():
    TemperatureInstrument(
        id="temp-4", tag="WTD-002", service=TemperatureService.WTD,
        asset_id="transformer-1", location="phase-B winding",
        sensor_equipment_id="thermal-image-1", sensor_technology=TemperatureSensorTechnology.OTHER,
        input_mode=TemperatureInputMode.THERMAL_IMAGE, interface_equipment_id="thermal-monitor-1",
    )


def test_alarm_trip_binding_requires_explicit_consumer_and_stage():
    binding = TemperatureAlarmTripBinding(
        id="alarm-1", instrument_id="temp-1", signal_id="sig-1",
        consumer_kind=TemperatureConsumerKind.TRIP, consumer_id="relay-1",
        function_id="thermal-trip", stage="HIGH_HIGH",
    )
    assert binding.threshold is None
    assert TemperatureInstrumentInventory(
        instruments=(TemperatureInstrument(
            id="temp-1", tag="BTD-001", service=TemperatureService.BTD,
            asset_id="motor-1", location="NDE bearing", sensor_equipment_id="rtd-1",
            sensor_technology=TemperatureSensorTechnology.RTD,
            input_mode=TemperatureInputMode.DIRECT_SENSOR,
        ),),
        alarm_trip_bindings=(binding,),
    )
