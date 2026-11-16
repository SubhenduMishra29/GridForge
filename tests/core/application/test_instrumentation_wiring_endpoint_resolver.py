from types import SimpleNamespace

from core.application.control_signal_mapping import (
    ControlSignalBinding,
    ControlSignalDestination,
    ControlSignalMapping,
    ControlSignalSource,
)
from core.application.instrumentation_wiring_endpoint_resolver import (
    resolve_signal_endpoint_bindings,
)
from core.model.instrument_wiring import (
    CableAssembly,
    CableCore,
    CarrierKind,
    InstrumentationWiringInventory,
    SignalCarrierBinding,
    SignalDefinition,
    SignalEndpointBinding,
    SignalEndpointKind,
    SignalEndpointReference,
    SignalKind,
    TerminalAccessory,
    TerminalAccessoryKind,
    TerminalAccessoryState,
    TerminalBlock,
    TerminalPoint,
    WiringConductorRole,
    WiringTerminalReference,
)


def _channel_configuration():
    return SimpleNamespace(
        channel_id="channel-1",
        source_id="CT-101",
        source_equipment_type="current_transformer",
        source_terminal_reference={
            "kind": "terminal",
            "object_id": "CT-101",
            "equipment_type": "current_transformer",
            "terminal_role": "S1",
        },
        signal_type="CURRENT",
        phase="A",
        unit="A",
    )


def _control_mapping(channel_id="channel-1"):
    return ControlSignalMapping(bindings=(
        ControlSignalBinding(
            source=ControlSignalSource(
                domain="measurement",
                element_type="measurement_channel",
                object_id=channel_id,
                signal="value",
            ),
            destination=ControlSignalDestination(
                control_id="control-1",
                component_id="component-1",
                input_name="PV",
                expected_signal_types=("CURRENT",),
                expected_phases=("A",),
                accepted_units=("A",),
            ),
        ),
    ))


def _base_inventory(*, carrier_direction="BIDIRECTIONAL", sink=None):
    signal = SignalDefinition(
        id="signal-1",
        tag="I-101",
        description="CT secondary current",
        kind=SignalKind.CURRENT,
        unit="A",
        phase="A",
        measurement_channel_id="channel-1",
    )
    cable = CableAssembly(
        id="cable-1", tag="C-101", service="CT secondary", core_count=1,
    )
    core = CableCore(
        id="core-1",
        cable_id=cable.id,
        core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(
            WiringTerminalReference("CT-101", "S1", "S1"),
            WiringTerminalReference("TB-101", "1", "1"),
            WiringTerminalReference("PLC-101", "AI1", "AI1"),
        ),
    )
    physical_sink = sink or WiringTerminalReference("PLC-101", "AI1", "AI1")
    endpoint = SignalEndpointBinding(
        id="endpoint-1",
        signal_id=signal.id,
        endpoint=SignalEndpointReference(
            kind=SignalEndpointKind.CONTROL_INPUT,
            endpoint_id="component-1",
            owner_id="control-1",
            port="PV",
            physical_terminal=physical_sink,
        ),
    )
    carrier = SignalCarrierBinding(
        id="carrier-1",
        signal_id=signal.id,
        carrier_kind=CarrierKind.CABLE_CORE,
        carrier_id=core.id,
        direction=carrier_direction,
    )
    return InstrumentationWiringInventory(
        cables=(cable,),
        cores=(core,),
        signals=(signal,),
        signal_bindings=(carrier,),
        endpoint_bindings=(endpoint,),
    )


def _resolve(inventory, *, mapping=None, configurations=None, samples=None, protection=None):
    return resolve_signal_endpoint_bindings(
        inventory,
        project_id="project-1",
        activation_generation=1,
        measurement_channel_configurations=(
            (_channel_configuration(),) if configurations is None else configurations
        ),
        measurement_channels=(
            (SimpleNamespace(channel_id="channel-1"),) if samples is None else samples
        ),
        control_signal_mapping=_control_mapping() if mapping is None else mapping,
        protection_configuration=protection,
    )


def test_control_endpoint_resolves_only_with_exact_channel_and_physical_path():
    result = _resolve(_base_inventory())
    assert len(result) == 1
    assert result[0].status == "RESOLVED"
    assert result[0].channel_id == "channel-1"
    assert result[0].carrier_ids == ("core-1",)


def test_control_endpoint_rejects_wrong_measurement_channel_identity():
    result = _resolve(_base_inventory(), mapping=_control_mapping("other-channel"))
    assert result[0].status == "UNRESOLVED"
    assert any("MeasurementChannel" in item for item in result[0].diagnostics)


def test_control_endpoint_rejects_reversed_carrier_direction():
    result = _resolve(_base_inventory(carrier_direction="SINK_TO_SOURCE"))
    assert result[0].status == "UNRESOLVED"
    assert any("does not permit SOURCE_TO_SINK" in item for item in result[0].diagnostics)


