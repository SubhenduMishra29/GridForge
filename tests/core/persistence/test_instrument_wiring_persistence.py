"""Canonical instrumentation wiring persistence and lifecycle contracts."""

import pytest
from types import SimpleNamespace

from core.application.transaction import Transaction

from core.application.project import ProjectContext
from core.application.services.instrumentation_wiring_service import InstrumentationWiringService
from core.model.instrument_wiring import (
    CableAssembly, CableCore, CarrierKind, InstrumentationWiringInventory,
    SignalCarrierBinding, SignalDefinition, SignalKind, WiringConductorRole,
    WiringTagSeries, WiringTagPolicy,
)
from core.persistence.instrument_wiring_serializer import (
    InstrumentationWiringSerializationError,
    deserialize_instrumentation_wiring,
    serialize_instrumentation_wiring,
)
from core.persistence.migration import _ProjectSchema5To6, _ProjectSchema6To7, _ProjectSchema7To8, _ProjectSchema8To9


class FakeNetwork:
    def get_by_identity(self, equipment_id):
        raise KeyError(equipment_id)


def sample_inventory():
    cable = CableAssembly(
        id="cable-id", tag="C-CT101", service="CT secondary", core_count=2,
        length_m=12.5,
    )
    core = CableCore(
        id="core-id", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, core_tag="C-CT101/1",
    )
    signal = SignalDefinition(
        id="signal-id", tag="IA_A", description="Phase A current",
        kind=SignalKind.CURRENT, unit="A", phase="A",
    )
    binding = SignalCarrierBinding(
        id="binding-id", signal_id=signal.id,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
        direction="SOURCE_TO_SINK",
    )
    return InstrumentationWiringInventory(
        cables=(cable,), cores=(core,), signals=(signal,),
        signal_bindings=(binding,),
    )


def test_wiring_inventory_codec_round_trips_without_losing_identity():
    inventory = sample_inventory()
    restored = deserialize_instrumentation_wiring(
        serialize_instrumentation_wiring(inventory)
    )
    assert restored == inventory


def test_wiring_inventory_codec_rejects_unknown_top_level_fields():
    payload = serialize_instrumentation_wiring(sample_inventory())
    payload["geometry"] = {"x": 10, "y": 20}
    with pytest.raises(InstrumentationWiringSerializationError, match="fields"):
        deserialize_instrumentation_wiring(payload)


def test_schema_five_migration_adds_only_an_empty_inventory():
    source = {"schema": 5, "project": {"project_id": "p1"}}
    migrated = _ProjectSchema5To6().migrate(source)
    assert migrated["schema"] == 6
    assert migrated["instrumentation_wiring"] == {
        "schema": 1, "cables": [], "cores": [], "panel_wires": [],
        "signals": [], "signal_bindings": [],
    }
    assert source == {"schema": 5, "project": {"project_id": "p1"}}


def test_wiring_service_activation_and_rollback_are_project_scoped():
    service = InstrumentationWiringService()
    initial = service.snapshot_state()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    inventory = sample_inventory()
    service.activate(context, inventory, network=FakeNetwork(), generation=4)
    assert service.project_id == "project-1"
    assert service.activation_generation == 4
    assert service.inventory == inventory
    service.restore_state(initial)
    assert service.project_id is None
    assert service.inventory == InstrumentationWiringInventory()


def test_wiring_service_rejects_inventory_without_project():
    service = InstrumentationWiringService()
    with pytest.raises(ValueError, match="project-less"):
        service.activate(None, sample_inventory())

def test_wiring_inventory_codec_rejects_unknown_record_fields():
    payload = serialize_instrumentation_wiring(sample_inventory())
    payload["cables"][0]["unmodeled_tag"] = "not-safe-to-drop"
    with pytest.raises(InstrumentationWiringSerializationError, match="unknown"):
        deserialize_instrumentation_wiring(payload)

def test_wiring_inventory_codec_rejects_boolean_schema_version():
    payload = serialize_instrumentation_wiring(sample_inventory())
    payload["schema"] = True
    with pytest.raises(InstrumentationWiringSerializationError, match="schema"):
        deserialize_instrumentation_wiring(payload)


def test_wiring_service_rejects_terminal_not_in_active_network():
    from core.model.instrument_wiring import WiringTerminalReference

    inventory = InstrumentationWiringInventory(
        cables=(CableAssembly(id="c", tag="C-1", service="instrument", core_count=1),),
        cores=(CableCore(
            id="cc", cable_id="c", core_number=1,
            role=WiringConductorRole.SIGNAL,
            terminal_path=(
                WiringTerminalReference("missing", "S1", "S1"),
                WiringTerminalReference("other", "1", "1"),
            ),
        ),),
    )
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    with pytest.raises(ValueError, match="not registered"):
        InstrumentationWiringService().activate(
            context, inventory, network=FakeNetwork(), generation=1
        )

