import pytest

from core.application.instrumentation_wiring_schedules import (
    build_instrumentation_wiring_schedules,
)
from core.application.read_models import (
    InstrumentationWiringReadModel,
    SignalEndpointResolutionReadModel,
)


def _wiring(accessory_state="CLOSED"):
    return InstrumentationWiringReadModel(
        project_id="project-1",
        activation_generation=7,
        cables=({
            "id": "cable-1", "tag": "IC-101", "service": "CT secondary",
            "core_count": 1, "length_m": None, "cable_type": None,
            "conductor_material": None, "cross_section_mm2": None,
            "rated_voltage_v": None, "from_location": "Field", "to_location": "Panel",
            "revision": 1, "lifecycle_status": "INSTALLED",
        },),
        cores=({
            "id": "core-1", "cable_id": "cable-1", "core_number": 1,
            "core_tag": "IC-101/1", "role": "SIGNAL", "colour": None,
            "pair_id": None,
            "terminal_path": (
                {"equipment_id": "CT-101", "terminal_role": "S1", "designation": "S1", "terminal_point_id": None},
                {"equipment_id": "TB-101", "terminal_role": "1", "designation": "1A", "terminal_point_id": "tb-point-1"},
            ),
        },),
        panel_wires=({
            "id": "wire-1", "tag": "W-101", "role": "SIGNAL",
            "cross_section_mm2": None, "colour": None,
            "terminal_path": (
                {"equipment_id": "TB-101", "terminal_role": "2", "designation": "2A", "terminal_point_id": "tb-point-2"},
                {"equipment_id": "PLC-101", "terminal_role": "AI1", "designation": "AI1", "terminal_point_id": None},
            ),
        },),
        signals=({
            "id": "signal-1", "tag": "IA_A", "description": "Phase A current",
            "kind": "CURRENT", "unit": "A", "phase": "A",
        },),
        signal_bindings=(
            {
                "id": "core-binding", "signal_id": "signal-1",
                "carrier_kind": "CABLE_CORE", "carrier_id": "core-1",
                "direction": "SOURCE_TO_SINK", "source_channel_id": "channel-1",
            },
            {
                "id": "wire-binding", "signal_id": "signal-1",
                "carrier_kind": "PANEL_WIRE", "carrier_id": "wire-1",
                "direction": "SOURCE_TO_SINK", "source_channel_id": "channel-1",
            },
        ),
        tag_policy=(),
        endpoint_bindings=(
            {
                "id": "source-binding", "signal_id": "signal-1",
                "endpoint": {"kind": "MEASUREMENT_CHANNEL", "endpoint_id": "channel-1"},
                "direction": "SOURCE_TO_SINK",
            },
            {
                "id": "control-binding", "signal_id": "signal-1",
                "endpoint": {
                    "kind": "CONTROL_INPUT", "endpoint_id": "component-1",
                    "owner_id": "control-1", "port": "PV",
                    "physical_terminal": {
                        "equipment_id": "PLC-101", "terminal_role": "AI1",
                        "designation": "AI1", "terminal_point_id": None,
                    },
                },
                "direction": "SOURCE_TO_SINK",
            },
        ),
        terminal_blocks=({
            "id": "TB-101", "tag": "TB-101", "panel_id": "PANEL-1",
            "location": "Marshalling cabinet", "terminal_count": 2,
            "terminal_type": "feed-through", "manufacturer": None,
            "part_number": None, "revision": 1, "lifecycle_status": "INSTALLED",
        },),
        terminal_points=(
            {
                "id": "tb-point-1", "terminal_block_id": "TB-101",
                "terminal_number": "1", "designation": "1A",
                "function": "FEED_THROUGH", "side": None,
                "manufacturer_designation": "1A", "lifecycle_status": "INSTALLED",
            },
            {
                "id": "tb-point-2", "terminal_block_id": "TB-101",
                "terminal_number": "2", "designation": "2A",
                "function": "FEED_THROUGH", "side": None,
                "manufacturer_designation": "2A", "lifecycle_status": "INSTALLED",
            },
        ),
        terminal_accessories=({
            "id": "link-1", "tag": "TB-101-L1", "terminal_block_id": "TB-101",
            "kind": "TEST_DISCONNECT", "state": accessory_state,
            "terminal_point_ids": ("tb-point-1", "tb-point-2"),
            "conductive_pairs": (("tb-point-1", "tb-point-2"),),
        },),
    )


def _resolutions(status="RESOLVED"):
    return (
        SignalEndpointResolutionReadModel(
            binding_id="source-binding", signal_id="signal-1",
            endpoint_kind="MEASUREMENT_CHANNEL", endpoint_id="channel-1",
            owner_id=None, port=None, status="RESOLVED",
        ),
        SignalEndpointResolutionReadModel(
            binding_id="control-binding", signal_id="signal-1",
            endpoint_kind="CONTROL_INPUT", endpoint_id="component-1",
            owner_id="control-1", port="PV", status=status,
            diagnostics=() if status == "RESOLVED" else ("Terminal link is open.",),
            physical_sink_terminal={
                "equipment_id": "PLC-101", "terminal_role": "AI1",
                "designation": "AI1", "terminal_point_id": None,
            },
        ),
    )


def test_schedules_derive_cable_core_terminal_loop_and_point_to_point_rows():
    schedules = build_instrumentation_wiring_schedules(_wiring(), _resolutions())

    assert schedules.project_id == "project-1"
    assert schedules.activation_generation == 7
    assert schedules.cable_schedule[0]["cable_tag"] == "IC-101"
    assert schedules.cable_schedule[0]["cores"][0]["core_tag"] == "IC-101/1"
    assert schedules.core_schedule[0]["source_channel_ids"] == ("channel-1",)
    assert schedules.core_schedule[0]["signal_tags"] == ("IA_A",)
    assert schedules.terminal_plan[0]["terminals"][0]["terminal_point_id"] == "tb-point-1"
    assert schedules.terminal_plan[0]["terminals"][0]["connected_carriers"][0]["carrier_tag"] == "IC-101/1"
    assert schedules.terminal_plan[0]["accessories"][0]["state"] == "CLOSED"
    assert schedules.instrument_loop_schedule[0]["resolution_status"] == "RESOLVED"
    assert len(schedules.interconnection_list) == 2
    assert len(schedules.point_to_point_list) == 2
    assert schedules.point_to_point_list[0]["complete"] is True


def test_schedules_propagate_unresolved_endpoint_diagnostics():
    schedules = build_instrumentation_wiring_schedules(_wiring("OPEN"), _resolutions("UNRESOLVED"))
    loop = schedules.instrument_loop_schedule[0]
    assert loop["resolution_status"] == "UNRESOLVED"
    assert "Terminal link is open." in loop["diagnostics"]


def test_schedules_preserve_unspecified_engineering_values_as_none():
    schedules = build_instrumentation_wiring_schedules(_wiring(), _resolutions())
    cable = schedules.cable_schedule[0]
    assert cable["length_m"] is None
    assert cable["cable_type"] is None
    assert cable["conductor_material"] is None
    assert cable["cross_section_mm2"] is None


def test_schedule_read_model_is_deeply_immutable():
    schedules = build_instrumentation_wiring_schedules(_wiring(), _resolutions())
    with pytest.raises(TypeError):
        schedules.cable_schedule[0]["cable_tag"] = "CHANGED"
    with pytest.raises(TypeError):
        schedules.terminal_plan[0]["terminals"][0]["designation"] = "CHANGED"


def test_schedule_builder_rejects_non_application_read_model():
    with pytest.raises(TypeError):
        build_instrumentation_wiring_schedules({}, ())
