"""Canonical instrumentation wiring persistence and lifecycle contracts."""

import pytest
from types import SimpleNamespace

from core.application.transaction import Transaction

from core.application.project import ProjectContext
from core.application.services.instrumentation_wiring_service import InstrumentationWiringService
from core.model.instrument_wiring import (
    CableAssembly, CableCore, CarrierKind, InstrumentationWiringInventory,
    SignalCarrierBinding, SignalDefinition, SignalKind, WiringConductorRole,
    SignalEndpointBinding, SignalEndpointKind, SignalEndpointReference,
    WiringTagSeries, WiringTagPolicy, WiringTerminalReference,
    TerminalBlock, TerminalPoint, TerminalAccessory, TerminalAccessoryKind, TerminalAccessoryState,
    CTSecondaryCircuit, CTSecondaryCircuitState,
    PTSecondaryCircuit, PTSecondaryCircuitState, PTSecondaryPolarity, PTSecondaryGrounding,
)
from core.persistence.instrument_wiring_serializer import (
    InstrumentationWiringSerializationError,
    deserialize_instrumentation_wiring,
    serialize_instrumentation_wiring,
)
from core.persistence.migration import _ProjectSchema5To6, _ProjectSchema6To7


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
        source_channel_id="channel-1",
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



def test_signal_endpoint_bindings_round_trip_for_all_endpoint_kinds():
    inventory = sample_inventory()
    endpoints = (
        SignalEndpointBinding(
            id="channel-binding", signal_id="signal-id",
            endpoint=SignalEndpointReference(
                kind=SignalEndpointKind.MEASUREMENT_CHANNEL,
                endpoint_id="channel-1",
            ),
        ),
        SignalEndpointBinding(
            id="control-binding", signal_id="signal-id",
            endpoint=SignalEndpointReference(
                kind=SignalEndpointKind.CONTROL_INPUT,
                endpoint_id="component-1", owner_id="control-1", port="PV",
            ),
        ),
        SignalEndpointBinding(
            id="protection-binding", signal_id="signal-id",
            endpoint=SignalEndpointReference(
                kind=SignalEndpointKind.PROTECTION_INPUT,
                endpoint_id="protection-measurement-binding",
                owner_id="protection-element-1", port="IA",
            ),
        ),
    )
    expected = InstrumentationWiringInventory(
        cables=inventory.cables, cores=inventory.cores,
        signals=inventory.signals, signal_bindings=inventory.signal_bindings,
        endpoint_bindings=endpoints,
    )
    payload = serialize_instrumentation_wiring(expected)
    assert payload["schema"] == 7
    assert len(payload["endpoint_bindings"]) == 3
    assert deserialize_instrumentation_wiring(payload) == expected


def test_schema_two_wiring_inventory_remains_readable_without_inferred_endpoints():
    payload = serialize_instrumentation_wiring(sample_inventory())
    payload["schema"] = 2
    payload.pop("endpoint_bindings")
    payload.pop("terminal_blocks")
    payload.pop("terminal_points")
    payload.pop("terminal_accessories")
    payload.pop("ct_secondary_circuits")
    payload.pop("pt_secondary_circuits")
    for binding in payload["signal_bindings"]:
        binding.pop("source_channel_id")
    restored = deserialize_instrumentation_wiring(payload)
    inventory = sample_inventory()
    expected = InstrumentationWiringInventory(
        cables=inventory.cables,
        cores=inventory.cores,
        signals=inventory.signals,
        signal_bindings=tuple(
            SignalCarrierBinding(
                id=item.id,
                signal_id=item.signal_id,
                carrier_kind=item.carrier_kind,
                carrier_id=item.carrier_id,
                direction=item.direction,
            )
            for item in inventory.signal_bindings
        ),
    )
    assert restored == expected
    assert restored.endpoint_bindings == ()


def test_schema_three_wiring_inventory_remains_readable_without_channel_ownership():
    inventory = sample_inventory()
    payload = serialize_instrumentation_wiring(inventory)
    payload["schema"] = 3
    payload.pop("terminal_blocks")
    payload.pop("terminal_points")
    payload.pop("terminal_accessories")
    for binding in payload["signal_bindings"]:
        binding.pop("source_channel_id")
    restored = deserialize_instrumentation_wiring(payload)
    assert restored == InstrumentationWiringInventory(
        cables=inventory.cables,
        cores=inventory.cores,
        signals=inventory.signals,
        signal_bindings=tuple(
            SignalCarrierBinding(
                id=item.id,
                signal_id=item.signal_id,
                carrier_kind=item.carrier_kind,
                carrier_id=item.carrier_id,
                direction=item.direction,
                source_channel_id=None,
            )
            for item in inventory.signal_bindings
        ),
    )


