from dataclasses import FrozenInstanceError

import pytest

from core.model import (
    CableAssembly,
    InstrumentationWiringInventory,
    CableCore,
    CarrierKind,
    WiringConductorRole,
    PanelWire,
    SignalCarrierBinding,
    SignalDefinition,
    SignalKind,
    WiringTerminalReference,
    PhysicalConnectionHop,
)


def terminal(equipment: str, terminal_id: str, designation: str):
    return WiringTerminalReference(equipment, terminal_id, designation)


def test_cable_and_core_keep_physical_identity_separate_from_signal():
    cable = CableAssembly(
        id="cable-id-1",
        tag="C-CT101-001",
        service="CT secondary",
        core_count=2,
        cable_type="declared project cable type",
        length_m=18.5,
    )
    core = CableCore(
        id="core-id-1",
        cable_id=cable.id,
        core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(
            terminal("CT-101", "ct-s1", "S1"),
            terminal("TB-101", "tb-01", "1"),
            terminal("RELAY-101", "relay-ia", "IA+"),
        ),
        core_tag="C-CT101-001/1",
    )
    signal = SignalDefinition(
        id="signal-id-1",
        tag="IA_PHASE_A",
        description="Phase A current measurement",
        kind=SignalKind.CURRENT,
        unit="A",
        phase="A",
    )
    binding = SignalCarrierBinding(
        id="binding-1",
        signal_id=signal.id,
        carrier_kind=CarrierKind.CABLE_CORE,
        carrier_id=core.id,
        direction="SOURCE_TO_SINK",
    )

    assert core.cable_id == cable.id
    assert core.terminal_path[0].designation == "S1"
    assert binding.carrier_id == core.id
    assert binding.signal_id == signal.id
    assert cable.tag != signal.tag
    with pytest.raises(FrozenInstanceError):
        cable.tag = "RENAMED"


def test_cable_assembly_rejects_invalid_core_count_and_length():
    with pytest.raises(ValueError):
        CableAssembly(id="c1", tag="C1", service="control", core_count=0)
    with pytest.raises(ValueError):
        CableAssembly(id="c1", tag="C1", service="control", core_count=2, length_m=float("inf"))


def test_core_requires_unique_terminal_path_and_valid_role():
    a = terminal("CT-101", "s1", "S1")
    with pytest.raises(ValueError):
        CableCore(
            id="core-1",
            cable_id="cable-1",
            core_number=1,
            role=WiringConductorRole.SIGNAL,
            terminal_path=(a, a),
        )
    with pytest.raises(TypeError):
        CableCore(id="core-1", cable_id="cable-1", core_number=1, role="SIGNAL")


def test_panel_wire_requires_two_distinct_terminals():
    a = terminal("TB-1", "1", "1")
    with pytest.raises(ValueError):
        PanelWire(id="wire-1", tag="W-1", role=WiringConductorRole.RETURN, terminal_path=(a,))
    with pytest.raises(ValueError):
        PanelWire(id="wire-1", tag="W-1", role=WiringConductorRole.RETURN, terminal_path=(a, a))


def test_signal_binding_validates_carrier_and_direction():
    with pytest.raises(ValueError):
        SignalCarrierBinding(
            id="b1", signal_id="s1", carrier_kind=CarrierKind.CABLE_CORE,
            carrier_id="c1", direction="SIDEWAYS",
        )



def test_inventory_enforces_cable_core_ownership_and_numbering():
    cable = CableAssembly(id="c1", tag="C-1", service="instrument", core_count=1)
    core = CableCore(id="cc1", cable_id="c1", core_number=1, role=WiringConductorRole.SIGNAL)
    inventory = InstrumentationWiringInventory(cables=(cable,), cores=(core,))
    assert inventory.cores == (core,)

    invalid = CableCore(id="cc2", cable_id="c1", core_number=2, role=WiringConductorRole.RETURN)
    with pytest.raises(ValueError, match="exceeds cable"):
        InstrumentationWiringInventory(cables=(cable,), cores=(invalid,))


def test_inventory_rejects_duplicate_tags_and_dangling_signal_bindings():
    cable_a = CableAssembly(id="c1", tag="C-1", service="instrument", core_count=1)
    cable_b = CableAssembly(id="c2", tag="C-1", service="instrument", core_count=1)
    with pytest.raises(ValueError, match="Duplicate cable tag"):
        InstrumentationWiringInventory(cables=(cable_a, cable_b))

    signal = SignalDefinition(id="s1", tag="SIG-1", description="Current", kind=SignalKind.CURRENT)
    dangling = SignalCarrierBinding(
        id="b1", signal_id=signal.id, carrier_kind=CarrierKind.CABLE_CORE,
        carrier_id="missing-core",
    )
    with pytest.raises(ValueError, match="missing cable core"):
        InstrumentationWiringInventory(signals=(signal,), signal_bindings=(dangling,))


