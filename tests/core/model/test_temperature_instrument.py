from types import SimpleNamespace

import pytest

from core.application.services.temperature_instrument_service import TemperatureInstrumentService
from core.model import (
    TemperatureAlarmTripBinding, TemperatureConsumerKind, TemperatureInputMode,
    TemperatureInstrument, TemperatureInstrumentInventory, TemperatureInterfaceDevice,
    TemperatureSensorTechnology, TemperatureService, TemperatureReceiverInput,
    TemperatureReceiverInputKind, TemperatureThermocoupleCableClass,
    TemperatureThermocoupleCableSpec, WiringTerminalReference,
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

def test_thermocouple_mapping_requires_explicit_positive_and_negative_polarity():
    from core.model import TemperatureTerminalMapping

    sensor_positive = terminal("tc-2", "P")
    sensor_negative = terminal("tc-2", "N")
    input_positive = terminal("monitor-2", "TC+")
    input_negative = terminal("monitor-2", "TC-")
    interface = TemperatureInterfaceDevice(
        id="monitor-2", tag="TM-2", equipment_kind=TemperatureInputMode.TEMPERATURE_MONITOR,
        supported_sensor_technologies=(TemperatureSensorTechnology.THERMOCOUPLE,),
        supported_sensor_configurations=("Type K",),
        input_terminals=(input_positive, input_negative),
        output_terminals=(terminal("monitor-2", "OUT"),),
        output_signal_kind="DIGITAL", output_unit="degC",
    )
    instrument = TemperatureInstrument(
        id="temp-tc-2", tag="WTD-TC-2", service=TemperatureService.WTD,
        asset_id="transformer-1", location="winding", sensor_equipment_id="tc-2",
        sensor_technology=TemperatureSensorTechnology.THERMOCOUPLE,
        input_mode=TemperatureInputMode.TEMPERATURE_MONITOR, interface_equipment_id="monitor-2",
        sensor_configuration="Type K",
        sensor_terminals=(sensor_positive, sensor_negative),
        sensor_input_mappings=(
            TemperatureTerminalMapping(sensor_positive, input_positive, "POSITIVE"),
            TemperatureTerminalMapping(sensor_negative, input_negative, "NEGATIVE"),
        ),
    )
    assert TemperatureInstrumentInventory((instrument,), (interface,)).instruments

    invalid = TemperatureInstrument(
        id="temp-tc-3", tag="WTD-TC-3", service=TemperatureService.WTD,
        asset_id="transformer-1", location="winding", sensor_equipment_id="tc-3",
        sensor_technology=TemperatureSensorTechnology.THERMOCOUPLE,
        input_mode=TemperatureInputMode.TEMPERATURE_MONITOR, interface_equipment_id="monitor-2",
        sensor_configuration="Type K",
        sensor_terminals=(terminal("tc-3", "P"), terminal("tc-3", "N")),
        sensor_input_mappings=(
            TemperatureTerminalMapping(terminal("tc-3", "P"), input_positive, "POSITIVE"),
            TemperatureTerminalMapping(terminal("tc-3", "N"), input_negative, "POSITIVE"),
        ),
    )
    with pytest.raises(ValueError, match="positive and negative"):
        TemperatureInstrumentInventory((invalid,), (interface,))

def test_receiver_input_capability_is_explicit_and_round_trips():
    sensor = terminal("rtd-receiver", "A")
    sensor_b = terminal("rtd-receiver", "B")
    tx_in_a, tx_in_b = terminal("tx-receiver", "IN_A"), terminal("tx-receiver", "IN_B")
    tx_out = (terminal("tx-receiver", "OUT+"), terminal("tx-receiver", "OUT-"))
    receiver_terminals = (terminal("plc-ai-1", "CH1+"), terminal("plc-ai-1", "CH1-"))
    interface = TemperatureInterfaceDevice(
        id="tx-receiver", tag="TT-RECV-1", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 2-wire",),
        input_terminals=(tx_in_a, tx_in_b), output_terminals=tx_out,
        output_signal_kind="4-20mA", output_unit="degC",
        output_range_min=4.0, output_range_max=20.0, output_range_unit="mA",
    )
    receiver = TemperatureReceiverInput(
        id="plc-ai-1-ch1", module_equipment_id="plc-ai-1", channel_designation="AI-01",
        input_kind=TemperatureReceiverInputKind.ANALOG_CURRENT,
        terminals=receiver_terminals, engineering_unit="degC",
        range_min=4.0, range_max=20.0, range_unit="mA",
    )
    instrument = TemperatureInstrument(
        id="temp-receiver-1", tag="OTD-RECV-1", service=TemperatureService.OTD,
        asset_id="transformer-1", location="main tank", sensor_equipment_id="rtd-receiver",
        sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.TRANSMITTER, interface_equipment_id="tx-receiver",
        sensor_configuration="Pt100 2-wire", sensor_terminals=(sensor, sensor_b),
        receiver_terminals=receiver_terminals, receiver_input_id=receiver.id, unit="degC",
    )
    inventory = TemperatureInstrumentInventory((instrument,), (interface,), (receiver,))
    restored = deserialize_temperature_instruments(serialize_temperature_instruments(inventory))
    assert restored == inventory


def test_receiver_input_rejects_interface_signal_kind_mismatch():
    interface = TemperatureInterfaceDevice(
        id="tx-receiver-2", tag="TT-RECV-2", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 2-wire",),
        input_terminals=(terminal("tx-receiver-2", "IN_A"), terminal("tx-receiver-2", "IN_B")),
        output_terminals=(terminal("tx-receiver-2", "OUT+"), terminal("tx-receiver-2", "OUT-")),
        output_signal_kind="4-20mA", output_unit="degC", output_range_min=4.0, output_range_max=20.0,
    )
    receiver = TemperatureReceiverInput(
        id="plc-ai-2-ch1", module_equipment_id="plc-ai-2", channel_designation="AI-01",
        input_kind=TemperatureReceiverInputKind.ANALOG_VOLTAGE,
        terminals=(terminal("plc-ai-2", "CH1+"), terminal("plc-ai-2", "CH1-")),
        engineering_unit="degC", range_min=4.0, range_max=20.0, range_unit="mA",
    )
    instrument = TemperatureInstrument(
        id="temp-receiver-2", tag="OTD-RECV-2", service=TemperatureService.OTD,
        asset_id="transformer-2", location="oil", sensor_equipment_id="rtd-2",
        sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.TRANSMITTER, interface_equipment_id="tx-receiver-2",
        receiver_terminals=receiver.terminals, receiver_input_id=receiver.id, unit="degC",
    )
    with pytest.raises(ValueError, match="capability does not match"):
        TemperatureInstrumentInventory((instrument,), (interface,), (receiver,))


def test_receiver_input_requires_declared_physical_terminals_and_range_pair():
    with pytest.raises(ValueError, match="physical terminal references"):
        TemperatureReceiverInput(
            id="plc-ai-empty", module_equipment_id="plc-ai-empty", channel_designation="AI-01",
            input_kind=TemperatureReceiverInputKind.ANALOG_CURRENT, terminals=(),
            engineering_unit="degC",
        )
    with pytest.raises(ValueError, match="range bounds"):
        TemperatureReceiverInput(
            id="plc-ai-range", module_equipment_id="plc-ai-range", channel_designation="AI-01",
            input_kind=TemperatureReceiverInputKind.ANALOG_CURRENT,
            terminals=(terminal("plc-ai-range", "CH1+"),), engineering_unit="degC",
            range_min=4.0,
        )

def test_receiver_terminal_declaration_without_capability_record_fails_closed():
    with pytest.raises(ValueError, match="without a receiver input capability"):
        TemperatureInstrumentInventory(instruments=(TemperatureInstrument(
            id="temp-unbound-receiver", tag="BTD-UNBOUND", service=TemperatureService.BTD,
            asset_id="motor-1", location="DE bearing", sensor_equipment_id="rtd-unbound",
            sensor_technology=TemperatureSensorTechnology.RTD,
            input_mode=TemperatureInputMode.DIRECT_SENSOR,
            receiver_terminals=(terminal("plc-unconfigured", "AI1"),),
        ),))

def test_direct_rtd_receiver_requires_exact_technology_and_sensor_configuration():
    receiver = TemperatureReceiverInput(
        id="plc-rtd-1", module_equipment_id="plc-rtd", channel_designation="RTD-01",
        input_kind=TemperatureReceiverInputKind.RTD,
        terminals=(terminal("plc-rtd", "RTD1+"), terminal("plc-rtd", "RTD1-"), terminal("plc-rtd", "RTD1S")),
        engineering_unit="degC",
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 3-wire",),
    )
    instrument = TemperatureInstrument(
        id="temp-direct-rtd", tag="BTD-DIRECT-1", service=TemperatureService.BTD,
        asset_id="motor-1", location="DE bearing", sensor_equipment_id="rtd-direct",
        sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.DIRECT_SENSOR, sensor_configuration="Pt100 3-wire",
        sensor_terminals=(terminal("rtd-direct", "A"), terminal("rtd-direct", "B"), terminal("rtd-direct", "C")),
        receiver_terminals=receiver.terminals, receiver_input_id=receiver.id, unit="degC",
    )
    assert TemperatureInstrumentInventory((instrument,), receiver_inputs=(receiver,)).receiver_inputs

    invalid = TemperatureInstrument(
        id="temp-direct-rtd-invalid", tag="BTD-DIRECT-2", service=TemperatureService.BTD,
        asset_id="motor-1", location="NDE bearing", sensor_equipment_id="rtd-invalid",
        sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.DIRECT_SENSOR, sensor_configuration="Pt100 4-wire",
        sensor_terminals=tuple(terminal("rtd-invalid", role) for role in ("A", "B", "C", "D")),
        receiver_terminals=receiver.terminals, receiver_input_id=receiver.id, unit="degC",
    )
    with pytest.raises(ValueError, match="does not explicitly support"):
        TemperatureInstrumentInventory((invalid,), receiver_inputs=(receiver,))

def test_receiver_module_channel_designation_must_be_unique():
    first = TemperatureReceiverInput(
        id="plc-duplicate-a", module_equipment_id="plc-duplicate", channel_designation="AI-01",
        input_kind=TemperatureReceiverInputKind.ANALOG_CURRENT,
        terminals=(terminal("plc-duplicate", "AI1+"),), engineering_unit="degC",
    )
    second = TemperatureReceiverInput(
        id="plc-duplicate-b", module_equipment_id="plc-duplicate", channel_designation="AI-01",
        input_kind=TemperatureReceiverInputKind.ANALOG_CURRENT,
        terminals=(terminal("plc-duplicate", "AI1-"),), engineering_unit="degC",
    )
    with pytest.raises(ValueError, match="must be unique within each module"):
        TemperatureInstrumentInventory(receiver_inputs=(first, second))


def test_project_thermocouple_cable_catalogue_round_trips_without_embedded_defaults():
    spec = TemperatureThermocoupleCableSpec(
        id="project-kx", thermocouple_type="k", cable_designation="kx",
        cable_class=TemperatureThermocoupleCableClass.EXTENSION,
        positive_conductor_material="Nickel Chromium",
        negative_conductor_material="Nickel Aluminium",
        standard_reference="IEC 60584-3:2021", tolerance_class="1",
    )
    inventory = TemperatureInstrumentInventory(thermocouple_cable_specs=(spec,))
    restored = deserialize_temperature_instruments(serialize_temperature_instruments(inventory))
    assert restored == inventory
    assert restored.thermocouple_cable_specs[0].cable_designation == "KX"


def test_project_thermocouple_catalogue_rejects_duplicate_type_designation():
    first = TemperatureThermocoupleCableSpec(
        "spec-a", "K", "KX", TemperatureThermocoupleCableClass.EXTENSION,
        "NiCr", "NiAl", "IEC 60584-3:2021", "1",
    )
    second = TemperatureThermocoupleCableSpec(
        "spec-b", "K", "KX", TemperatureThermocoupleCableClass.EXTENSION,
        "NiCr-a", "NiAl-a", "IEC 60584-3:2021", "2",
    )
    with pytest.raises(ValueError, match="duplicate type/designation"):
        TemperatureInstrumentInventory(thermocouple_cable_specs=(first, second))
