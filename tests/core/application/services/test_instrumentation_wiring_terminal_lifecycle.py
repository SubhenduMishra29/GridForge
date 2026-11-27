from types import SimpleNamespace

import pytest

from core.application.project import ProjectContext
from core.application.services.instrumentation_wiring_service import InstrumentationWiringService
from core.model.instrument_wiring import (
    CableAssembly,
    CableCore,
    CarrierKind,
    InstrumentationWiringInventory,
    PhysicalConnectionHop,
    TerminalAccessory,
    TerminalAccessoryKind,
    TerminalAccessoryState,
    TerminalBlock,
    TerminalPoint,
    WiringConductorRole,
    WiringTerminalReference,
)


def _service(inventory, *, network=None):
    service = InstrumentationWiringService()
    if network is None:
        network = SimpleNamespace(get_by_identity=lambda _identity: None)
    context = ProjectContext(project_id="project-terminal-lifecycle", name="Test", path=None)
    service.activate(context, inventory, network=network, generation=1)
    return service


def test_retire_terminal_point_prepares_one_atomic_inventory_command():
    block = TerminalBlock(
        id="tb-retire-point", tag="TB-RETIRE-POINT",
        panel_id="PANEL-1", location="MCC-1", terminal_count=1,
    )
    point = TerminalPoint(
        id="tp-retire-point", terminal_block_id=block.id,
        terminal_number="1", designation="X1:1",
    )
    service = _service(InstrumentationWiringInventory(
        terminal_blocks=(block,), terminal_points=(point,),
    ))

    command = service.create_retire_terminal_point_command(point.id)
    replacement = command.payload["replacement_inventory"]
    assert replacement.terminal_points[0].id == point.id
    assert replacement.terminal_points[0].lifecycle_status == "RETIRED"
    assert replacement.terminal_points[0].revision == point.revision + 1


def test_retire_terminal_block_retires_child_points_in_the_same_command():
    block = TerminalBlock(
        id="tb-retire-block", tag="TB-RETIRE-BLOCK",
        panel_id="PANEL-1", location="MCC-1", terminal_count=2,
        lifecycle_status="INSTALLED",
    )
    points = (
        TerminalPoint(
            id="tp-retire-block-1", terminal_block_id=block.id,
            terminal_number="1", designation="X1:1", lifecycle_status="INSTALLED",
        ),
        TerminalPoint(
            id="tp-retire-block-2", terminal_block_id=block.id,
            terminal_number="2", designation="X1:2",
            lifecycle_status="PLANNED",
        ),
    )
    service = _service(InstrumentationWiringInventory(
        terminal_blocks=(block,), terminal_points=points,
    ))

    command = service.create_retire_terminal_block_command(block.id)
    replacement = command.payload["replacement_inventory"]
    assert replacement.terminal_blocks[0].lifecycle_status == "RETIRED"
    assert replacement.terminal_blocks[0].revision == block.revision + 1
    assert tuple(item.lifecycle_status for item in replacement.terminal_points) == (
        "RETIRED", "RETIRED",
    )
    assert tuple(item.revision for item in replacement.terminal_points) == (2, 2)


def test_terminal_retirement_fails_until_active_routes_are_reconciled():
    block = TerminalBlock(
        id="tb-live-route", tag="TB-LIVE-ROUTE",
        panel_id="PANEL-1", location="MCC-1", terminal_count=1,
        lifecycle_status="INSTALLED",
    )
    point = TerminalPoint(
        id="tp-live-route", terminal_block_id=block.id,
        terminal_number="1", designation="X1:1", lifecycle_status="INSTALLED",
    )
    terminal = WiringTerminalReference(
        block.id, point.terminal_number, point.designation,
        terminal_point_id=point.id,
    )
    device = WiringTerminalReference("DEVICE-1", "AI+", "AI+")
    cable = CableAssembly(
        id="cable-live-route", tag="C-LIVE-ROUTE",
        service="signal", core_count=1,
    )
    core = CableCore(
        id="core-live-route", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, terminal_path=(device, terminal),
    )
    equipment = SimpleNamespace(id="DEVICE-1")
    equipment.terminals = (SimpleNamespace(role="AI+", owner=equipment),)
    network = SimpleNamespace(
        get_by_identity=lambda identity: equipment if identity == "DEVICE-1" else None
    )
    service = _service(InstrumentationWiringInventory(
        cables=(cable,), cores=(core,),
        terminal_blocks=(block,), terminal_points=(point,),
    ), network=network)

    with pytest.raises(ValueError, match="non-active terminal point"):
        service.create_retire_terminal_point_command(point.id)


def test_block_retirement_fails_while_accessory_is_not_removed():
    block = TerminalBlock(
        id="tb-accessory-live", tag="TB-ACCESSORY-LIVE",
        panel_id="PANEL-1", location="MCC-1", terminal_count=1,
        lifecycle_status="INSTALLED",
    )
    point = TerminalPoint(
        id="tp-accessory-live", terminal_block_id=block.id,
        terminal_number="1", designation="X1:1", lifecycle_status="INSTALLED",
    )
    accessory = TerminalAccessory(
        id="acc-accessory-live", tag="ACC-ACCESSORY-LIVE",
        terminal_block_id=block.id, kind=TerminalAccessoryKind.OTHER,
        state=TerminalAccessoryState.UNKNOWN, terminal_point_ids=(point.id,),
    )
    service = _service(InstrumentationWiringInventory(
        terminal_blocks=(block,), terminal_points=(point,),
        terminal_accessories=(accessory,),
    ))

    with pytest.raises(ValueError, match="must be REMOVED"):
        service.create_retire_terminal_block_command(block.id)