def test_wiring_service_adds_and_reads_signal_endpoint_binding():
    service = InstrumentationWiringService()
    network = FakeNetwork()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    signal = SignalDefinition(
        id="signal-1", tag="SIG-1", description="Pressure",
        kind=SignalKind.ANALOG, unit="bar",
    )
    service.activate(
        context,
        InstrumentationWiringInventory(signals=(signal,)),
        network=network,
        generation=2,
    )
    binding = SignalEndpointBinding(
        id="endpoint-binding-1", signal_id=signal.id,
        endpoint=SignalEndpointReference(
            kind=SignalEndpointKind.MEASUREMENT_CHANNEL,
            endpoint_id="channel-1",
        ),
    )
    command = service.create_add_record_command(binding)
    _apply_wiring_command(service, network, command)
    read_model = service.read_model()
    assert read_model.endpoint_bindings[0]["id"] == binding.id
    assert read_model.endpoint_bindings[0]["endpoint"]["endpoint_id"] == "channel-1"



def test_endpoint_sink_terminal_round_trips_without_losing_designation():
    from core.model.instrument_wiring import WiringTerminalReference

    base = sample_inventory()
    endpoint = SignalEndpointBinding(
        id="endpoint-binding-id",
        signal_id="signal-id",
        endpoint=SignalEndpointReference(
            kind=SignalEndpointKind.CONTROL_INPUT,
            endpoint_id="component-id",
            owner_id="control-id",
            port="PV",
            physical_terminal=WiringTerminalReference(
                "PLC-101", "AI-01+", "AI-01+",
            ),
        ),
        direction="SOURCE_TO_SINK",
    )
    inventory = InstrumentationWiringInventory(
        cables=base.cables,
        cores=base.cores,
        signals=base.signals,
        signal_bindings=base.signal_bindings,
        endpoint_bindings=(endpoint,),
    )
    payload = serialize_instrumentation_wiring(inventory)
    assert payload["endpoint_bindings"][0]["endpoint"]["physical_terminal"] == {
        "equipment_id": "PLC-101",
        "terminal_role": "AI-01+",
        "designation": "AI-01+",
        "terminal_point_id": None,
    }
    assert deserialize_instrumentation_wiring(payload) == inventory



def test_schema_four_wiring_inventory_remains_readable_without_terminal_records():
    inventory = sample_inventory()
    payload = serialize_instrumentation_wiring(inventory)
    payload["schema"] = 4
    payload.pop("terminal_blocks")
    payload.pop("terminal_points")
    payload.pop("terminal_accessories")
    restored = deserialize_instrumentation_wiring(payload)
    assert restored == inventory


def test_terminal_block_points_and_accessory_state_round_trip_in_schema_seven():
    base = sample_inventory()
    block = TerminalBlock(
        id="tb-id", tag="TB-101", panel_id="PANEL-1",
        location="MCC-1 / marshalling section", terminal_count=4,
        terminal_type="feed-through", manufacturer="approved make",
        part_number="TB-4MM",
    )
    point_a = TerminalPoint(
        id="tb-point-a", terminal_block_id=block.id,
        terminal_number="1", designation="1A",
        manufacturer_designation="1A", function="FEED_THROUGH",
    )
    point_b = TerminalPoint(
        id="tb-point-b", terminal_block_id=block.id,
        terminal_number="2", designation="2A",
        manufacturer_designation="2A", function="FEED_THROUGH",
    )
    accessory = TerminalAccessory(
        id="tb-link-id", tag="TB-101-L1", terminal_block_id=block.id,
        kind=TerminalAccessoryKind.TEST_DISCONNECT,
        state=TerminalAccessoryState.CLOSED,
        terminal_point_ids=(point_a.id, point_b.id),
        conductive_pairs=((point_a.id, point_b.id),),
    )
    terminal_cable = CableAssembly(
        id="terminal-cable-id", tag="C-TB-101", service="terminal bridge route",
        core_count=1,
    )
    terminal_core = CableCore(
        id="terminal-core-id", cable_id=terminal_cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(
            WiringTerminalReference(block.id, "1", "1A", point_a.id),
            WiringTerminalReference(block.id, "2", "2A", point_b.id),
        ),
    )
    inventory = InstrumentationWiringInventory(
        cables=base.cables + (terminal_cable,),
        cores=base.cores + (terminal_core,), signals=base.signals,
        signal_bindings=base.signal_bindings,
        terminal_blocks=(block,), terminal_points=(point_a, point_b),
        terminal_accessories=(accessory,),
    )
    payload = serialize_instrumentation_wiring(inventory)
    assert payload["schema"] == 5
    assert payload["terminal_accessories"][0]["conductive_pairs"] == [["tb-point-a", "tb-point-b"]]
    assert payload["cores"][-1]["terminal_path"][0]["terminal_point_id"] == "tb-point-a"
    assert deserialize_instrumentation_wiring(payload) == inventory


