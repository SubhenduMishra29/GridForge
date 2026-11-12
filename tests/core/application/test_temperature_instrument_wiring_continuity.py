import pytest

from core.application.services.temperature_instrument_service import TemperatureInstrumentService
from core.model.instrument_wiring import (
    CableAssembly, CableCore, InstrumentationWiringInventory, PanelWire,
    WiringConductorRole, WiringTerminalReference,
)
from core.model.temperature_instrument import (
    TemperatureInputMode, TemperatureInstrument, TemperatureInstrumentInventory,
    TemperatureInterfaceDevice, TemperatureSensorTechnology, TemperatureService,
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
    sensor = terminal("rtd", "A")
    transmitter_input = terminal("tx", "IN")
    transmitter_output = terminal("tx", "OUT")
    receiver = terminal("plc", "AI+")
    interface = TemperatureInterfaceDevice(
        id="tx", tag="TT-1", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 2-wire",),
        input_terminals=(transmitter_input,), output_terminals=(transmitter_output,),
        output_signal_kind="4-20mA", output_unit="degC",
    )
    instrument = TemperatureInstrument(
        id="temp-1", tag="OTD-1", service=TemperatureService.OTD,
        asset_id="transformer-1", location="main tank",
        sensor_equipment_id="rtd", sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.TRANSMITTER, interface_equipment_id="tx",
        sensor_configuration="Pt100 2-wire", sensor_terminals=(sensor,),
        receiver_terminals=(receiver,),
    )
    inventory = TemperatureInstrumentInventory(instruments=(instrument,), interfaces=(interface,))
    wiring = wiring_inventory(
        CableCore("sensor-core", "temporary", 1, WiringConductorRole.SIGNAL, (sensor, transmitter_input)),
        PanelWire("output-wire", "W-OUT", WiringConductorRole.SIGNAL, (transmitter_output, receiver)),
    )
    assert TemperatureInstrumentService._validate_physical_continuity(inventory, wiring) == ()


def test_transmitter_temperature_loop_rejects_missing_output_segment():
    sensor = terminal("rtd", "A")
    transmitter_input = terminal("tx", "IN")
    transmitter_output = terminal("tx", "OUT")
    receiver = terminal("plc", "AI+")
    interface = TemperatureInterfaceDevice(
        id="tx", tag="TT-1", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 2-wire",),
        input_terminals=(transmitter_input,), output_terminals=(transmitter_output,),
        output_signal_kind="4-20mA", output_unit="degC",
    )
    instrument = TemperatureInstrument(
        id="temp-1", tag="OTD-1", service=TemperatureService.OTD,
        asset_id="transformer-1", location="main tank",
        sensor_equipment_id="rtd", sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.TRANSMITTER, interface_equipment_id="tx",
        sensor_configuration="Pt100 2-wire", sensor_terminals=(sensor,),
        receiver_terminals=(receiver,),
    )
    inventory = TemperatureInstrumentInventory(instruments=(instrument,), interfaces=(interface,))
    wiring = wiring_inventory(
        CableCore("sensor-core", "temporary", 1, WiringConductorRole.SIGNAL, (sensor, transmitter_input)),
    )
    with pytest.raises(ValueError, match="interface-output-to-receiver"):
        TemperatureInstrumentService._validate_physical_continuity(inventory, wiring)
