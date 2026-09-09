# ============================================================
# File: tests/core/test_measurement_generation.py
# GridForge V2 — GF-AUD-204 Measurement Generation Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from core.analysis.line_flow import LineFlowResult
from core.analysis.transformer_flow import TransformerFlowResult
from core.analysis.power_flow_preparation import PreparedPowerFlow
from core.model.ct import CTPolarity, CurrentTransformer
from core.model.cvt import CapacitiveVoltageTransformer
from core.model.pt import PT
from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
    MeasurementSignalType,
)
from core.numerical.ybus import YBus
from core.solver.power_flow.input import PowerFlowBusType, PowerFlowInput
from core.solver.power_flow.result import PowerFlowResult
from core.solver.short_circuit.fault_types import FaultType
from core.solver.short_circuit.result import ShortCircuitResult
from core.measurement.measurement_generation import (
    MeasurementGeneration,
    PreparedMeasurementContext,
    UnsupportedMeasurementQuantity,
)


def _channel(signal_type: MeasurementSignalType) -> MeasurementChannel:
    return MeasurementChannel(
        id="MC-01",
        signal_type=signal_type,
        unit="pu",
        quality=MeasurementQuality.UNKNOWN,
    )


def _power_flow_result() -> PowerFlowResult:
    return PowerFlowResult(
        success=True,
        iterations=2,
        error=0.0,
        pv_to_pq=(),
        history=(0.0,),
        message="ok",
        voltage_magnitudes=(1.0, 0.95),
        voltage_angles=(0.0, -2.0),
    )


def _prepared_power_flow() -> PreparedPowerFlow:
    input_data = PowerFlowInput(
        bus_ids=("BUS-2", "BUS-1"),
        bus_types=(PowerFlowBusType.SLACK, PowerFlowBusType.PQ),
        p_spec=(0.0, -0.5),
        q_spec=(0.0, -0.2),
        q_min=(None, None),
        q_max=(None, None),
        initial_vm=(1.0, 1.0),
        initial_va=(0.0, 0.0),
    )
    ybus = YBus(
        matrix=csr_matrix(np.eye(2, dtype=complex)),
        bus_ids=input_data.bus_ids,
    )
    return PreparedPowerFlow(input=input_data, ybus=ybus)


def test_prepared_context_is_immutable_and_does_not_store_solver_index() -> None:
    quantity = LineFlowResult(
        line_id="L1",
        from_bus="BUS-1",
        to_bus="BUS-2",
        current_from=1 + 2j,
        current_to=3 + 4j,
        p_from=0.0,
        q_from=0.0,
        p_to=0.0,
        q_to=0.0,
        p_loss=0.0,
        q_balance=0.0,
    )
    context = PreparedMeasurementContext("CT-01", "P1", "BUS-1", "from", quantity)
    assert context.quantity is quantity
    assert context.bus_id == "BUS-1"
    assert not hasattr(context, "bus_index")
    with pytest.raises(FrozenInstanceError):
        context.bus_id = "BUS-2"


def test_context_preserves_actual_analysis_quantity_without_core_objects() -> None:
    quantity = LineFlowResult(
        line_id="L1",
        from_bus="BUS-1",
        to_bus="BUS-2",
        current_from=1 + 0j,
        current_to=0j,
        p_from=0.0,
        q_from=0.0,
        p_to=0.0,
        q_to=0.0,
        p_loss=0.0,
        q_balance=0.0,
    )
    context = PreparedMeasurementContext("CT-01", "P1", "BUS-1", "from", quantity)
    assert context.quantity is quantity
    assert not hasattr(context.quantity, "network")
    assert not hasattr(context, "bus_index")


def test_line_current_is_consumed_without_recalculation() -> None:
    result = LineFlowResult(
        line_id="L1",
        from_bus="BUS-1",
        to_bus="BUS-2",
        current_from=2 + 3j,
        current_to=4 + 5j,
        p_from=0.0,
        q_from=0.0,
        p_to=0.0,
        q_to=0.0,
        p_loss=0.0,
        q_balance=0.0,
    )
    source = CurrentTransformer("CT-01", primary_rated_current_a=100, secondary_rated_current_a=5)
    channel = _channel(MeasurementSignalType.CURRENT)
    context = PreparedMeasurementContext("CT-01", "P1", "BUS-1", "from", result)
    value = MeasurementGeneration().generate_current(context, source, channel)
    assert value == (2 + 3j) / source.ratio
    assert channel.raw_value == value


