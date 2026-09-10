# ============================================================
# File: tests/core/measurement/test_measurement_conversion_contract.py
# GridForge V2 — GF-AUD-204 Measurement Conversion Contract Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

import pytest

from core.analysis.line_flow import LineFlowResult
from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementPhase,
    MeasurementSignalType,
)
from core.measurement.measurement_generation import (
    MeasurementGeneration,
    PreparedMeasurementContext,
)
from core.model.ct import CurrentTransformer
from core.model.cvt import CapacitiveVoltageTransformer
from core.model.pt import PT
from core.solver.power_flow.result import PowerFlowResult


def _prepared_power_flow() -> SimpleNamespace:
    return SimpleNamespace(
        base_mva=100.0,
        bus_voltage_bases={"BUS-1": 11.0},
        input=SimpleNamespace(index_of=lambda bus_id: {"BUS-1": 0}[bus_id]),
    )


def _current_channel() -> MeasurementChannel:
    return MeasurementChannel(
        id="CH-I",
        signal_type=MeasurementSignalType.CURRENT,
        phase=MeasurementPhase.A,
        unit="A",
    )


def _voltage_channel() -> MeasurementChannel:
    return MeasurementChannel(
        id="CH-V",
        signal_type=MeasurementSignalType.VOLTAGE,
        phase=MeasurementPhase.A,
        unit="V",
    )


def test_ct_conversion_is_pu_to_base_current_to_primary_to_secondary() -> None:
    source = CurrentTransformer(
        "CT-1",
        primary_rated_current_a=1000.0,
        secondary_rated_current_a=5.0,
    )
    quantity = LineFlowResult(
        line_id="L1",
        from_bus="BUS-1",
        to_bus="BUS-2",
        current_from=2.0 + 0.0j,
        current_to=0.0 + 0.0j,
        p_from=0.0,
        q_from=0.0,
        p_to=0.0,
        q_to=0.0,
        p_loss=0.0,
        q_balance=0.0,
    )
    context = PreparedMeasurementContext(
        source_id="CT-1",
        source_terminal="P1",
        bus_id="BUS-1",
        electrical_side="from",
        quantity=quantity,
    )

    value = MeasurementGeneration().generate_current(
        context,
        source,
        _current_channel(),
        prepared_power_flow=_prepared_power_flow(),
    )

    expected_base_a = 100.0 * 1000.0 / (3.0**0.5 * 11.0)
    assert value == pytest.approx(2.0 * expected_base_a / 200.0)


def test_pt_conversion_is_pu_to_primary_voltage_to_secondary_voltage() -> None:
    source = PT(
        "PT-1",
        primary_voltage_kv=11.0,
        secondary_voltage_v=110.0,
    )
    quantity = PowerFlowResult(
        success=True,
        iterations=1,
        error=0.0,
        pv_to_pq=(),
        history=(),
        message="ok",
        voltage_magnitudes=(1.1,),
        voltage_angles=(0.0,),
        bus_ids=("BUS-1",),
    )
    context = PreparedMeasurementContext(
        source_id="PT-1",
        source_terminal="primary_a",
        bus_id="BUS-1",
        electrical_side=None,
        quantity=quantity,
    )

    value = MeasurementGeneration().generate_voltage(
        context,
        source,
        _voltage_channel(),
        _prepared_power_flow(),
    )

    assert value == pytest.approx(121.0)


def test_cvt_uses_declared_voltage_ratio_not_a_pu_ratio_shortcut() -> None:
    source = CapacitiveVoltageTransformer(
        "CVT-1",
        rated_primary_voltage_kv=220.0,
        rated_secondary_voltage_v=110.0,
    )
    quantity = PowerFlowResult(
        success=True,
        iterations=1,
        error=0.0,
        pv_to_pq=(),
        history=(),
        message="ok",
        voltage_magnitudes=(1.0,),
        voltage_angles=(0.0,),
        bus_ids=("BUS-1",),
    )
    prepared = SimpleNamespace(
        base_mva=100.0,
        bus_voltage_bases={"BUS-1": 220.0},
        input=SimpleNamespace(index_of=lambda bus_id: 0),
    )
    context = PreparedMeasurementContext(
        source_id="CVT-1",
        source_terminal="H1",
        bus_id="BUS-1",
        electrical_side=None,
        quantity=quantity,
    )

    value = MeasurementGeneration().generate_voltage(
        context,
        source,
        _voltage_channel(),
        prepared,
    )

    assert value == pytest.approx(110.0)


def test_measurement_source_binding_rejects_mismatched_source_identity() -> None:
    source = CurrentTransformer("CT-actual")
    context = PreparedMeasurementContext(
        source_id="CT-requested",
        source_terminal="P1",
        bus_id="BUS-1",
        electrical_side="from",
        quantity=LineFlowResult(
            line_id="L1",
            from_bus="BUS-1",
            to_bus="BUS-2",
            current_from=1.0,
            current_to=0.0,
            p_from=0.0,
            q_from=0.0,
            p_to=0.0,
            q_to=0.0,
            p_loss=0.0,
            q_balance=0.0,
        ),
    )

    with pytest.raises(ValueError, match="source_id"):
        MeasurementGeneration().generate_current(
            context,
            source,
            _current_channel(),
            prepared_power_flow=_prepared_power_flow(),
        )
