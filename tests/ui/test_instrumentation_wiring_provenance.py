from types import SimpleNamespace

from core.application.read_models import InstrumentationWiringReadModel, SignalEndpointResolutionReadModel
from ui.instrumentation_wiring_provenance import project_signal_provenance


def _wiring():
    return InstrumentationWiringReadModel(
        project_id="project-1",
        activation_generation=1,
        cables=({"id": "cable-1", "tag": "C-101"},),
        cores=({
            "id": "core-1", "cable_id": "cable-1",
            "core_number": 2, "core_tag": "PT101-B",
        },),
        panel_wires=({"id": "wire-1", "tag": "W-101"},),
        signals=({"id": "signal-1", "tag": "PT-101-V"},),
        signal_bindings=(
            {
                "id": "carrier-1", "signal_id": "signal-1",
                "carrier_kind": "CABLE_CORE", "carrier_id": "core-1",
            },
            {
                "id": "carrier-2", "signal_id": "signal-1",
                "carrier_kind": "PANEL_WIRE", "carrier_id": "wire-1",
            },
        ),
        tag_policy=(),
    )


def test_signal_provenance_preserves_signal_cable_core_and_panel_wire_tags():
    resolution = SignalEndpointResolutionReadModel(
        binding_id="binding-1",
        signal_id="signal-1",
        endpoint_kind="CONTROL_INPUT",
        endpoint_id="component-1",
        owner_id="control-1",
        port="PV",
        status="RESOLVED",
        direction="SOURCE_TO_SINK",
        physical_sink_terminal={
            "equipment_id": "PLC-101",
            "terminal_role": "AI-01+",
            "designation": "AI-01+",
            "terminal_point_id": "terminal-point-101",
        },
    )
    result = project_signal_provenance(_wiring(), (resolution,))
    assert len(result) == 1
    item = result[0]
    assert item.signal_tag == "PT-101-V"
    assert item.carrier_labels == ("C-101 / core PT101-B", "W-101")
    assert item.short_label == "PT-101-V | C-101 / core PT101-B, W-101"
    assert "Endpoint: CONTROL_INPUT" in item.detail_text
    assert "Direction: SOURCE_TO_SINK" in item.detail_text
    assert "PLC-101 / AI-01+ / AI-01+ / terminal-point-101" in item.detail_text


def test_signal_provenance_marks_unresolved_endpoint_and_preserves_diagnostics():
    resolution = SignalEndpointResolutionReadModel(
        binding_id="binding-2",
        signal_id="signal-1",
        endpoint_kind="PROTECTION_INPUT",
        endpoint_id="protection-binding-1",
        owner_id="element-1",
        port="IA",
        status="UNRESOLVED",
        diagnostics=("Physical path is discontinuous.",),
    )
    item = project_signal_provenance(_wiring(), (resolution,))[0]
    assert item.short_label == "! UNRESOLVED: PT-101-V"
    assert "Physical path is discontinuous." in item.detail_text


def test_signal_provenance_ignores_resolution_without_canonical_signal_record():
    resolution = SimpleNamespace(
        binding_id="binding-3",
        signal_id="missing-signal",
        endpoint_kind="CONTROL_INPUT",
        endpoint_id="component-1",
        owner_id="control-1",
        port="PV",
        status="RESOLVED",
        diagnostics=(),
    )
    assert project_signal_provenance(_wiring(), (resolution,)) == ()