def test_transformer_current_is_consumed_without_recalculation() -> None:
    result = TransformerFlowResult(
        transformer_id="T1",
        from_bus="BUS-1",
        to_bus="BUS-2",
        tap_ratio=1.0,
        phase_shift_deg=0.0,
        p_from=0.0,
        q_from=0.0,
        p_to=0.0,
        q_to=0.0,
        p_loss=0.0,
        q_loss=0.0,
        s_from_pu=0.0,
        s_to_pu=0.0,
        i_from_pu=1.5,
        i_to_pu=0.7,
    )
    source = CurrentTransformer("CT-01", primary_rated_current_a=100, secondary_rated_current_a=5)
    channel = _channel(MeasurementSignalType.CURRENT)
    context = PreparedMeasurementContext("CT-01", "P1", "BUS-1", "from", result)
    value = MeasurementGeneration().generate_current(context, source, channel)
    assert value == result.i_from_pu / source.ratio


def test_endpoint_correlation_rejects_positional_bus_guessing() -> None:
    result = LineFlowResult(
        line_id="L1",
        from_bus="BUS-1",
        to_bus="BUS-2",
        current_from=2 + 0j,
        current_to=3 + 0j,
        p_from=0.0,
        q_from=0.0,
        p_to=0.0,
        q_to=0.0,
        p_loss=0.0,
        q_balance=0.0,
    )
    source = CurrentTransformer("CT-01")
    channel = _channel(MeasurementSignalType.CURRENT)
    context = PreparedMeasurementContext("CT-01", "P1", "BUS-WRONG", "from", result)
    with pytest.raises(UnsupportedMeasurementQuantity):
        MeasurementGeneration().generate_current(context, source, channel)


def test_power_flow_uses_bus_id_to_find_execution_index() -> None:
    prepared = _prepared_power_flow()
    result = _power_flow_result()
    source = PT("PT-01", primary_voltage_kv=11, secondary_voltage_v=110)
    channel = _channel(MeasurementSignalType.VOLTAGE)
    context = PreparedMeasurementContext("PT-01", "primary_a", "BUS-1", None, result)
    value = MeasurementGeneration().generate_voltage(context, source, channel, prepared)
    assert value == result.voltage_magnitudes[prepared.input.index_of("BUS-1")] / source.voltage_ratio
    assert value != result.voltage_magnitudes[0] / source.voltage_ratio


def test_cvt_voltage_uses_existing_power_flow_quantity() -> None:
    prepared = _prepared_power_flow()
    result = _power_flow_result()
    source = CapacitiveVoltageTransformer("CVT-01", rated_primary_voltage_kv=220, rated_secondary_voltage_v=110)
    channel = _channel(MeasurementSignalType.VOLTAGE)
    context = PreparedMeasurementContext("CVT-01", "H1", "BUS-2", None, result)
    value = MeasurementGeneration().generate_voltage(context, source, channel, prepared)
    assert value == result.voltage_magnitudes[prepared.input.index_of("BUS-2")] / source.voltage_ratio


def test_ct_polarity_is_taken_from_authoritative_source() -> None:
    result = LineFlowResult(
        line_id="L1",
        from_bus="BUS-1",
        to_bus="BUS-2",
        current_from=2 + 0j,
        current_to=0j,
        p_from=0.0,
        q_from=0.0,
        p_to=0.0,
        q_to=0.0,
        p_loss=0.0,
        q_balance=0.0,
    )
    source = CurrentTransformer("CT-01", primary_rated_current_a=100, secondary_rated_current_a=5, polarity=CTPolarity.P2_P1)
    channel = _channel(MeasurementSignalType.CURRENT)
    context = PreparedMeasurementContext("CT-01", "P1", "BUS-1", "from", result)
    value = MeasurementGeneration().generate_current(context, source, channel)
    assert value == -result.current_from / source.ratio


