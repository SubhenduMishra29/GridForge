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

def test_schema_six_migration_adds_empty_explicit_tag_policy():
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


def test_project_tag_policy_allocates_without_assuming_a_standard_prefix():
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


def test_application_tag_allocation_is_committed_only_by_inventory_command():
    service = InstrumentationWiringService()
    context = ProjectContext(project_id="project-1", name="Test", path=None)
    network = FakeNetwork()
    policy = WiringTagPolicy(series=(
        WiringTagSeries(record_kind="CABLE", prefix="CAB", separator="-", minimum_digits=3),
    ))
    inventory = InstrumentationWiringInventory(tag_policy=policy)
    service.activate(context, inventory, network=network, generation=1)
    tag, candidate = service.allocate_tag("CABLE")
    assert tag == "CAB-001"
    assert service.inventory is inventory
    command = service.create_replace_command(candidate)
    transaction = Transaction()
    result = service.execute(command, SimpleNamespace(network=network), transaction)
    assert result.success is True
    assert service.inventory.tag_policy.series[0].next_number == 2
    transaction.rollback()
    assert service.inventory is inventory