def test_inventory_enforces_one_case_insensitive_tag_namespace_across_record_kinds():
    cable = CableAssembly(id="cable-1", tag="CAB-001", service="instrument", core_count=1)
    core = CableCore(
        id="core-1", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, core_tag="CORE-001",
    )
    wire = PanelWire(
        id="wire-1", tag="wire-001", role=WiringConductorRole.SIGNAL,
        terminal_path=(terminal("TB-1", "1", "1"), terminal("TB-2", "1", "1")),
    )
    signal = SignalDefinition(
        id="signal-1", tag="SIG-001", description="Pressure",
        kind=SignalKind.ANALOG,
    )
    valid = InstrumentationWiringInventory(
        cables=(cable,), cores=(core,), panel_wires=(wire,), signals=(signal,),
    )
    assert valid.signals == (signal,)

    duplicate_signal = SignalDefinition(
        id="signal-2", tag="cab-001", description="Conflicting tag",
        kind=SignalKind.ANALOG,
    )
    with pytest.raises(ValueError, match="Duplicate project wiring tag"):
        InstrumentationWiringInventory(
            cables=(cable,), cores=(core,), panel_wires=(wire,),
            signals=(signal, duplicate_signal),
        )

    duplicate_core = CableCore(
        id="core-2", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.RETURN, core_tag="SIG-001",
    )
    with pytest.raises(ValueError, match="Duplicate project wiring tag"):
        InstrumentationWiringInventory(
            cables=(cable,), cores=(core, duplicate_core), signals=(signal,),
        )


def test_physical_connection_hops_have_stable_ids_and_validate_carrier_segments():
    a = terminal("CT-101", "s1", "S1")
    b = terminal("TB-101", "1", "1")
    c_terminal = terminal("RELAY-101", "ia", "IA+")
    cable = CableAssembly(id="cable-hop", tag="C-HOP", service="CT secondary", core_count=1)
    core = CableCore(
        id="core-hop", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, terminal_path=(a, b, c_terminal),
    )
    first = PhysicalConnectionHop(
        id="hop-stable-001", from_terminal=a, to_terminal=b,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
    )
    second = PhysicalConnectionHop(
        id="hop-stable-002", from_terminal=b, to_terminal=c_terminal,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
        revision=2, lifecycle_status="REPLACED", supersedes_hop_id=first.id,
    )
    inventory = InstrumentationWiringInventory(
        cables=(cable,), cores=(core,), connection_hops=(first, second),
    )
    assert tuple(hop.id for hop in inventory.connection_hops) == (
        "hop-stable-001", "hop-stable-002",
    )
    assert second.supersedes_hop_id == first.id

    non_adjacent = PhysicalConnectionHop(
        id="hop-invalid", from_terminal=a, to_terminal=c_terminal,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
    )
    with pytest.raises(ValueError, match="not an adjacent segment"):
        InstrumentationWiringInventory(
            cables=(cable,), cores=(core,), connection_hops=(non_adjacent,),
        )


def test_physical_connection_hop_rejects_missing_carrier_and_predecessor():
    a = terminal("TB-1", "1", "1")
    b = terminal("TB-2", "1", "1")
    missing_carrier = PhysicalConnectionHop(
        id="hop-1", from_terminal=a, to_terminal=b,
        carrier_kind=CarrierKind.PANEL_WIRE, carrier_id="absent-wire",
    )
    with pytest.raises(ValueError, match="references missing panel_wire"):
        InstrumentationWiringInventory(connection_hops=(missing_carrier,))

    wire = PanelWire(
        id="wire-hop", tag="W-HOP", role=WiringConductorRole.SIGNAL,
        terminal_path=(a, b),
    )
    missing_predecessor = PhysicalConnectionHop(
        id="hop-2", from_terminal=a, to_terminal=b,
        carrier_kind=CarrierKind.PANEL_WIRE, carrier_id=wire.id,
        supersedes_hop_id="absent-hop",
    )
    with pytest.raises(ValueError, match="supersedes missing hop"):
        InstrumentationWiringInventory(
            panel_wires=(wire,), connection_hops=(missing_predecessor,),
        )