def test_out_of_service_source_marks_channel_unavailable() -> None:
    result = LineFlowResult(
        line_id="L1",
        from_bus="BUS-1",
        to_bus="BUS-2",
        current_from=2 + 0j,
        current_to=0j,
        p_from=0.0,
        q_from=0.0,
        p_to=0.0,
        q_to=0.0,
        p_loss=0.0,
        q_balance=0.0,
    )
    source = CurrentTransformer("CT-01", in_service=False)
    channel = _channel(MeasurementSignalType.CURRENT)
    context = PreparedMeasurementContext("CT-01", "P1", "BUS-1", "from", result)
    MeasurementGeneration().generate_current(context, source, channel)
    assert channel.available is False


def test_supported_short_circuit_fault_quantity_is_consumed() -> None:
    result = ShortCircuitResult(
        fault_type=FaultType.THREE_PHASE,
        fault_bus_index=1,
        fault_bus_id="BUS-2",
        success=True,
        values={"fault_current": 5 + 1j, "fault_current_magnitude": 5.099},
    )
    source = CurrentTransformer("CT-01")
    channel = _channel(MeasurementSignalType.CURRENT)
    context = PreparedMeasurementContext("CT-01", "P1", "BUS-2", None, result)
    value = MeasurementGeneration().generate_short_circuit(context, source, channel, "fault_current")
    assert value == (5 + 1j) / source.ratio


def test_short_circuit_phase_family_consumes_existing_member() -> None:
    result = ShortCircuitResult(
        fault_type=FaultType.LINE_LINE,
        fault_bus_index=1,
        fault_bus_id="BUS-2",
        success=True,
        values={"phase_currents": {"Ia": 2 + 1j, "Ib": 3 + 0j, "Ic": 0j}},
    )
    source = CurrentTransformer("CT-01")
    channel = _channel(MeasurementSignalType.CURRENT)
    context = PreparedMeasurementContext("CT-01", "P1", "BUS-2", None, result)
    value = MeasurementGeneration().generate_short_circuit(context, source, channel, "phase_currents.Ia")
    assert value == (2 + 1j) / source.ratio


def test_arbitrary_short_circuit_branch_mapping_is_rejected() -> None:
    result = ShortCircuitResult(
        fault_type=FaultType.THREE_PHASE,
        fault_bus_index=1,
        fault_bus_id="BUS-2",
        success=True,
        values={"fault_current": 5 + 1j},
    )
    source = CurrentTransformer("CT-01")
    channel = _channel(MeasurementSignalType.CURRENT)
    context = PreparedMeasurementContext("CT-01", "P1", "BUS-2", "from", result)
    with pytest.raises(UnsupportedMeasurementQuantity, match="branch"):
        MeasurementGeneration().generate_short_circuit(context, source, channel, "branch_current")


def test_post_fault_bus_voltage_mapping_is_rejected() -> None:
    result = ShortCircuitResult(
        fault_type=FaultType.THREE_PHASE,
        fault_bus_index=1,
        fault_bus_id="BUS-2",
        success=True,
        values={"fault_current": 5 + 1j, "Vprefault": 1 + 0j},
    )
    source = PT("PT-01")
    channel = _channel(MeasurementSignalType.VOLTAGE)
    context = PreparedMeasurementContext("PT-01", "primary_a", "BUS-2", None, result)
    with pytest.raises(UnsupportedMeasurementQuantity, match="post-fault"):
        MeasurementGeneration().generate_short_circuit(context, source, channel, "post_fault_voltage")


def test_measurement_generation_has_no_forbidden_dependencies() -> None:
    path = Path(__file__).parents[2] / "core" / "measurement" / "measurement_generation.py"
    text = path.read_text(encoding="utf-8")
    forbidden = (
        "PowerFlowAnalysis", "ShortCircuitAnalysis", "PowerFlowSolver", "ShortCircuitSolver",
        "Network", "Bus", "Terminal", "CurrentTransformer", "CapacitiveVoltageTransformer",
    )
    assert not any(f"import {name}" in text for name in forbidden)
    assert "from core.model.ct" not in text
    assert "from core.model.pt" not in text
    assert "from core.model.cvt" not in text
