import pytest

from core.application.services.temperature_instrument_service import TemperatureInstrumentService
from core.model.instrument_wiring import (
    CableAssembly, CableCore, InstrumentationWiringInventory, PanelWire,
    WiringConductorRole, WiringTerminalReference,
)
from core.model.temperature_instrument import (
    TemperatureInputMode, TemperatureInstrument, TemperatureInstrumentInventory,
    TemperatureInterfaceDevice, TemperatureSensorTechnology, TemperatureService,
    TemperatureTerminalMapping,
)


def terminal(equipment_id, role):
    return WiringTerminalReference(equipment_id, role, role)


def wiring_inventory(*carriers):
    cores = tuple(item for item in carriers if isinstance(item, CableCore))
    wires = tuple(item for item in carriers if isinstance(item, PanelWire))
    cables = tuple(
        CableAssembly(id=f"cable-{index}", tag=f"C-{index}", service="instrument", core_count=1)
        for index, _ in enumerate(cores, start=1)
    )
    # Each supplied core is normalized to the matching cable assembly.
    normalized = tuple(
        CableCore(
            id=core.id, cable_id=cables[index].id, core_number=1,
            role=core.role, terminal_path=core.terminal_path,
            conductor_material=core.conductor_material,
            thermocouple_type=core.thermocouple_type,
            thermocouple_polarity=core.thermocouple_polarity,
        )
        for index, core in enumerate(cores)
    )
    return InstrumentationWiringInventory(cables=cables, cores=normalized, panel_wires=wires)


def test_temperature_route_can_span_cable_core_and_panel_wire():
    sensor, jb, receiver = terminal("sensor", "A"), terminal("jb", "1"), terminal("plc", "AI+")
    inventory = wiring_inventory(
        CableCore("core-1", "temporary", 1, WiringConductorRole.SIGNAL, (sensor, jb)),
        PanelWire("wire-1", "W-1", WiringConductorRole.SIGNAL, (jb, receiver)),
    )
    assert TemperatureInstrumentService._has_physical_route(inventory, (sensor,), (receiver,))


def test_temperature_route_rejects_disconnected_carriers():
    sensor, jb, receiver = terminal("sensor", "A"), terminal("jb", "1"), terminal("plc", "AI+")
    inventory = wiring_inventory(
        CableCore("core-1", "temporary", 1, WiringConductorRole.SIGNAL, (sensor, jb)),
    )
    assert not TemperatureInstrumentService._has_physical_route(inventory, (sensor,), (receiver,))


def test_transmitter_temperature_loop_requires_both_physical_segments():
    sensor_a, sensor_b = terminal("rtd", "A"), terminal("rtd", "B")
    transmitter_input_a, transmitter_input_b = terminal("tx", "IN+"), terminal("tx", "IN-")
    transmitter_output = terminal("tx", "OUT")
    receiver = terminal("plc", "AI+")
    interface = TemperatureInterfaceDevice(
        id="tx", tag="TT-1", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 2-wire",),
        input_terminals=(transmitter_input_a, transmitter_input_b), output_terminals=(transmitter_output,),
        output_signal_kind="4-20mA", output_unit="degC",
    )
    instrument = TemperatureInstrument(
        id="temp-1", tag="OTD-1", service=TemperatureService.OTD,
        asset_id="transformer-1", location="main tank",
        sensor_equipment_id="rtd", sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.TRANSMITTER, interface_equipment_id="tx",
        sensor_configuration="Pt100 2-wire", sensor_terminals=(sensor_a, sensor_b),
        receiver_terminals=(receiver,),
        sensor_input_mappings=(
            TemperatureTerminalMapping(sensor_a, transmitter_input_a),
            TemperatureTerminalMapping(sensor_b, transmitter_input_b),
        ),
    )
    inventory = TemperatureInstrumentInventory(instruments=(instrument,), interfaces=(interface,))
    wiring = wiring_inventory(
        CableCore("sensor-core-a", "temporary", 1, WiringConductorRole.SIGNAL, (sensor_a, transmitter_input_a)),
        CableCore("sensor-core-b", "temporary", 1, WiringConductorRole.RETURN, (sensor_b, transmitter_input_b)),
        PanelWire("output-wire", "W-OUT", WiringConductorRole.SIGNAL, (transmitter_output, receiver)),
    )
    assert TemperatureInstrumentService._validate_physical_continuity(inventory, wiring) == ()