def test_inventory_replacement_command_is_transactional_and_undoable():
    service = InstrumentationWiringService()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    network = FakeNetwork()
    original = sample_inventory()
    service.activate(context, original, network=network, generation=4)
    replacement = InstrumentationWiringInventory()
    command = service.create_replace_command(replacement)
    transaction = Transaction()
    result = service.execute(command, SimpleNamespace(network=network), transaction)
    assert result.success is True
    assert service.inventory is replacement
    journal = transaction.commit()
    assert len(journal) == 1
    journal[0]()
    assert service.inventory is original


def test_inventory_replacement_command_rejects_stale_expected_snapshot():
    service = InstrumentationWiringService()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    network = FakeNetwork()
    original = sample_inventory()
    service.activate(context, original, network=network, generation=4)
    stale_command = service.create_replace_command(InstrumentationWiringInventory())
    service.activate(context, InstrumentationWiringInventory(), network=network, generation=5)
    with pytest.raises(ValueError, match="changed since"):
        service.execute(stale_command, SimpleNamespace(network=network), Transaction())

def _apply_wiring_command(service, network, command):
    transaction = Transaction()
    result = service.execute(command, SimpleNamespace(network=network), transaction)
    assert result.success is True
    transaction.commit()


def test_typed_record_add_and_update_use_atomic_inventory_command():
    service = InstrumentationWiringService()
    network = FakeNetwork()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    service.activate(context, InstrumentationWiringInventory(), network=network, generation=1)
    cable = CableAssembly(id="new-cable", tag="CAB-1", service="RTD", core_count=2)
    add = service.create_add_record_command(cable)
    _apply_wiring_command(service, network, add)
    assert service.inventory.cables == (cable,)

    updated = CableAssembly(
        id="new-cable", tag="CAB-1", service="RTD loop", core_count=2,
        length_m=18.0,
    )
    update = service.create_update_record_command(updated)
    _apply_wiring_command(service, network, update)
    assert service.inventory.cables == (updated,)


def test_typed_record_add_rejects_duplicate_identity_and_tag():
    service = InstrumentationWiringService()
    network = FakeNetwork()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    cable = CableAssembly(id="c1", tag="CAB-1", service="RTD", core_count=1)
    service.activate(context, InstrumentationWiringInventory(cables=(cable,)), network=network, generation=1)
    with pytest.raises(ValueError, match="already exists"):
        service.create_add_record_command(cable)
    duplicate_tag = CableAssembly(id="c2", tag="CAB-1", service="PT", core_count=1)
    with pytest.raises(ValueError, match="Duplicate cable tag"):
        service.create_add_record_command(duplicate_tag)


def test_record_removal_rejects_dangling_cable_core_and_signal_references():
    service = InstrumentationWiringService()
    network = FakeNetwork()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    inventory = sample_inventory()
    service.activate(context, inventory, network=network, generation=1)
    with pytest.raises(ValueError, match="references missing cable"):
        service.create_remove_record_command(CableAssembly, "cable-id")
    with pytest.raises(ValueError, match="references missing cable core"):
        service.create_remove_record_command(CableCore, "core-id")
    with pytest.raises(ValueError, match="references missing signal"):
        service.create_remove_record_command(SignalDefinition, "signal-id")


def test_record_removal_succeeds_after_dependencies_are_removed():
    service = InstrumentationWiringService()
    network = FakeNetwork()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    service.activate(context, sample_inventory(), network=network, generation=1)
    binding = service.create_remove_record_command(SignalCarrierBinding, "binding-id")
    _apply_wiring_command(service, network, binding)
    core = service.create_remove_record_command(CableCore, "core-id")
    _apply_wiring_command(service, network, core)
    signal = service.create_remove_record_command(SignalDefinition, "signal-id")
    _apply_wiring_command(service, network, signal)
    cable = service.create_remove_record_command(CableAssembly, "cable-id")
    _apply_wiring_command(service, network, cable)
    assert service.inventory == InstrumentationWiringInventory()