def test_inventory_rejects_terminal_block_reference_without_stable_point_identity():
    block = TerminalBlock(
        id="TB-101", tag="TB-101", panel_id="PANEL-1",
        location="Marshalling", terminal_count=2,
    )
    point = TerminalPoint(
        id="tb-point-1", terminal_block_id=block.id,
        terminal_number="1", designation="1",
    )
    cable = CableAssembly(id="cable", tag="C-1", service="instrument", core_count=1)
    with pytest.raises(ValueError, match="must include terminal_point_id"):
        InstrumentationWiringInventory(
            cables=(cable,), terminal_blocks=(block,), terminal_points=(point,),
            cores=(CableCore(
                id="core", cable_id=cable.id, core_number=1,
                role=WiringConductorRole.SIGNAL,
                terminal_path=(
                    WiringTerminalReference("TB-101", "1", "1"),
                    WiringTerminalReference("PLC-101", "AI1", "AI1"),
                ),
            ),),
        )


def test_application_service_adds_and_reads_terminal_block_points_and_accessories():
    service = InstrumentationWiringService()
    network = FakeNetwork()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    service.activate(context, InstrumentationWiringInventory(), network=network, generation=1)

    block = TerminalBlock(
        id="TB-101", tag="TB-101", panel_id="PANEL-1",
        location="Marshalling cabinet", terminal_count=2,
    )
    _apply_wiring_command(service, network, service.create_add_record_command(block))
    point_a = TerminalPoint(
        id="TB-101-1", terminal_block_id=block.id,
        terminal_number="1", designation="1A",
    )
    point_b = TerminalPoint(
        id="TB-101-2", terminal_block_id=block.id,
        terminal_number="2", designation="2A",
    )
    _apply_wiring_command(service, network, service.create_add_record_command(point_a))
    _apply_wiring_command(service, network, service.create_add_record_command(point_b))
    cable = CableAssembly(
        id="C-TB-101-ID", tag="C-TB-101", service="terminal test circuit",
        core_count=1,
    )
    _apply_wiring_command(service, network, service.create_add_record_command(cable))
    core = CableCore(
        id="C-TB-101-CORE-1", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(
            WiringTerminalReference(block.id, "1", "1A", point_a.id),
            WiringTerminalReference(block.id, "2", "2A", point_b.id),
        ),
    )
    _apply_wiring_command(service, network, service.create_add_record_command(core))
    accessory = TerminalAccessory(
        id="TB-101-L1", tag="TB-101-L1", terminal_block_id=block.id,
        kind=TerminalAccessoryKind.TEST_DISCONNECT,
        state=TerminalAccessoryState.CLOSED,
        terminal_point_ids=(point_a.id, point_b.id),
        conductive_pairs=((point_a.id, point_b.id),),
    )
    _apply_wiring_command(service, network, service.create_add_record_command(accessory))

    read_model = service.read_model()
    assert read_model.terminal_blocks[0]["tag"] == "TB-101"
    assert {item["id"] for item in read_model.terminal_points} == {"TB-101-1", "TB-101-2"}
    assert read_model.terminal_accessories[0]["state"] == "CLOSED"