def test_transmitter_temperature_loop_rejects_missing_output_segment():
    sensor_a, sensor_b = terminal("rtd", "A"), terminal("rtd", "B")
    transmitter_input_a, transmitter_input_b = terminal("tx", "IN+"), terminal("tx", "IN-")
    transmitter_output = terminal("tx", "OUT")
    receiver = terminal("plc", "AI+")
    interface = TemperatureInterfaceDevice(
        id="tx", tag="TT-1", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 2-wire",),
        input_terminals=(transmitter_input_a, transmitter_input_b), output_terminals=(transmitter_output,),
        output_signal_kind="4-20mA", output_unit="degC",
    )
    instrument = TemperatureInstrument(
        id="temp-1", tag="OTD-1", service=TemperatureService.OTD,
        asset_id="transformer-1", location="main tank",
        sensor_equipment_id="rtd", sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.TRANSMITTER, interface_equipment_id="tx",
        sensor_configuration="Pt100 2-wire", sensor_terminals=(sensor_a, sensor_b),
        receiver_terminals=(receiver,),
        sensor_input_mappings=(
            TemperatureTerminalMapping(sensor_a, transmitter_input_a),
            TemperatureTerminalMapping(sensor_b, transmitter_input_b),
        ),
    )
    inventory = TemperatureInstrumentInventory(instruments=(instrument,), interfaces=(interface,))
    wiring = wiring_inventory(
        CableCore("sensor-core-a", "temporary", 1, WiringConductorRole.SIGNAL, (sensor_a, transmitter_input_a)),
        CableCore("sensor-core-b", "temporary", 1, WiringConductorRole.RETURN, (sensor_b, transmitter_input_b)),
    )
    with pytest.raises(ValueError, match="interface-output-to-receiver"):
        TemperatureInstrumentService._validate_physical_continuity(inventory, wiring)

def test_spare_core_cannot_prove_temperature_signal_continuity():
    sensor, receiver = terminal("sensor", "A"), terminal("plc", "AI+")
    inventory = wiring_inventory(
        CableCore("spare-core", "temporary", 1, WiringConductorRole.SPARE, (sensor, receiver)),
    )
    assert not TemperatureInstrumentService._has_physical_route(inventory, (sensor,), (receiver,))


def test_thermocouple_route_requires_matching_type_polarity_and_material():
    sensor_pos, tx_pos = terminal("tc", "POS"), terminal("tx", "IN+")
    sensor_neg, tx_neg = terminal("tc", "NEG"), terminal("tx", "IN-")
    positive = CableCore(
        "tc-pos", "temporary", 1, WiringConductorRole.SIGNAL,
        (sensor_pos, tx_pos), conductor_material="declared-alloy-a",
        thermocouple_type="K", thermocouple_polarity="POSITIVE",
    )
    negative = CableCore(
        "tc-neg", "temporary", 1, WiringConductorRole.RETURN,
        (sensor_neg, tx_neg), conductor_material="declared-alloy-b",
        thermocouple_type="K", thermocouple_polarity="NEGATIVE",
    )
    wiring = wiring_inventory(positive, negative)
    # The helper's cable assemblies must carry declared construction metadata.
    cables = tuple(
        CableAssembly(
            id=item.id, tag=item.tag, service=item.service, core_count=item.core_count,
            cable_type="declared-K-extension", conductor_material="declared-pair-construction",
        ) for item in wiring.cables
    )
    wiring = InstrumentationWiringInventory(cables=cables, cores=wiring.cores)
    assert TemperatureInstrumentService._has_physical_route(
        wiring, (sensor_pos,), (tx_pos,), thermocouple_type="K", polarity="POSITIVE"
    )
    assert not TemperatureInstrumentService._has_physical_route(
        wiring, (sensor_pos,), (tx_pos,), thermocouple_type="J", polarity="POSITIVE"
    )
    assert not TemperatureInstrumentService._has_physical_route(
        wiring, (sensor_pos,), (tx_pos,), thermocouple_type="K", polarity="NEGATIVE"
    )


