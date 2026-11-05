"""Typed transient result archive round-trip and schema-compatibility contracts."""

import hashlib
import json
from uuid import uuid4

import numpy as np
import pytest

from core.application.revision import ProjectRevision
from core.application.study import StudyResult
from core.application.read_service import StudyReadService
from core.persistence.study_result_archive import (
    ARCHIVE_FORMAT,
    StudyResultArchive,
    StudyResultArchiveError,
    _canonical_json,
)
from core.solver.dynamics.events import EventExecution, EventTransition
from core.solver.dynamics.dae_solver import AlgebraicNetworkSolution
from core.solver.dynamics.transient_stability import TransientDiscontinuity, TransientStabilityResult


def _transient_result() -> TransientStabilityResult:
    event = EventExecution(
        event_id="GEN1-CB-OPEN",
        event_type="breaker_open",
        time=1.0,
        scheduled_time=1.0,
        dispatch_time=1.0000000002,
        priority=5,
        description="Generator breaker trip",
        metadata={
            "breaker_id": "CB-GEN1",
            "machine_ids": ("GEN-1",),
            "machine_connection_paths": {"GEN-1": ("CB-GEN1",)},
        },
        status="succeeded",
        result={
            "transition_type": "breaker_open",
            "switch_id": "CB-GEN1",
            "pre_event_revision": 7,
            "post_event_revision": 8,
            "machine_transitions": {
                "GEN-1": {
                    "connected_before": True,
                    "connected_after": False,
                    "switching_path": ("CB-GEN1",),
                }
            },
        },
        pre_event_revision=7,
        post_event_revision=8,
        post_event_re_evaluation_status="succeeded",
    )
    failed_event = EventExecution(
        event_id="FAULT-CLEAR-FAILED",
        event_type="fault_clear",
        time=1.5,
        scheduled_time=1.5,
        dispatch_time=1.5000000001,
        status="failed",
        failure_type="ValueError",
        failure_message="No active fault is available to clear.",
        pre_event_revision=8,
        post_event_revision=8,
    )
    quality_pre = AlgebraicNetworkSolution(
        bus_voltages={"BUS-GEN1": 1.0 + 0.0j},
        status="UNVERIFIED",
        accepted=True,
        quality_verified=False,
        solver_name="archive-test",
        bus_ids=("BUS-GEN1",),
        topology_revision=7,
        simulation_time=1.0,
    )
    quality_post = AlgebraicNetworkSolution(
        bus_voltages={"BUS-GEN1": 0.0 + 0.0j},
        status="UNVERIFIED",
        accepted=True,
        quality_verified=False,
        solver_name="archive-test",
        bus_ids=("BUS-GEN1",),
        topology_revision=8,
        simulation_time=1.0,
    )
    discontinuity = TransientDiscontinuity(
        time=1.0,
        event_ids=(event.event_id,),
        event_executions=(event,),
        pre_state=np.asarray([0.1, 0.0]),
        pre_terminal_voltages={"BUS-GEN1": 1.0 + 0.0j},
        pre_electrical_powers={"GEN-1": (1.0, 0.1)},
        pre_algebraic_quality=quality_pre,
        pre_topology_revision=7,
        post_state=np.asarray([0.2, 0.01]),
        post_terminal_voltages={"BUS-GEN1": 0.0 + 0.0j},
        post_electrical_powers={"GEN-1": (0.0, 0.0)},
        post_algebraic_quality=quality_post,
        post_topology_revision=8,
        post_status="succeeded",
    )
    return TransientStabilityResult(
        time=np.asarray([0.0, 1.0], dtype=float),
        states=np.asarray([[0.0, 0.0], [0.2, 0.01]], dtype=float),
        terminal_voltages=(
            {"BUS-GEN1": 1.0 + 0.0j},
            {"BUS-GEN1": 0.0 + 0.0j},
        ),
        electrical_powers=(
            {"GEN-1": (1.0, 0.1)},
            {"GEN-1": (0.0, 0.0)},
        ),
        events=(event, failed_event),
        discontinuities=(discontinuity,),
        provenance={
            "project_id": "project-archive-test",
            "activation_generation": 3,
            "source_revision": (4, 7, 2, 4),
            "machine_connections": {
                "GEN-1": {
                    "switching_path": ("CB-GEN1",),
                    "disconnected_rotor_policy": "continue_with_zero_electrical_power",
                }
            },
            "final_detached_network_revision": 8,
        },
    )