def test_schema_four_endpoint_sink_reference_remains_readable_without_point_id():
    base = sample_inventory()
    endpoint = SignalEndpointBinding(
        id="endpoint-binding-id", signal_id="signal-id",
        endpoint=SignalEndpointReference(
            kind=SignalEndpointKind.CONTROL_INPUT,
            endpoint_id="component-id", owner_id="control-id", port="PV",
            physical_terminal=WiringTerminalReference("PLC-101", "AI-01+", "AI-01+"),
        ),
    )
    inventory = InstrumentationWiringInventory(
        cables=base.cables, cores=base.cores, signals=base.signals,
        signal_bindings=base.signal_bindings, endpoint_bindings=(endpoint,),
    )
    payload = serialize_instrumentation_wiring(inventory)
    payload["schema"] = 4
    payload.pop("terminal_blocks")
    payload.pop("terminal_points")
    payload.pop("terminal_accessories")
    payload["endpoint_bindings"][0]["endpoint"]["physical_terminal"].pop("terminal_point_id")
    assert deserialize_instrumentation_wiring(payload) == inventory



def test_ct_secondary_circuit_codec_round_trips_explicit_shorting_arrangement():
    base = sample_inventory()
    block = TerminalBlock(
        id="ct-tb", tag="TB-CT-1", panel_id="PANEL-1",
        location="Protection marshalling", terminal_count=2,
    )
    point_s1 = TerminalPoint(
        id="ct-point-s1", terminal_block_id=block.id,
        terminal_number="1", designation="S1-LINK",
    )
    point_s2 = TerminalPoint(
        id="ct-point-s2", terminal_block_id=block.id,
        terminal_number="2", designation="S2-LINK",
    )
    shorting = TerminalAccessory(
        id="ct-short", tag="TB-CT-1-SHORT", terminal_block_id=block.id,
        kind=TerminalAccessoryKind.SHORTING_LINK,
        state=TerminalAccessoryState.CLOSED,
        terminal_point_ids=(point_s1.id, point_s2.id),
        conductive_pairs=((point_s1.id, point_s2.id),),
    )
    s1 = WiringTerminalReference("CT-1", "S1", "S1")
    s2 = WiringTerminalReference("CT-1", "S2", "S2")
    cable = CableAssembly(id="ct-cable", tag="C-CT-1", service="CT secondary", core_count=2)
    core_s1 = CableCore(
        id="ct-core-s1", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(s1, WiringTerminalReference(block.id, "1", "S1-LINK", point_s1.id)),
    )
    core_s2 = CableCore(
        id="ct-core-s2", cable_id=cable.id, core_number=2,
        role=WiringConductorRole.RETURN,
        terminal_path=(s2, WiringTerminalReference(block.id, "2", "S2-LINK", point_s2.id)),
    )
    circuit = CTSecondaryCircuit(
        id="ct-circuit-a", ct_id="CT-1", phase="A",
        s1_terminal=s1, s2_terminal=s2,
        s1_carrier_ids=(core_s1.id,), s2_carrier_ids=(core_s2.id,),
        shorting_accessory_id=shorting.id,
        shorting_s1_terminal_point_id=point_s1.id,
        shorting_s2_terminal_point_id=point_s2.id,
        secondary_state=CTSecondaryCircuitState.OPEN,
    )
    inventory = InstrumentationWiringInventory(
        cables=base.cables + (cable,),
        cores=base.cores + (core_s1, core_s2),
        signals=base.signals, signal_bindings=base.signal_bindings,
        terminal_blocks=(block,), terminal_points=(point_s1, point_s2),
        terminal_accessories=(shorting,), ct_secondary_circuits=(circuit,),
    )
    payload = serialize_instrumentation_wiring(inventory)
    assert payload["schema"] == 6
    assert payload["ct_secondary_circuits"][0]["s1_terminal"]["terminal_role"] == "S1"
    assert deserialize_instrumentation_wiring(payload) == inventory


def test_schema_five_wiring_inventory_remains_readable_after_schema_seven():
    inventory = sample_inventory()
    payload = serialize_instrumentation_wiring(inventory)
    payload["schema"] = 5
    payload.pop("ct_secondary_circuits")
    assert deserialize_instrumentation_wiring(payload) == inventory



