"""Canonical instrumentation wiring persistence and lifecycle contracts."""

import pytest

from core.application.project import ProjectContext
from core.application.services.instrumentation_wiring_service import InstrumentationWiringService
from core.model.instrument_wiring import (
    CableAssembly, CableCore, CarrierKind, InstrumentationWiringInventory,
    SignalCarrierBinding, SignalDefinition, SignalKind, WiringConductorRole,
)
from core.persistence.instrument_wiring_serializer import (
    InstrumentationWiringSerializationError,
    deserialize_instrumentation_wiring,
    serialize_instrumentation_wiring,
)
from core.persistence.migration import _ProjectSchema5To6


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
    service.activate(context, inventory, generation=4)
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
