"""Canvas hand-off for the read-only physical instrumentation wiring projection."""

from core.application.read_models import InstrumentationWiringReadModel
from ui.canvas.sld_canvas_projection import SLDCanvasProjection
from ui.sld.instrumentation_wiring_projection import SLDInstrumentationWiringAdapter
from ui.sld.sld_model import SLDModel, SLDNode


def test_canvas_snapshot_contains_transient_physical_wiring_connections():
    model = SLDModel()
    model.add_node(SLDNode(node_id="ct-node", equipment_id="CT-1"))
    model.add_node(SLDNode(node_id="tb-node", equipment_id="TB-1"))
    read_model = InstrumentationWiringReadModel(
        project_id="project-1",
        activation_generation=2,
        cables=({"id": "cable-1", "tag": "IC-001", "service": "CT secondary", "core_count": 1},),
        cores=({
            "id": "core-1", "cable_id": "cable-1", "core_number": 1,
            "role": "SIGNAL", "core_tag": "IC-001/1",
            "terminal_path": (
                {"equipment_id": "CT-1", "terminal_role": "S1", "designation": "X1:1"},
                {"equipment_id": "TB-1", "terminal_role": "1", "designation": "X2:1"},
            ),
        },),
        panel_wires=(),
        signals=({"id": "signal-1", "tag": "IA_A", "description": "Phase A current", "kind": "CURRENT"},),
        signal_bindings=({
            "id": "binding-1", "signal_id": "signal-1",
            "carrier_kind": "CABLE_CORE", "carrier_id": "core-1",
            "direction": "SOURCE_TO_SINK",
        },),
        tag_policy=(),
    )
    wiring = SLDInstrumentationWiringAdapter().project(read_model, model)

    snapshot = SLDCanvasProjection().project(model, instrumentation_wiring=wiring)

    assert len(snapshot.connections) == 1
    connection = snapshot.connections[0]
    assert connection.connection_id == "CABLE_CORE:core-1:1"
    assert connection.projection_source == "instrumentation_wiring"
    assert connection.properties["cable_id"] == "cable-1"
    assert connection.properties["core_id"] == "core-1"
    assert connection.properties["signal_tags"] == ("IA_A",)
    assert connection.source_endpoint.terminal_role == "S1"
    assert connection.target_endpoint.terminal_role == "1"
    assert snapshot.physical_wiring_diagnostics == ()
    assert model.connection_count == 0


def test_canvas_snapshot_exposes_unresolved_physical_wiring_diagnostics():
    model = SLDModel()
    model.add_node(SLDNode(node_id="ct-node", equipment_id="CT-1"))
    read_model = InstrumentationWiringReadModel(
        project_id="project-1",
        activation_generation=2,
        cables=({"id": "cable-1", "tag": "IC-001", "service": "CT secondary", "core_count": 1},),
        cores=({
            "id": "core-1", "cable_id": "cable-1", "core_number": 1,
            "role": "SIGNAL", "terminal_path": (
                {"equipment_id": "CT-1", "terminal_role": "S1", "designation": "X1:1"},
                {"equipment_id": "TB-1", "terminal_role": "1", "designation": "X2:1"},
            ),
        },),
        panel_wires=(), signals=(), signal_bindings=(), tag_policy=(),
    )
    wiring = SLDInstrumentationWiringAdapter().project(read_model, model)

    snapshot = SLDCanvasProjection().project(model, instrumentation_wiring=wiring)

    assert snapshot.connections == ()
    assert len(snapshot.physical_wiring_diagnostics) == 1
    assert "TB-1/1" in snapshot.physical_wiring_diagnostics[0]