def test_installed_terminal_identity_cannot_be_deleted_from_the_inventory():
    block = TerminalBlock(
        id="tb-immutable-history", tag="TB-IMMUTABLE-HISTORY",
        panel_id="PANEL-1", location="MCC-1", terminal_count=1,
        lifecycle_status="INSTALLED",
    )
    point = TerminalPoint(
        id="tp-immutable-history", terminal_block_id=block.id,
        terminal_number="1", designation="X1:1", lifecycle_status="INSTALLED",
    )
    service = _service(InstrumentationWiringInventory(
        terminal_blocks=(block,), terminal_points=(point,),
    ))

    with pytest.raises(ValueError, match="cannot be removed after it leaves PLANNED"):
        service.create_replace_command(InstrumentationWiringInventory(
            terminal_blocks=(block,), terminal_points=(),
        ))


def test_activation_ignores_retired_hop_endpoints_missing_from_live_terminal_inventory():
    block = TerminalBlock(
        id="tb-current", tag="TB-CURRENT",
        panel_id="PANEL-1", location="MCC-1", terminal_count=1,
        lifecycle_status="INSTALLED",
    )
    point = TerminalPoint(
        id="tp-current", terminal_block_id=block.id,
        terminal_number="1", designation="X1:1", lifecycle_status="INSTALLED",
    )
    live_terminal = WiringTerminalReference(
        block.id, point.terminal_number, point.designation,
        terminal_point_id=point.id,
    )
    old_terminal = WiringTerminalReference(
        "tb-removed", "1", "X-OLD:1", terminal_point_id="tp-removed",
    )
    device = WiringTerminalReference("DEVICE-1", "AI+", "AI+")
    cable = CableAssembly(
        id="cable-history", tag="C-HISTORY", service="signal", core_count=1,
    )
    core = CableCore(
        id="core-history", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, terminal_path=(device, live_terminal),
    )
    retired_hop = PhysicalConnectionHop(
        id="hop-history", from_terminal=device, to_terminal=old_terminal,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
        lifecycle_status="RETIRED",
    )
    equipment = SimpleNamespace(id="DEVICE-1")
    equipment.terminals = (SimpleNamespace(role="AI+", owner=equipment),)
    network = SimpleNamespace(
        get_by_identity=lambda identity: equipment if identity == "DEVICE-1" else None
    )
    inventory = InstrumentationWiringInventory(
        cables=(cable,), cores=(core,), connection_hops=(retired_hop,),
        terminal_blocks=(block,), terminal_points=(point,),
    )

    service = _service(inventory, network=network)
    assert service.inventory.connection_hops == (retired_hop,)


def test_terminal_retirement_inverse_restores_prior_lifecycle_state():
    from core.application.transaction import Transaction

    block = TerminalBlock(
        id="tb-undo-retire", tag="TB-UNDO-RETIRE",
        panel_id="PANEL-1", location="MCC-1", terminal_count=1,
        lifecycle_status="INSTALLED",
    )
    point = TerminalPoint(
        id="tp-undo-retire", terminal_block_id=block.id,
        terminal_number="1", designation="X1:1", lifecycle_status="INSTALLED",
    )
    network = SimpleNamespace(get_by_identity=lambda _identity: None)
    service = _service(InstrumentationWiringInventory(
        terminal_blocks=(block,), terminal_points=(point,),
    ), network=network)
    context = SimpleNamespace(network=network)

    command = service.create_retire_terminal_point_command(point.id)
    service.execute(command, context, Transaction())
    assert service.inventory.terminal_points[0].lifecycle_status == "RETIRED"
    assert service.inventory.terminal_points[0].revision == 2

    inverse = command.inverse()
    assert inverse.payload["allow_terminal_lifecycle_rollback"] is True
    service.execute(inverse, context, Transaction())
    assert service.inventory.terminal_points[0].lifecycle_status == "INSTALLED"
    assert service.inventory.terminal_points[0].revision == 1



def test_terminal_record_update_requires_a_monotonic_revision():
    from dataclasses import replace

    block = TerminalBlock(
        id="tb-revision-guard", tag="TB-REVISION-GUARD",
        panel_id="PANEL-1", location="MCC-1", terminal_count=1,
        lifecycle_status="INSTALLED",
    )
    point = TerminalPoint(
        id="tp-revision-guard", terminal_block_id=block.id,
        terminal_number="1", designation="X1:1", lifecycle_status="INSTALLED",
    )
    service = _service(InstrumentationWiringInventory(
        terminal_blocks=(block,), terminal_points=(point,),
    ))
    changed_without_revision = replace(point, designation="X1:2")
    candidate = InstrumentationWiringInventory(
        terminal_blocks=(block,), terminal_points=(changed_without_revision,),
    )

    with pytest.raises(ValueError, match="revision must advance"):
        service.create_replace_command(candidate)


def test_retired_terminal_history_is_immutable():
    from dataclasses import replace

    block = TerminalBlock(
        id="tb-retired-immutable", tag="TB-RETIRED-IMMUTABLE",
        panel_id="PANEL-1", location="MCC-1", terminal_count=1,
        lifecycle_status="INSTALLED",
    )
    point = TerminalPoint(
        id="tp-retired-immutable", terminal_block_id=block.id,
        terminal_number="1", designation="X1:1",
        lifecycle_status="RETIRED", revision=2,
    )
    service = _service(InstrumentationWiringInventory(
        terminal_blocks=(block,), terminal_points=(point,),
    ))
    changed = replace(point, designation="X1:1-CORRECTED", revision=3)
    candidate = InstrumentationWiringInventory(
        terminal_blocks=(block,), terminal_points=(changed,),
    )

    with pytest.raises(ValueError, match="immutable after it is RETIRED"):
        service.create_replace_command(candidate)