def test_wiring_read_model_is_detached_and_immutable():
    service = InstrumentationWiringService()
    network = FakeNetwork()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    inventory = sample_inventory()
    service.activate(context, inventory, network=network, generation=8)
    read_model = service.read_model()
    assert read_model.project_id == "project-1"
    assert read_model.activation_generation == 8
    assert read_model.cables[0]["tag"] == "C-CT101"
    with pytest.raises(TypeError):
        read_model.cables[0]["tag"] = "MUTATED"
    assert service.inventory is inventory
    assert service.inventory.cables[0].tag == "C-CT101"


def test_wiring_read_model_rejects_projectless_service():
    with pytest.raises(RuntimeError, match="No active project"):
        InstrumentationWiringService().read_model()

def test_schema_six_migration_adds_empty_tag_policy_without_inference():
    source = {
        "schema": 6,
        "instrumentation_wiring": {
            "schema": 1, "cables": [], "cores": [], "panel_wires": [],
            "signals": [], "signal_bindings": [],
        },
    }
    migrated = _ProjectSchema6To7().migrate(source)
    assert migrated["schema"] == 7
    assert migrated["instrumentation_wiring"]["schema"] == 2
    assert migrated["instrumentation_wiring"]["tag_policy"] == []
    assert source["instrumentation_wiring"]["schema"] == 1


def test_tag_policy_uses_explicit_project_format_and_skips_collisions():
    policy = WiringTagPolicy(series=(
        WiringTagSeries(
            record_kind="CABLE", prefix="INST-CAB",
            separator="/", minimum_digits=4, next_number=1,
        ),
    ))
    tag, advanced = policy.allocate("cable", used_tags=("INST-CAB/0001",))
    assert tag == "INST-CAB/0002"
    assert advanced.series[0].next_number == 3
    assert policy.series[0].next_number == 1


def test_tag_counter_and_new_record_are_one_inventory_command():
    service = InstrumentationWiringService()
    network = FakeNetwork()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    policy = WiringTagPolicy(series=(
        WiringTagSeries(record_kind="CABLE", prefix="CAB", separator="-"),
    ))
    initial = InstrumentationWiringInventory(tag_policy=policy)
    service.activate(context, initial, network=network, generation=1)
    tag, policy_candidate = service.allocate_tag("CABLE")
    cable = CableAssembly(id="tagged-cable", tag=tag, service="PT secondary", core_count=2)
    command = service.create_add_record_command(cable, tag_policy_inventory=policy_candidate)
    _apply_wiring_command(service, network, command)
    assert service.inventory.cables[0].tag == "CAB-001"
    assert service.inventory.tag_policy.series[0].next_number == 2


def test_wiring_codec_round_trips_hop_identity_and_lifecycle_without_geometry():
    from core.model.instrument_wiring import PhysicalConnectionHop, WiringTerminalReference

    start = WiringTerminalReference("TX-1", "AI+", "1+")
    end = WiringTerminalReference("PLC-1", "AI+", "CH1+")
    cable = CableAssembly(id="cable-hop", tag="CAB-HOP", service="4-20 mA", core_count=1)
    core = CableCore(id="core-hop", cable_id=cable.id, core_number=1, role=WiringConductorRole.SIGNAL, terminal_path=(start, end), revision=4)
    hop = PhysicalConnectionHop(id="hop-stable-001", from_terminal=start, to_terminal=end, carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id, revision=3, lifecycle_status="INSTALLED")
    inventory = InstrumentationWiringInventory(cables=(cable,), cores=(core,), connection_hops=(hop,))
    payload = serialize_instrumentation_wiring(inventory)
    assert payload["schema"] == 4
    assert "geometry" not in payload
    restored = deserialize_instrumentation_wiring(payload)
    assert restored == inventory
    assert restored.connection_hops[0].id == "hop-stable-001"
    assert restored.cores[0].revision == 4


def test_schema_seven_migration_preserves_legacy_paths_without_fabricating_hop_ids():
    source = {"schema": 7, "instrumentation_wiring": {"schema": 2, "cables": [], "cores": [], "panel_wires": [], "signals": [], "signal_bindings": [], "tag_policy": []}}
    migrated = _ProjectSchema7To8().migrate(source)
    assert migrated["schema"] == 8
    assert migrated["instrumentation_wiring"]["schema"] == 3
    assert migrated["instrumentation_wiring"]["connection_hops"] == []
    assert source["instrumentation_wiring"]["schema"] == 2


