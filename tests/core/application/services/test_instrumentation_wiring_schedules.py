from core.application.services.instrumentation_wiring_schedules import (
    build_cable_core_schedule,
    build_panel_wire_schedule,
    build_signal_loop_schedule,
)
from core.model.instrument_wiring import (
    CableAssembly,
    CableCore,
    CarrierKind,
    InstrumentationWiringInventory,
    PanelWire,
    PhysicalConnectionHop,
    SignalCarrierBinding,
    SignalDefinition,
    SignalKind,
    WiringConductorRole,
    WiringTerminalReference,
)


def _inventory():
    source = WiringTerminalReference("TX-1", "AI", "1+")
    junction = WiringTerminalReference("JB-1", "TB", "1")
    destination = WiringTerminalReference("PLC-1", "AI", "CH1+")
    cable = CableAssembly(id="cable-1", tag="CAB-001", service="4-20 mA", core_count=1)
    core = CableCore(
        id="core-1", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, terminal_path=(source, junction, destination),
        core_tag="CAB-001-1",
    )
    wire = PanelWire(
        id="wire-1", tag="W-001", role=WiringConductorRole.SIGNAL,
        terminal_path=(junction, destination),
    )
    signal = SignalDefinition(
        id="signal-1", tag="FIT-001.PV", description="Flow transmitter process value",
        kind=SignalKind.ANALOG, unit="mA",
    )
    hop1 = PhysicalConnectionHop(
        id="hop-1", from_terminal=source, to_terminal=junction,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
    )
    hop2 = PhysicalConnectionHop(
        id="hop-2", from_terminal=junction, to_terminal=destination,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
    )
    binding = SignalCarrierBinding(
        id="binding-1", signal_id=signal.id,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
        direction="SOURCE_TO_SINK",
    )
    return InstrumentationWiringInventory(
        cables=(cable,), cores=(core,), panel_wires=(wire,),
        signals=(signal,), signal_bindings=(binding,), connection_hops=(hop1, hop2),
    )


def test_cable_and_panel_wire_schedules_use_stable_hop_ids():
    inventory = _inventory()
    cable_rows = build_cable_core_schedule(inventory)
    wire_rows = build_panel_wire_schedule(inventory)
    assert [row.hop_id for row in cable_rows] == ["hop-1", "hop-2"]
    assert cable_rows[0].from_terminal.designation == "1+"
    assert [row.hop_id for row in wire_rows] == [None]
    assert wire_rows[0].lifecycle_status == "UNMAPPED_LEGACY"


def test_signal_loop_schedule_joins_signal_binding_and_physical_hops():
    rows = build_signal_loop_schedule(_inventory())
    assert len(rows) == 1
    row = rows[0]
    assert row.signal_tag == "FIT-001.PV"
    assert row.binding_id == "binding-1"
    assert row.carrier_id == "core-1"
    assert row.hop_ids == ("hop-1", "hop-2")
    assert row.physical_route_status == "MAPPED"


def test_legacy_route_is_visible_without_fabricating_hop_identity():
    inventory = _inventory()
    legacy = InstrumentationWiringInventory(
        cables=inventory.cables, cores=inventory.cores, panel_wires=inventory.panel_wires,
        signals=inventory.signals, signal_bindings=inventory.signal_bindings,
    )
    rows = build_cable_core_schedule(legacy)
    assert [row.hop_id for row in rows] == [None, None]
    assert all(row.lifecycle_status == "UNMAPPED_LEGACY" for row in rows)
    loop = build_signal_loop_schedule(legacy)[0]
    assert loop.hop_ids == ()
    assert loop.physical_route_status == "UNMAPPED_LEGACY"
