from types import SimpleNamespace

import pytest

from core.application.services.temperature_instrument_service import TemperatureInstrumentService
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

def test_temperature_sensor_pin_mapping_is_explicit_and_round_trips():
    from core.model import TemperatureTerminalMapping

    sensor_a, sensor_b = terminal("rtd-2", "A"), terminal("rtd-2", "B")
    input_a, input_b = terminal("tx-1", "SENSOR_A"), terminal("tx-1", "SENSOR_B")
    interface = TemperatureInterfaceDevice(
        id="tx-1", tag="TT-002", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 2-wire",),
        input_terminals=(input_a, input_b),
        output_terminals=(terminal("tx-1", "+"), terminal("tx-1", "-")),
        output_signal_kind="4-20mA", output_unit="degC",
    )
    instrument = TemperatureInstrument(
        id="temp-map-1", tag="OTD-002", service=TemperatureService.OTD,
        asset_id="transformer-1", location="main tank",
        sensor_equipment_id="rtd-2", sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.TRANSMITTER, interface_equipment_id="tx-1",
        sensor_configuration="Pt100 2-wire", sensor_terminals=(sensor_a, sensor_b),
        sensor_input_mappings=(
            TemperatureTerminalMapping(sensor_a, input_a),
            TemperatureTerminalMapping(sensor_b, input_b),
        ),
    )
    inventory = TemperatureInstrumentInventory((instrument,), (interface,))
    restored = deserialize_temperature_instruments(serialize_temperature_instruments(inventory))
    assert restored == inventory


def test_temperature_sensor_pin_mapping_must_be_bijective():
    from core.model import TemperatureTerminalMapping

    sensor_a, sensor_b = terminal("rtd-3", "A"), terminal("rtd-3", "B")
    input_a, input_b = terminal("tx-3", "IN_A"), terminal("tx-3", "IN_B")
    interface = TemperatureInterfaceDevice(
        id="tx-3", tag="TT-003", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 2-wire",),
        input_terminals=(input_a, input_b), output_terminals=(terminal("tx-3", "OUT"),),
        output_signal_kind="4-20mA", output_unit="degC",
    )
    instrument = TemperatureInstrument(
        id="temp-map-3", tag="OTD-003", service=TemperatureService.OTD,
        asset_id="transformer-1", location="main tank",
        sensor_equipment_id="rtd-3", sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.TRANSMITTER, interface_equipment_id="tx-3",
        sensor_configuration="Pt100 2-wire", sensor_terminals=(sensor_a, sensor_b),
        sensor_input_mappings=(TemperatureTerminalMapping(sensor_a, input_a),),
    )
    inventory = TemperatureInstrumentInventory((instrument,), (interface,))
    service = TemperatureInstrumentService()
    service._inventory = inventory
    channel = SimpleNamespace(
        signal_type=SimpleNamespace(value="TEMPERATURE"),
        unit="degC",
        source_id="tx-3",
        source_terminal=SimpleNamespace(terminal_role="OUT"),
    )
    with pytest.raises(ValueError, match="cover every declared"):
        service.validate_measurement_channels({"temperature-channel": channel})

def test_rtd_declared_wire_configuration_must_match_terminal_count():
    with pytest.raises(ValueError, match="3-wire configuration"):
        TemperatureInstrument(
            id="temp-rtd-count", tag="BTD-003", service=TemperatureService.BTD,
            asset_id="motor-1", location="NDE bearing", sensor_equipment_id="rtd-3",
            sensor_technology=TemperatureSensorTechnology.RTD,
            input_mode=TemperatureInputMode.DIRECT_SENSOR,
            sensor_configuration="Pt100 3-wire",
            sensor_terminals=(terminal("rtd-3", "A"), terminal("rtd-3", "B")),
        )


def test_thermocouple_measurement_pair_excludes_screen_terminal():
    with pytest.raises(ValueError, match="exactly two measurement terminals"):
        TemperatureInstrument(
            id="temp-tc-pair", tag="BTD-004", service=TemperatureService.BTD,
            asset_id="motor-1", location="winding", sensor_equipment_id="tc-1",
            sensor_technology=TemperatureSensorTechnology.THERMOCOUPLE,
            input_mode=TemperatureInputMode.DIRECT_SENSOR,
            sensor_terminals=(
                terminal("tc-1", "+"), terminal("tc-1", "-"), terminal("tc-1", "SCREEN"),
            ),
        )
