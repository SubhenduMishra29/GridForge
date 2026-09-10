"""Regression contracts for Protection preparation and measurement conversion."""

from types import SimpleNamespace

from core.analysis.line_flow import LineFlowResult
from core.measurement.measurement_channel import MeasurementChannel, MeasurementSignalType
from core.measurement.measurement_generation import (
    MeasurementGeneration,
    PreparedMeasurementContext,
)
from core.protection.preparation import ProtectionPreparation


def _line_result(current_pu: complex = 1.0 + 0.0j) -> LineFlowResult:
    return LineFlowResult(
        line_id="line-1",
        from_bus="bus-1",
        to_bus="bus-2",
        current_from=current_pu,
        current_to=current_pu,
        p_from=0.0,
        q_from=0.0,
        p_to=0.0,
        q_to=0.0,
        p_loss=0.0,
        q_balance=0.0,
    )


def test_measurement_current_uses_pu_to_primary_to_secondary_chain():
    channel = MeasurementChannel(
        id="ia",
        signal_type=MeasurementSignalType.CURRENT,
        unit="A",
    )
    source = SimpleNamespace(
        id="ct-1",
        ratio=10.0,
        polarity="P1_P2",
        in_service=True,
    )
    context = PreparedMeasurementContext(
        source_id="ct-1",
        source_terminal="P1",
        bus_id="bus-1",
        electrical_side="from",
        quantity=_line_result(2.0 + 0.0j),
    )
    prepared_power_flow = SimpleNamespace(
        base_mva=100.0,
        bus_voltage_bases={"bus-1": 10.0},
    )

    value = MeasurementGeneration().generate_current(
        context,
        source,
        channel,
        prepared_power_flow=prepared_power_flow,
    )

    # Ibase = 100 MVA / (sqrt(3) * 10 kV) = 5773.5 A.
    # Iprimary = 2 pu * Ibase = 11547 A; secondary = / 10.
    assert abs(value - 1154.700538) < 1.0e-6


def test_protection_preparation_detaches_measurement_values_and_settings():
    channel = MeasurementChannel(
        id="ia",
        signal_type=MeasurementSignalType.CURRENT,
        unit="A",
        raw_value=5.0,
    )
    relay = SimpleNamespace(
        id="relay-1",
        function_type="OVER_CURRENT",
        settings={"pickup": 4.0},
        in_service=True,
        enabled=True,
        blocked=False,
    )

    prepared = ProtectionPreparation().prepare(
        relay,
        {"IA": channel},
        element_id="oc-1",
        function_code="51",
    )

    channel.update(99.0)
    relay.settings["pickup"] = 100.0

    assert prepared.relay_id == "relay-1"
    assert prepared.element_id == "oc-1"
    assert prepared.measurements["IA"].engineering_value == 5.0
    assert prepared.settings["pickup"] == 4.0