def test_in_service_ct_open_secondary_requires_closed_explicit_shorting_link():
    from types import SimpleNamespace

    base = sample_inventory()
    block = TerminalBlock(
        id="ct-tb", tag="TB-CT-1", panel_id="PANEL-1",
        location="Protection marshalling", terminal_count=2,
    )
    point_s1 = TerminalPoint(id="ct-point-s1", terminal_block_id=block.id, terminal_number="1", designation="S1")
    point_s2 = TerminalPoint(id="ct-point-s2", terminal_block_id=block.id, terminal_number="2", designation="S2")
    shorting = TerminalAccessory(
        id="ct-short", tag="TB-CT-1-SHORT", terminal_block_id=block.id,
        kind=TerminalAccessoryKind.SHORTING_LINK,
        state=TerminalAccessoryState.OPEN,
        terminal_point_ids=(point_s1.id, point_s2.id),
        conductive_pairs=((point_s1.id, point_s2.id),),
    )
    s1 = WiringTerminalReference("CT-1", "S1", "S1")
    s2 = WiringTerminalReference("CT-1", "S2", "S2")
    cable = CableAssembly(id="ct-cable", tag="C-CT-1", service="CT secondary", core_count=2)
    core_s1 = CableCore(id="ct-core-s1", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL, terminal_path=(s1, WiringTerminalReference(block.id, "1", "S1", point_s1.id)))
    core_s2 = CableCore(id="ct-core-s2", cable_id=cable.id, core_number=2,
        role=WiringConductorRole.RETURN, terminal_path=(s2, WiringTerminalReference(block.id, "2", "S2", point_s2.id)))
    circuit = CTSecondaryCircuit(
        id="ct-circuit-a", ct_id="CT-1", phase="A",
        s1_terminal=s1, s2_terminal=s2,
        s1_carrier_ids=(core_s1.id,), s2_carrier_ids=(core_s2.id,),
        shorting_accessory_id=shorting.id,
        shorting_s1_terminal_point_id=point_s1.id,
        shorting_s2_terminal_point_id=point_s2.id,
        secondary_state=CTSecondaryCircuitState.OPEN,
    )
    inventory = InstrumentationWiringInventory(
        cables=base.cables + (cable,), cores=base.cores + (core_s1, core_s2),
        signals=base.signals, signal_bindings=base.signal_bindings,
        terminal_blocks=(block,), terminal_points=(point_s1, point_s2),
        terminal_accessories=(shorting,), ct_secondary_circuits=(circuit,),
    )
    network = SimpleNamespace(get_by_identity=lambda identity: SimpleNamespace(
        id=identity, element_type="CT", in_service=True,
    ))
    with pytest.raises(ValueError, match="without a CLOSED"):
        InstrumentationWiringService._validate_ct_secondary_circuits(network, inventory)

    from dataclasses import replace
    closed_link = replace(shorting, state=TerminalAccessoryState.CLOSED)
    normal_service_circuit = replace(circuit, secondary_state=CTSecondaryCircuitState.CLOSED)
    normal_service_inventory = replace(
        inventory,
        terminal_accessories=(closed_link,),
        ct_secondary_circuits=(normal_service_circuit,),
    )
    with pytest.raises(ValueError, match="requires the shorting link to be explicitly OPEN"):
        InstrumentationWiringService._validate_ct_secondary_circuits(
            network, normal_service_inventory
        )