def test_thermocouple_conductor_metadata_must_be_complete():
    with pytest.raises(ValueError, match="conductor_material"):
        CableCore(
            "tc-incomplete", "cable", 1, WiringConductorRole.SIGNAL,
            thermocouple_type="K",
        )


def test_mapped_thermocouple_loop_requires_type_polarity_and_construction_on_each_leg():
    sensor_pos, sensor_neg = terminal("tc", "POS"), terminal("tc", "NEG")
    tx_pos, tx_neg = terminal("tx", "IN+"), terminal("tx", "IN-")
    tx_out, receiver = terminal("tx", "OUT"), terminal("plc", "AI+")
    interface = TemperatureInterfaceDevice(
        id="tx", tag="TT-1", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.THERMOCOUPLE,),
        supported_sensor_configurations=("Type K",),
        input_terminals=(tx_pos, tx_neg), output_terminals=(tx_out,),
        output_signal_kind="4-20mA", output_unit="degC",
    )
    instrument = TemperatureInstrument(
        id="temp-tc", tag="OTD-TC-1", service=TemperatureService.OTD,
        asset_id="transformer-1", location="top oil", sensor_equipment_id="tc",
        sensor_technology=TemperatureSensorTechnology.THERMOCOUPLE,
        input_mode=TemperatureInputMode.TRANSMITTER, interface_equipment_id="tx",
        sensor_configuration="Type K", thermocouple_type="K",
        sensor_terminals=(sensor_pos, sensor_neg), receiver_terminals=(receiver,),
        sensor_input_mappings=(
            TemperatureTerminalMapping(sensor_pos, tx_pos, "POSITIVE"),
            TemperatureTerminalMapping(sensor_neg, tx_neg, "NEGATIVE"),
        ),
    )
    inventory = TemperatureInstrumentInventory(instruments=(instrument,), interfaces=(interface,))
    cables = (
        CableAssembly("cable-pos", "C-POS", "TC extension", 1, cable_type="K-extension", conductor_material="declared-pair"),
        CableAssembly("cable-neg", "C-NEG", "TC extension", 1, cable_type="K-extension", conductor_material="declared-pair"),
    )
    cores = (
        CableCore("core-pos", "cable-pos", 1, WiringConductorRole.SIGNAL, (sensor_pos, tx_pos),
                  conductor_material="declared-positive-alloy", thermocouple_type="K", thermocouple_polarity="POSITIVE"),
        CableCore("core-neg", "cable-neg", 1, WiringConductorRole.RETURN, (sensor_neg, tx_neg),
                  conductor_material="declared-negative-alloy", thermocouple_type="K", thermocouple_polarity="NEGATIVE"),
    )
    output = PanelWire("out-wire", "W-OUT", WiringConductorRole.SIGNAL, (tx_out, receiver))
    wiring = InstrumentationWiringInventory(cables=cables, cores=cores, panel_wires=(output,))
    assert TemperatureInstrumentService._validate_physical_continuity(inventory, wiring) == ()

    wrong_leg = CableCore(
        "core-neg", "cable-neg", 1, WiringConductorRole.RETURN, (sensor_neg, tx_neg),
        conductor_material="declared-negative-alloy", thermocouple_type="K", thermocouple_polarity="POSITIVE",
    )
    invalid = InstrumentationWiringInventory(cables=cables, cores=(cores[0], wrong_leg), panel_wires=(output,))
    with pytest.raises(ValueError, match="thermocouple negative conductor path"):
        TemperatureInstrumentService._validate_physical_continuity(inventory, invalid)
