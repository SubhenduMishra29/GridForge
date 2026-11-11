from dataclasses import FrozenInstanceError

import pytest

from core.model import (
    CableAssembly,
    InstrumentationWiringInventory,
    CableCore,
    CarrierKind,
    ConductorRole,
    PanelWire,
    SignalCarrierBinding,
    SignalDefinition,
    SignalKind,
    WiringTerminalReference,
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
        role=ConductorRole.SIGNAL,
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
            role=ConductorRole.SIGNAL,
            terminal_path=(a, a),
        )
    with pytest.raises(TypeError):
        CableCore(id="core-1", cable_id="cable-1", core_number=1, role="SIGNAL")


def test_panel_wire_requires_two_distinct_terminals():
    a = terminal("TB-1", "1", "1")
    with pytest.raises(ValueError):
        PanelWire(id="wire-1", tag="W-1", role=ConductorRole.RETURN, terminal_path=(a,))
    with pytest.raises(ValueError):
        PanelWire(id="wire-1", tag="W-1", role=ConductorRole.RETURN, terminal_path=(a, a))


def test_signal_binding_validates_carrier_and_direction():
    with pytest.raises(ValueError):
        SignalCarrierBinding(
            id="b1", signal_id="s1", carrier_kind=CarrierKind.CABLE_CORE,
            carrier_id="c1", direction="SIDEWAYS",
        )



def test_inventory_enforces_cable_core_ownership_and_numbering():
    cable = CableAssembly(id="c1", tag="C-1", service="instrument", core_count=1)
    core = CableCore(id="cc1", cable_id="c1", core_number=1, role=ConductorRole.SIGNAL)
    inventory = InstrumentationWiringInventory(cables=(cable,), cores=(core,))
    assert inventory.cores == (core,)

    invalid = CableCore(id="cc2", cable_id="c1", core_number=2, role=ConductorRole.RETURN)
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