def _study_result(value) -> StudyResult:
    return StudyResult(
        study_id=uuid4(),
        project_id="project-archive-test",
        activation_generation=3,
        source_revision=ProjectRevision(4, 7, 2, 4),
        study_type="transient_stability",
        status="completed",
        value=value,
    )


def test_transient_result_and_event_execution_round_trip_as_canonical_types(tmp_path):
    archive = StudyResultArchive(tmp_path)
    original = _study_result(_transient_result())

    archive.save(original)
    restored = archive.load_latest(
        original.project_id,
        original.activation_generation,
        original.study_id,
    )

    assert restored is not None
    value = restored.result.value
    assert isinstance(value, TransientStabilityResult)
    np.testing.assert_array_equal(value.time, original.value.time)
    np.testing.assert_array_equal(value.states, original.value.states)
    assert value.time.flags.writeable is False
    assert value.states.flags.writeable is False
    assert value.terminal_voltages[0]["BUS-GEN1"] == 1.0 + 0.0j
    assert value.electrical_powers[1]["GEN-1"] == (0.0, 0.0)
    assert value.provenance["final_detached_network_revision"] == 8
    assert len(value.discontinuities) == 1
    boundary = value.discontinuities[0]
    assert isinstance(boundary, TransientDiscontinuity)
    assert boundary.event_ids == ("GEN1-CB-OPEN",)
    assert boundary.pre_terminal_voltages["BUS-GEN1"] == 1.0 + 0.0j
    assert boundary.post_terminal_voltages["BUS-GEN1"] == 0.0 + 0.0j
    assert boundary.pre_topology_revision == 7
    assert boundary.post_topology_revision == 8

    assert len(value.events) == 2
    event = value.events[0]
    assert isinstance(event, EventExecution)
    assert event.scheduled_time == 1.0
    assert event.dispatch_time == 1.0000000002
    assert event.priority == 5
    assert event.status == "succeeded"
    assert event.pre_event_revision == 7
    assert event.post_event_revision == 8
    assert event.post_event_re_evaluation_status == "succeeded"
    assert event.result["machine_transitions"]["GEN-1"]["connected_after"] is False
    assert isinstance(event.transition, EventTransition)
    assert event.transition.transition_type == "breaker_open"
    assert event.transition.target_kind == "switch"
    assert event.transition.target_id == "CB-GEN1"
    assert event.transition.pre_event_revision == 7
    assert event.transition.post_event_revision == 8
    assert event.transition.details["machine_transitions"]["GEN-1"]["connected_after"] is False
    failed_event = value.events[1]
    assert failed_event.event_id == "FAULT-CLEAR-FAILED"
    assert failed_event.status == "failed"
    assert failed_event.failure_type == "ValueError"
    assert failed_event.pre_event_revision == failed_event.post_event_revision == 8
    with pytest.raises(TypeError):
        event.metadata["breaker_id"] = "CHANGED"
    with pytest.raises(TypeError):
        event.result["switch_id"] = "CHANGED"


