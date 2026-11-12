"""SLD projection contracts for canonical physical instrumentation wiring."""

import pytest

from core.application.read_models import InstrumentationWiringReadModel
from ui.sld.instrumentation_wiring_projection import SLDInstrumentationWiringAdapter
from ui.sld.sld_model import SLDModel, SLDNode


def _read_model(*, core_path=None, panel_wires=(), extra_binding=True):
    terminal_path = core_path if core_path is not None else (
        {"equipment_id": "CT-1", "terminal_role": "S1", "designation": "X1:1"},
        {"equipment_id": "TB-1", "terminal_role": "1", "designation": "X2:1"},
        {"equipment_id": "RELAY-1", "terminal_role": "IA", "designation": "X3:1"},
    )
    return InstrumentationWiringReadModel(
        project_id="project-1",
        activation_generation=3,
        cables=({"id": "cable-1", "tag": "IC-001", "service": "CT secondary", "core_count": 2},),
        cores=({
            "id": "core-1", "cable_id": "cable-1", "core_number": 1,
            "role": "SIGNAL", "core_tag": "IC-001/1",
            "terminal_path": terminal_path,
        },),
        panel_wires=panel_wires,
        signals=({"id": "signal-1", "tag": "IA_A", "description": "Phase A current", "kind": "CURRENT"},),
        signal_bindings=(
            ({"id": "binding-1", "signal_id": "signal-1", "carrier_kind": "CABLE_CORE", "carrier_id": "core-1", "direction": "SOURCE_TO_SINK"},)
            if extra_binding else ()
        ),
        tag_policy=(),
    )


def _sld_model():
    model = SLDModel()
    model.add_node(SLDNode(node_id="node-ct", equipment_id="CT-1"))
    model.add_node(SLDNode(node_id="node-tb", equipment_id="TB-1"))
    model.add_node(SLDNode(node_id="node-relay", equipment_id="RELAY-1"))
    return model


def test_physical_core_projects_each_terminal_hop_without_mutating_document():
    model = _sld_model()
    before = (model.node_count, model.connection_count)
    projection = SLDInstrumentationWiringAdapter().project(_read_model(), model)

    assert projection.project_id == "project-1"
    assert projection.activation_generation == 3
    assert len(projection.records) == 1
    record = projection.records[0]
    assert record.complete is True
    assert record.carrier_tag == "IC-001/1"
    assert len(record.segments) == 2
    assert record.segments[0].source.equipment_id == "CT-1"
    assert record.segments[0].source.terminal_role == "S1"
    assert record.segments[0].target.equipment_id == "TB-1"
    assert record.segments[1].source.equipment_id == "TB-1"
    assert record.segments[1].target.equipment_id == "RELAY-1"
    assert record.segments[1].signal_tags == ("IA_A",)
    assert (model.node_count, model.connection_count) == before


def test_missing_sld_equipment_node_marks_whole_carrier_unresolved():
    model = SLDModel()
    model.add_node(SLDNode(node_id="node-ct", equipment_id="CT-1"))
    projection = SLDInstrumentationWiringAdapter().project(_read_model(), model)

    record = projection.records[0]
    assert record.complete is False
    assert record.segments == ()
    assert any("TB-1/1" in item for item in record.diagnostics)
    assert any("RELAY-1/IA" in item for item in record.diagnostics)


def test_duplicate_sld_nodes_for_same_equipment_are_not_guessed():
    model = _sld_model()
    model.add_node(SLDNode(node_id="duplicate-relay", equipment_id="RELAY-1"))
    projection = SLDInstrumentationWiringAdapter().project(_read_model(), model)

    record = projection.records[0]
    assert record.complete is False
    assert record.segments == ()
    assert any("ambiguous" in item for item in record.diagnostics)


def test_carrier_without_terminal_path_is_not_drawable():
    model = _sld_model()
    projection = SLDInstrumentationWiringAdapter().project(
        _read_model(core_path=()), model
    )
    record = projection.records[0]
    assert record.complete is False
    assert record.segments == ()
    assert "No physical terminal path" in record.diagnostics[0]


def test_adapter_rejects_wrong_boundary_types():
    with pytest.raises(TypeError):
        SLDInstrumentationWiringAdapter().project({}, _sld_model())
    with pytest.raises(TypeError):
        SLDInstrumentationWiringAdapter().project(_read_model(), object())

def test_panel_wire_projects_with_its_own_identity_and_carrier_kind():
    panel_wire = {
        "id": "wire-1", "tag": "W-001", "role": "RETURN",
        "terminal_path": (
            {"equipment_id": "TB-1", "terminal_role": "2", "designation": "X2:2"},
            {"equipment_id": "RELAY-1", "terminal_role": "COM", "designation": "X3:2"},
        ),
    }
    read_model = _read_model(panel_wires=(panel_wire,))
    projection = SLDInstrumentationWiringAdapter().project(read_model, _sld_model())

    wire_record = next(item for item in projection.records if item.carrier_kind == "PANEL_WIRE")
    assert wire_record.complete is True
    assert wire_record.carrier_id == "wire-1"
    assert wire_record.segments[0].carrier_kind == "PANEL_WIRE"
    assert wire_record.segments[0].carrier_tag == "W-001"
    assert wire_record.segments[0].cable_id is None

def test_engineer_owned_route_override_is_attached_to_stable_carrier_segment():
    route = {
        "routing_mode": "manual",
        "ownership": "engineer",
        "points": [[12.0, 18.0], [42.0, 18.0]],
    }
    projection = SLDInstrumentationWiringAdapter().project(
        _read_model(),
        _sld_model(),
        route_overrides={"CABLE_CORE:core-1:1": route},
    )

    assert projection.records[0].segments[0].route.ownership == "engineer"
    assert projection.records[0].segments[0].route.points == (
        (12.0, 18.0), (42.0, 18.0),
    )
    assert projection.records[0].segments[1].route.ownership == "auto"