def _pt_secondary_inventory(*, fuse_state=TerminalAccessoryState.CLOSED):
    base = sample_inventory()
    block = TerminalBlock(id="pt-tb", tag="TB-PT-1", panel_id="PANEL-1", location="PT marshalling", terminal_count=4)
    points = (
        TerminalPoint(id="pt-p1", terminal_block_id=block.id, terminal_number="1", designation="X1-IN"),
        TerminalPoint(id="pt-p2", terminal_block_id=block.id, terminal_number="2", designation="X1-OUT"),
        TerminalPoint(id="pt-p3", terminal_block_id=block.id, terminal_number="3", designation="X2-IN"),
        TerminalPoint(id="pt-p4", terminal_block_id=block.id, terminal_number="4", designation="X2-OUT"),
    )
    fuse = TerminalAccessory(
        id="pt-fuse", tag="FU-PT-1", terminal_block_id=block.id,
        kind=TerminalAccessoryKind.FUSE_LINK, state=fuse_state,
        terminal_point_ids=("pt-p1", "pt-p2"),
        conductive_pairs=(("pt-p1", "pt-p2"),),
    )
    cable = CableAssembly(id="pt-cable", tag="C-PT-1", service="PT secondary", core_count=2)
    output = WiringTerminalReference("PT-1", "X1", "X1")
    returned = WiringTerminalReference("PT-1", "X2", "X2")
    core_out = CableCore(
        id="pt-core-out", cable_id=cable.id, core_number=1, role=WiringConductorRole.SIGNAL,
        terminal_path=(output, WiringTerminalReference(block.id, "1", "X1-IN", "pt-p1"), WiringTerminalReference(block.id, "2", "X1-OUT", "pt-p2")),
    )
    core_return = CableCore(
        id="pt-core-return", cable_id=cable.id, core_number=2, role=WiringConductorRole.RETURN,
        terminal_path=(returned, WiringTerminalReference(block.id, "3", "X2-IN", "pt-p3"), WiringTerminalReference(block.id, "4", "X2-OUT", "pt-p4")),
    )
    circuit = PTSecondaryCircuit(
        id="pt-circuit-a", instrument_id="PT-1", instrument_kind="PT", phase="A",
        output_terminal=output, return_terminal=returned,
        output_carrier_ids=(core_out.id,), return_carrier_ids=(core_return.id,),
        fuse_accessory_ids=(fuse.id,),
        grounding=PTSecondaryGrounding.UNGROUNDED_BY_DESIGN,
        polarity=PTSecondaryPolarity.NORMAL,
        secondary_state=PTSecondaryCircuitState.CLOSED,
    )
    return InstrumentationWiringInventory(
        cables=base.cables + (cable,), cores=base.cores + (core_out, core_return),
        signals=base.signals, signal_bindings=base.signal_bindings,
        terminal_blocks=(block,), terminal_points=points, terminal_accessories=(fuse,),
        pt_secondary_circuits=(circuit,),
    )


def test_pt_secondary_schema_seven_round_trip_preserves_terminals_fusing_and_grounding():
    inventory = _pt_secondary_inventory()
    payload = serialize_instrumentation_wiring(inventory)
    assert payload["schema"] == 7
    circuit = payload["pt_secondary_circuits"][0]
    assert circuit["output_terminal"]["designation"] == "X1"
    assert circuit["fuse_accessory_ids"] == ["pt-fuse"]
    assert circuit["grounding"] == "UNGROUNDED_BY_DESIGN"
    assert deserialize_instrumentation_wiring(payload) == inventory


def test_pt_secondary_fuse_must_be_physically_on_output_route():
    inventory = _pt_secondary_inventory()
    circuit = inventory.pt_secondary_circuits[0]
    detached = TerminalAccessory(
        id="detached-fuse", tag="FU-PT-DETACHED", terminal_block_id="pt-tb",
        kind=TerminalAccessoryKind.FUSE_LINK, state=TerminalAccessoryState.CLOSED,
        terminal_point_ids=("pt-p3", "pt-p4"),
        conductive_pairs=(("pt-p3", "pt-p4"),),
    )
    with pytest.raises(ValueError, match="not physically located on the declared output carrier route"):
        replace(inventory, terminal_accessories=(detached,), pt_secondary_circuits=(replace(circuit, fuse_accessory_ids=(detached.id,)),))


def test_in_service_pt_rejects_open_secondary_fuse_and_unknown_grounding():
    from dataclasses import replace
    from types import SimpleNamespace
    inventory = _pt_secondary_inventory(fuse_state=TerminalAccessoryState.OPEN)
    network = SimpleNamespace(get_by_identity=lambda identity: SimpleNamespace(
        id=identity, element_type="PT", in_service=True,
    ))
    with pytest.raises(ValueError, match="fuse link that is not explicitly CLOSED"):
        InstrumentationWiringService._validate_pt_secondary_circuits(network, inventory)
    fuse_closed = replace(inventory.terminal_accessories[0], state=TerminalAccessoryState.CLOSED)
    circuit_unknown_ground = replace(inventory.pt_secondary_circuits[0], grounding=PTSecondaryGrounding.UNKNOWN)
    unknown_inventory = replace(inventory, terminal_accessories=(fuse_closed,), pt_secondary_circuits=(circuit_unknown_ground,))
    with pytest.raises(ValueError, match="requires an explicit grounded or ungrounded-by-design"):
        InstrumentationWiringService._validate_pt_secondary_circuits(network, unknown_inventory)