def test_terminal_block_points_and_accessories_have_stable_validated_identity():
    from core.model.instrument_wiring import (
        InstrumentationWiringInventory,
        TerminalAccessory,
        TerminalAccessoryKind,
        TerminalAccessoryState,
        TerminalBlock,
        TerminalPoint,
    )

    block = TerminalBlock(
        id="tb-1", tag="TB-01", panel_id="PANEL-1",
        location="MCC-1", terminal_count=4,
    )
    first = TerminalPoint(
        id="tp-1", terminal_block_id=block.id,
        terminal_number="1", designation="X1:1",
    )
    second = TerminalPoint(
        id="tp-2", terminal_block_id=block.id,
        terminal_number="2", designation="X1:2",
    )
    link = TerminalAccessory(
        id="link-1", tag="LINK-01", terminal_block_id=block.id,
        kind=TerminalAccessoryKind.TEST_DISCONNECT,
        state=TerminalAccessoryState.CLOSED,
        terminal_point_ids=(first.id, second.id),
        conductive_pairs=((first.id, second.id),),
    )
    inventory = InstrumentationWiringInventory(
        terminal_blocks=(block,),
        terminal_points=(first, second),
        terminal_accessories=(link,),
    )

    assert inventory.terminal_blocks == (block,)
    assert link.active_conductive_pairs == ((first.id, second.id),)
    opened = TerminalAccessory(
        id="link-open", tag="LINK-02", terminal_block_id=block.id,
        kind=TerminalAccessoryKind.TEST_DISCONNECT,
        state=TerminalAccessoryState.OPEN,
        terminal_point_ids=(first.id, second.id),
        conductive_pairs=((first.id, second.id),),
    )
    assert opened.active_conductive_pairs == ()


def test_terminal_point_references_require_exact_inventory_identity():
    from core.model.instrument_wiring import (
        CableAssembly,
        CableCore,
        InstrumentationWiringInventory,
        TerminalBlock,
        TerminalPoint,
        WiringConductorRole,
        WiringTerminalReference,
    )

    block = TerminalBlock(
        id="tb-2", tag="TB-02", panel_id="PANEL-1",
        location="MCC-1", terminal_count=2,
    )
    point = TerminalPoint(
        id="tp-3", terminal_block_id=block.id,
        terminal_number="1", designation="X2:1",
    )
    terminal = WiringTerminalReference(
        equipment_id=block.id, terminal_role="1",
        designation="X2:1", terminal_point_id=point.id,
    )
    device = WiringTerminalReference(
        equipment_id="DEVICE-1", terminal_role="S1", designation="S1",
    )
    inventory = InstrumentationWiringInventory(
        cables=(CableAssembly(id="c-1", tag="C-01", service="instrument", core_count=1),),
        cores=(CableCore(
            id="core-1", cable_id="c-1", core_number=1,
            role=WiringConductorRole.SIGNAL,
            terminal_path=(device, terminal),
        ),),
        terminal_blocks=(block,), terminal_points=(point,),
    )
    assert inventory.cores[0].terminal_path[1].canonical_identity == (
        block.id, "1", point.id,
    )

    with pytest.raises(ValueError, match="terminal_point_id"):
        InstrumentationWiringInventory(
            terminal_blocks=(block,),
            terminal_points=(point,),
            cables=(CableAssembly(id="c-2", tag="C-02", service="instrument", core_count=1),),
            cores=(CableCore(
                id="core-2", cable_id="c-2", core_number=1,
                role=WiringConductorRole.SIGNAL,
                terminal_path=(
                    device,
                    WiringTerminalReference(
                        equipment_id=block.id, terminal_role="1", designation="X2:1",
                    ),
                ),
            ),),
        )


def test_terminal_points_reject_duplicate_designations_and_cross_block_accessories():
    from core.model.instrument_wiring import (
        InstrumentationWiringInventory,
        TerminalAccessory,
        TerminalAccessoryKind,
        TerminalAccessoryState,
        TerminalBlock,
        TerminalPoint,
    )

    first = TerminalBlock(id="tb-a", tag="TB-A", panel_id="P", location="L", terminal_count=2)
    second = TerminalBlock(id="tb-b", tag="TB-B", panel_id="P", location="L", terminal_count=2)
    point_a = TerminalPoint(id="tp-a", terminal_block_id=first.id, terminal_number="1", designation="X1:1")
    point_b = TerminalPoint(id="tp-b", terminal_block_id=first.id, terminal_number="2", designation="X1:1")
    with pytest.raises(ValueError, match="duplicate terminal designation"):
        InstrumentationWiringInventory(
            terminal_blocks=(first,), terminal_points=(point_a, point_b),
        )

    foreign = TerminalPoint(id="tp-c", terminal_block_id=second.id, terminal_number="1", designation="X2:1")
    accessory = TerminalAccessory(
        id="acc-1", tag="ACC-1", terminal_block_id=first.id,
        kind=TerminalAccessoryKind.FIXED_LINK, state=TerminalAccessoryState.CLOSED,
        terminal_point_ids=(point_a.id, foreign.id),
        conductive_pairs=((point_a.id, foreign.id),),
    )
    with pytest.raises(ValueError, match="another block"):
        InstrumentationWiringInventory(
            terminal_blocks=(first, second),
            terminal_points=(point_a, foreign),
            terminal_accessories=(accessory,),
        )
