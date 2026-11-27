import pytest

from core.application.services.instrumentation_wiring_service import InstrumentationWiringService
from core.model.instrument_wiring import (
    CableAssembly,
    CableCore,
    CarrierKind,
    InstrumentationWiringInventory,
    PhysicalConnectionHop,
    WiringConductorRole,
    WiringTerminalReference,
)


def terminal(owner: str, role: str) -> WiringTerminalReference:
    return WiringTerminalReference(owner, role, role)


def test_route_revision_preserves_unchanged_hops_and_retires_removed_segments():
    a, b, c, d = (
        terminal("A", "1"), terminal("B", "1"),
        terminal("C", "1"), terminal("D", "1"),
    )
    cable = CableAssembly(id="cable-1", tag="C-1", service="instrument", core_count=1)
    core = CableCore(
        id="core-1", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, terminal_path=(a, b, c, d),
    )
    hops = (
        PhysicalConnectionHop(
            id="hop-ab", from_terminal=a, to_terminal=b,
            carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
        ),
        PhysicalConnectionHop(
            id="hop-bc", from_terminal=b, to_terminal=c,
            carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
        ),
        PhysicalConnectionHop(
            id="hop-cd", from_terminal=c, to_terminal=d,
            carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
        ),
    )
    service = InstrumentationWiringService()
    service._inventory = InstrumentationWiringInventory(
        cables=(cable,), cores=(core,), connection_hops=hops,
    )

    command = service.create_update_carrier_route_command(
        CarrierKind.CABLE_CORE, core.id, (a, b, d), new_hop_ids=("hop-bd",),
    )
    replacement = command.payload["replacement_inventory"]
    revised = {hop.id: hop for hop in replacement.connection_hops}

    assert replacement.cores[0].terminal_path == (a, b, d)
    assert replacement.cores[0].revision == core.revision + 1
    assert revised["hop-ab"] == hops[0]
    assert revised["hop-bc"].lifecycle_status == "RETIRED"
    assert revised["hop-bc"].revision == hops[1].revision + 1
    assert revised["hop-cd"].lifecycle_status == "RETIRED"
    assert revised["hop-bd"].lifecycle_status == "PLANNED"
    assert revised["hop-bd"].from_terminal == b
    assert revised["hop-bd"].to_terminal == d


def test_route_revision_requires_explicit_ids_for_new_segments_and_never_reuses_ids():
    a, b, c = terminal("A", "1"), terminal("B", "1"), terminal("C", "1")
    cable = CableAssembly(id="cable-2", tag="C-2", service="instrument", core_count=1)
    core = CableCore(
        id="core-2", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, terminal_path=(a, b),
    )
    hop = PhysicalConnectionHop(
        id="hop-existing", from_terminal=a, to_terminal=b,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
    )
    service = InstrumentationWiringService()
    service._inventory = InstrumentationWiringInventory(
        cables=(cable,), cores=(core,), connection_hops=(hop,),
    )

    with pytest.raises(ValueError, match="requires exactly 2 new_hop_ids"):
        service.create_update_carrier_route_command(
            CarrierKind.CABLE_CORE, core.id, (a, c, b),
        )
    with pytest.raises(ValueError, match="must not reuse existing hop IDs"):
        service.create_update_carrier_route_command(
            CarrierKind.CABLE_CORE, core.id, (a, c, b),
            new_hop_ids=("hop-existing", "hop-new"),
        )


def test_route_revision_records_explicit_replacement_lineage():
    a, b, c, d = (
        terminal("A", "1"), terminal("B", "1"),
        terminal("C", "1"), terminal("D", "1"),
    )
    cable = CableAssembly(id="cable-lineage", tag="C-L", service="instrument", core_count=1)
    core = CableCore(
        id="core-lineage", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, terminal_path=(a, b, c, d),
    )
    hops = (
        PhysicalConnectionHop(
            id="hop-lineage-ab", from_terminal=a, to_terminal=b,
            carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
        ),
        PhysicalConnectionHop(
            id="hop-lineage-bc", from_terminal=b, to_terminal=c,
            carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
        ),
        PhysicalConnectionHop(
            id="hop-lineage-cd", from_terminal=c, to_terminal=d,
            carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
        ),
    )
    service = InstrumentationWiringService()
    service._inventory = InstrumentationWiringInventory(
        cables=(cable,), cores=(core,), connection_hops=hops,
    )

    command = service.create_update_carrier_route_command(
        CarrierKind.CABLE_CORE,
        core.id,
        (a, b, d),
        new_hop_ids=("hop-lineage-bd",),
        supersedes_hop_ids=("hop-lineage-bc",),
    )
    replacement = command.payload["replacement_inventory"]
    revised = {hop.id: hop for hop in replacement.connection_hops}

    assert revised["hop-lineage-ab"] == hops[0]
    assert revised["hop-lineage-bc"].lifecycle_status == "REPLACED"
    assert revised["hop-lineage-bc"].revision == hops[1].revision + 1
    assert revised["hop-lineage-cd"].lifecycle_status == "RETIRED"
    assert revised["hop-lineage-bd"].supersedes_hop_id == "hop-lineage-bc"
    assert revised["hop-lineage-bd"].lifecycle_status == "PLANNED"


def test_route_revision_rejects_lineage_to_a_preserved_or_unknown_hop():
    a, b, c = terminal("A", "1"), terminal("B", "1"), terminal("C", "1")
    cable = CableAssembly(id="cable-lineage-invalid", tag="C-LI", service="instrument", core_count=1)
    core = CableCore(
        id="core-lineage-invalid", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, terminal_path=(a, b),
    )
    hop = PhysicalConnectionHop(
        id="hop-lineage-existing", from_terminal=a, to_terminal=b,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
    )
    service = InstrumentationWiringService()
    service._inventory = InstrumentationWiringInventory(
        cables=(cable,), cores=(core,), connection_hops=(hop,),
    )

    with pytest.raises(ValueError, match="retained by the revised route"):
        service.create_update_carrier_route_command(
            CarrierKind.CABLE_CORE, core.id, (a, b, c),
            new_hop_ids=("hop-lineage-bc",),
            supersedes_hop_ids=("hop-lineage-existing",),
        )
    with pytest.raises(ValueError, match="not an active hop of this carrier"):
        service.create_update_carrier_route_command(
            CarrierKind.CABLE_CORE, core.id, (a, c),
            new_hop_ids=("hop-lineage-ac",),
            supersedes_hop_ids=("missing-hop",),
        )