def test_schema_v3_rejects_unknown_event_execution_fields(tmp_path):
    archive = StudyResultArchive(tmp_path)
    original = _study_result(_transient_result())
    archive.save(original)

    record_path = next(tmp_path.rglob("*.json"))
    envelope = json.loads(record_path.read_text(encoding="utf-8"))
    event_payload = envelope["payload"]["value"]["fields"]["events"][0]
    event_payload["fields"]["unexpected"] = "must fail closed"

    unsigned = {
        key: envelope[key]
        for key in ("format", "schema_version", "record_id", "saved_at", "payload")
    }
    envelope["record_sha256"] = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
    record_path.write_bytes(_canonical_json(envelope))

    with pytest.raises(StudyResultArchiveError, match="EventExecution fields"):
        archive.load_all(original.project_id)



def test_schema_v2_event_execution_migrates_transition_from_legacy_result_mapping(tmp_path):
    archive = StudyResultArchive(tmp_path)
    original = _study_result(_transient_result())
    archive.save(original)

    record_path = next(tmp_path.rglob("*.json"))
    envelope = json.loads(record_path.read_text(encoding="utf-8"))
    envelope["schema_version"] = 2
    for event_payload in envelope["payload"]["value"]["fields"]["events"]:
        event_payload["fields"].pop("transition", None)
    unsigned = {
        key: envelope[key]
        for key in ("format", "schema_version", "record_id", "saved_at", "payload")
    }
    envelope["record_sha256"] = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
    record_path.write_bytes(_canonical_json(envelope))

    restored = archive.load_latest(original.project_id, original.activation_generation, original.study_id)
    assert restored is not None
    event = restored.result.value.events[0]
    assert isinstance(event.transition, EventTransition)
    assert event.transition.target_id == "CB-GEN1"
    assert event.transition.post_event_revision == 8

def test_schema_v1_transient_dataclass_keeps_legacy_mapping_semantics(tmp_path):
    project_id = "project-archive-test"
    study_id = uuid4()
    record_id = uuid4()
    event_class = "core.solver.dynamics.events.EventExecution"
    transient_class = "core.solver.dynamics.transient_stability.TransientStabilityResult"
    legacy_event = {
        "$type": "dataclass",
        "class": event_class,
        "fields": {
            "event_id": "LEGACY-EVENT",
            "event_type": "breaker_open",
            "time": 1.0,
            "result": None,
        },
    }
    legacy_transient = {
        "$type": "dataclass",
        "class": transient_class,
        "fields": {
            "time": [0.0],
            "states": [[0.0, 0.0]],
            "terminal_voltages": [{"BUS-1": {"$type": "complex", "real": 1.0, "imag": 0.0}}],
            "electrical_powers": [{"GEN-1": [1.0, 0.0]}],
            "events": [legacy_event],
            "provenance": {"legacy_schema": 1},
        },
    }
    payload = {
        "study_id": str(study_id),
        "project_id": project_id,
        "activation_generation": 3,
        "source_revision": {
            "model_revision": 4,
            "topology_revision": 7,
            "presentation_revision": 2,
            "persisted_revision": 4,
        },
        "study_type": "transient_stability",
        "status": "completed",
        "value": legacy_transient,
        "message": "",
        "metadata": {},
    }
    unsigned = {
        "format": ARCHIVE_FORMAT,
        "schema_version": 1,
        "record_id": str(record_id),
        "saved_at": "2026-11-02T00:00:00+00:00",
        "payload": payload,
    }
    envelope = {
        **unsigned,
        "record_sha256": hashlib.sha256(_canonical_json(unsigned)).hexdigest(),
    }
    directory = tmp_path / StudyResultArchive._project_key(project_id) / "3"
    directory.mkdir(parents=True)
    path = directory / f"{study_id}.{record_id}.json"
    path.write_bytes(_canonical_json(envelope))

    restored = StudyResultArchive(tmp_path).load_latest(project_id, 3, study_id)
    assert restored is not None
    assert isinstance(restored.result.value, dict)
    assert restored.result.value["$dataclass"] == transient_class
    assert restored.result.value["fields"]["events"][0]["$dataclass"] == event_class
    assert restored.result.value["fields"]["terminal_voltages"][0]["BUS-1"] == 1.0 + 0.0j