def test_control_endpoint_rejects_sink_terminal_outside_carrier_graph():
    result = _resolve(
        _base_inventory(sink=WiringTerminalReference("PLC-999", "AI9", "AI9"))
    )
    assert result[0].status == "UNRESOLVED"
    assert any("sink terminal" in item for item in result[0].diagnostics)


def test_multiple_physical_routes_to_same_consumer_are_ambiguous():
    base = _base_inventory()
    second_cable = CableAssembly(
        id="cable-2", tag="C-102", service="Parallel CT secondary route", core_count=1,
    )
    second_core = CableCore(
        id="core-2",
        cable_id=second_cable.id,
        core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(
            WiringTerminalReference("CT-101", "S1", "S1"),
            WiringTerminalReference("TB-202", "2", "2"),
            WiringTerminalReference("PLC-101", "AI1", "AI1"),
        ),
    )
    second_binding = SignalCarrierBinding(
        id="carrier-2",
        signal_id="signal-1",
        carrier_kind=CarrierKind.CABLE_CORE,
        carrier_id="core-2",
        direction="BIDIRECTIONAL",
    )
    inventory = InstrumentationWiringInventory(
        cables=base.cables + (second_cable,),
        cores=base.cores + (second_core,),
        signals=base.signals,
        signal_bindings=base.signal_bindings + (second_binding,),
        endpoint_bindings=base.endpoint_bindings,
    )
    result = _resolve(inventory)
    assert result[0].status == "AMBIGUOUS"
    assert result[0].carrier_ids == ("core-1", "core-2")


def _split_route_inventory(accessory_state):
    signal = SignalDefinition(
        id="signal-1",
        tag="I-101",
        description="CT secondary current",
        kind=SignalKind.CURRENT,
        unit="A",
        phase="A",
        measurement_channel_id="channel-1",
    )
    cable_a = CableAssembly(id="cable-a", tag="C-A", service="CT lead", core_count=1)
    cable_b = CableAssembly(id="cable-b", tag="C-B", service="Panel jumper", core_count=1)
    block = TerminalBlock(
        id="TB-101", tag="TB-101", panel_id="P-101", location="Panel", terminal_count=2,
    )
    point_a = TerminalPoint(
        id="tp-1", terminal_block_id=block.id, terminal_number="1", designation="1",
    )
    point_b = TerminalPoint(
        id="tp-2", terminal_block_id=block.id, terminal_number="2", designation="2",
    )
    core_a = CableCore(
        id="core-a", cable_id=cable_a.id, core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(
            WiringTerminalReference("CT-101", "S1", "S1"),
            WiringTerminalReference(block.id, "1", "1", point_a.id),
        ),
    )
    core_b = CableCore(
        id="core-b", cable_id=cable_b.id, core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(
            WiringTerminalReference(block.id, "2", "2", point_b.id),
            WiringTerminalReference("PLC-101", "AI1", "AI1"),
        ),
    )
    accessory = TerminalAccessory(
        id="link-1",
        tag="LINK-1",
        terminal_block_id=block.id,
        kind=TerminalAccessoryKind.FIXED_LINK,
        state=accessory_state,
        terminal_point_ids=(point_a.id, point_b.id),
        conductive_pairs=((point_a.id, point_b.id),),
    )
    endpoint = SignalEndpointBinding(
        id="endpoint-1",
        signal_id=signal.id,
        endpoint=SignalEndpointReference(
            kind=SignalEndpointKind.CONTROL_INPUT,
            endpoint_id="component-1",
            owner_id="control-1",
            port="PV",
            physical_terminal=WiringTerminalReference("PLC-101", "AI1", "AI1"),
        ),
    )
    return InstrumentationWiringInventory(
        cables=(cable_a, cable_b),
        cores=(core_a, core_b),
        signals=(signal,),
        signal_bindings=(
            SignalCarrierBinding(
                id="carrier-a", signal_id=signal.id,
                carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core_a.id,
            ),
            SignalCarrierBinding(
                id="carrier-b", signal_id=signal.id,
                carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core_b.id,
            ),
        ),
        terminal_blocks=(block,),
        terminal_points=(point_a, point_b),
        terminal_accessories=(accessory,),
        endpoint_bindings=(endpoint,),
    )


def test_closed_terminal_accessory_can_complete_physical_signal_path():
    result = _resolve(_split_route_inventory(TerminalAccessoryState.CLOSED))
    assert result[0].status == "RESOLVED"


def test_open_terminal_accessory_does_not_complete_physical_signal_path():
    result = _resolve(_split_route_inventory(TerminalAccessoryState.OPEN))
    assert result[0].status == "UNRESOLVED"
    assert any("discontinuous" in item for item in result[0].diagnostics)