def test_schema_eight_migration_leaves_channel_association_unset_without_inference():
    source = {
        "schema": 8,
        "instrumentation_wiring": {
            "schema": 3,
            "cables": [], "cores": [], "panel_wires": [],
            "signals": [{
                "id": "sig-1", "tag": "IA", "description": "Phase A current",
                "kind": "CURRENT", "unit": "A", "phase": "A",
            }],
            "signal_bindings": [], "tag_policy": [], "connection_hops": [],
        },
    }
    migrated = _ProjectSchema8To9().migrate(source)
    assert migrated["schema"] == 9
    assert migrated["instrumentation_wiring"]["schema"] == 4
    assert migrated["instrumentation_wiring"]["signals"][0]["measurement_channel_id"] is None
    assert source["instrumentation_wiring"]["signals"][0].get("measurement_channel_id") is None


def test_wiring_codec_round_trips_explicit_measurement_channel_identity():
    signal = SignalDefinition(
        id="signal-with-channel", tag="IA-CH", description="Phase A current",
        kind=SignalKind.CURRENT, unit="A", phase="A",
        measurement_channel_id="measurement-channel-17",
    )
    inventory = InstrumentationWiringInventory(signals=(signal,))
    payload = serialize_instrumentation_wiring(inventory)
    assert payload["signals"][0]["measurement_channel_id"] == "measurement-channel-17"
    assert deserialize_instrumentation_wiring(payload) == inventory


def test_inventory_rejects_two_signals_claiming_one_measurement_channel():
    first = SignalDefinition(
        id="signal-1", tag="IA-1", description="First current",
        kind=SignalKind.CURRENT, unit="A", phase="A",
        measurement_channel_id="channel-shared",
    )
    second = SignalDefinition(
        id="signal-2", tag="IA-2", description="Second current",
        kind=SignalKind.CURRENT, unit="A", phase="A",
        measurement_channel_id="channel-shared",
    )
    with pytest.raises(ValueError, match="only one instrumentation signal"):
        InstrumentationWiringInventory(signals=(first, second))



def test_terminal_block_inventory_round_trips_schema_five_without_losing_point_identity():
    from core.model.instrument_wiring import (
        CableAssembly,
        CableCore,
        InstrumentationWiringInventory,
        TerminalAccessory,
        TerminalAccessoryKind,
        TerminalAccessoryState,
        TerminalBlock,
        TerminalPoint,
        WiringConductorRole,
        WiringTerminalReference,
    )

    block = TerminalBlock(
        id="tb-persist", tag="TB-PERSIST", panel_id="PANEL-2",
        location="MARSHALLING-1", terminal_count=2,
    )
    point = TerminalPoint(
        id="tp-persist", terminal_block_id=block.id,
        terminal_number="10", designation="X10:10",
        manufacturer_designation="10",
    )
    external = WiringTerminalReference(
        equipment_id="CT-1", terminal_role="S1", designation="S1",
    )
    block_terminal = WiringTerminalReference(
        equipment_id=block.id, terminal_role=point.terminal_number,
        designation=point.designation, terminal_point_id=point.id,
    )
    cable = CableAssembly(
        id="c-persist", tag="C-PERSIST", service="CT secondary", core_count=1,
    )
    core = CableCore(
        id="cc-persist", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(external, block_terminal),
    )
    accessory = TerminalAccessory(
        id="acc-persist", tag="ACC-PERSIST", terminal_block_id=block.id,
        kind=TerminalAccessoryKind.TEST_DISCONNECT,
        state=TerminalAccessoryState.UNKNOWN,
        terminal_point_ids=(point.id,),
    )
    inventory = InstrumentationWiringInventory(
        cables=(cable,), cores=(core,),
        terminal_blocks=(block,), terminal_points=(point,),
        terminal_accessories=(accessory,),
    )
    payload = serialize_instrumentation_wiring(inventory)
    assert payload["schema"] == 5
    restored = deserialize_instrumentation_wiring(payload)
    assert restored == inventory


def test_schema_four_instrumentation_wiring_remains_readable_after_schema_five_upgrade():
    payload = serialize_instrumentation_wiring(sample_inventory())
    payload["schema"] = 4
    payload.pop("terminal_blocks")
    payload.pop("terminal_points")
    payload.pop("terminal_accessories")
    for core in payload["cores"]:
        for terminal in core.get("terminal_path", []):
            terminal.pop("terminal_point_id", None)
    for wire in payload["panel_wires"]:
        for terminal in wire.get("terminal_path", []):
            terminal.pop("terminal_point_id", None)
    for hop in payload["connection_hops"]:
        hop["from_terminal"].pop("terminal_point_id", None)
        hop["to_terminal"].pop("terminal_point_id", None)

    assert deserialize_instrumentation_wiring(payload) == sample_inventory()