def test_empty_transient_state_array_shape_round_trips(tmp_path):
    value = TransientStabilityResult(
        time=np.empty((0,), dtype=float),
        states=np.empty((0, 3), dtype=float),
        terminal_voltages=(),
        electrical_powers=(),
        events=(),
        provenance={"empty_run": True},
    )
    original = _study_result(value)
    archive = StudyResultArchive(tmp_path)
    archive.save(original)

    restored = archive.load_latest(
        original.project_id,
        original.activation_generation,
        original.study_id,
    )

    assert restored is not None
    assert isinstance(restored.result.value, TransientStabilityResult)
    assert restored.result.value.time.shape == (0,)
    assert restored.result.value.states.shape == (0, 3)
    assert restored.result.value.states.flags.writeable is False


def test_schema_v3_rejects_unknown_transient_result_fields(tmp_path):
    archive = StudyResultArchive(tmp_path)
    original = _study_result(_transient_result())
    archive.save(original)

    record_path = next(tmp_path.rglob("*.json"))
    envelope = json.loads(record_path.read_text(encoding="utf-8"))
    envelope["payload"]["value"]["fields"]["unexpected"] = "must fail closed"

    unsigned = {
        key: envelope[key]
        for key in ("format", "schema_version", "record_id", "saved_at", "payload")
    }
    envelope["record_sha256"] = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
    record_path.write_bytes(_canonical_json(envelope))

    with pytest.raises(StudyResultArchiveError, match="TransientStabilityResult fields"):
        archive.load_all(original.project_id)


def test_schema_v3_migrates_transient_result_without_discontinuity_collection(tmp_path):
    archive = StudyResultArchive(tmp_path)
    original = _study_result(_transient_result())
    archive.save(original)
    record_path = next(tmp_path.rglob("*.json"))
    envelope = json.loads(record_path.read_text(encoding="utf-8"))
    envelope["schema_version"] = 3
    envelope["payload"]["value"]["fields"].pop("discontinuities")
    unsigned = {key: envelope[key] for key in ("format", "schema_version", "record_id", "saved_at", "payload")}
    envelope["record_sha256"] = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
    record_path.write_bytes(_canonical_json(envelope))
    restored = archive.load_latest(original.project_id, original.activation_generation, original.study_id)
    assert restored is not None
    assert isinstance(restored.result.value, TransientStabilityResult)
    assert restored.result.value.discontinuities == ()


def test_schema_v4_rejects_unknown_discontinuity_fields(tmp_path):
    archive = StudyResultArchive(tmp_path)
    original = _study_result(_transient_result())
    archive.save(original)
    record_path = next(tmp_path.rglob("*.json"))
    envelope = json.loads(record_path.read_text(encoding="utf-8"))
    discontinuity = envelope["payload"]["value"]["fields"]["discontinuities"][0]
    discontinuity["fields"]["unexpected"] = "must fail closed"
    unsigned = {key: envelope[key] for key in ("format", "schema_version", "record_id", "saved_at", "payload")}
    envelope["record_sha256"] = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
    record_path.write_bytes(_canonical_json(envelope))
    with pytest.raises(StudyResultArchiveError, match="TransientDiscontinuity fields"):
        archive.load_all(original.project_id)


def test_application_transient_presentation_exposes_discontinuity_sides():
    row = _study_result(_transient_result())
    presentation = StudyReadService._transient_presentation(row, historical=False)
    assert presentation is not None
    assert len(presentation.discontinuities) == 1
    boundary = presentation.discontinuities[0]
    assert boundary.time_s == 1.0
    assert boundary.event_ids == ("GEN1-CB-OPEN",)
    assert boundary.pre_terminal_voltages["BUS-GEN1"] == 1.0 + 0.0j
    assert boundary.post_terminal_voltages["BUS-GEN1"] == 0.0 + 0.0j
    assert boundary.pre_topology_revision == 7
    assert boundary.post_topology_revision == 8
