# ============================================================
# File: tests/core/analysis/test_power_flow_preparation_snapshot_gf_aud_214.py
# GridForge V2 — Prepared Power Flow Snapshot Contract
# Author: Subhendu Mishra
# ============================================================

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from core.analysis.power_flow_preparation import (
    PreparedBranch,
    PreparedPowerFlow,
    PreparedShunt,
    PreparedTransformer,
)
from core.numerical.ybus import YBusBuilder
from core.solver.power_flow.input import PowerFlowInput


def _input() -> PowerFlowInput:
    return PowerFlowInput(
        bus_ids=("B1", "B2"),
        bus_types=("SLACK", "PQ"),
        p_spec=(0.0, -0.1),
        q_spec=(0.0, -0.05),
        q_min=(None, None),
        q_max=(None, None),
        initial_vm=(1.0, 1.0),
        initial_va=(0.0, 0.0),
    )


def test_prepared_branch_is_immutable_and_detached():
    branch = PreparedBranch(
        branch_id="L1",
        from_bus_id="B1",
        to_bus_id="B2",
        r_pu=0.01,
        x_pu=0.05,
        b_pu=0.001,
        in_service=True,
    )

    assert branch.branch_id == "L1"
    assert branch.from_bus_id == "B1"
    assert branch.to_bus_id == "B2"
    assert branch.r_pu == pytest.approx(0.01)

    with pytest.raises(FrozenInstanceError):
        branch.r_pu = 0.02


def test_prepared_transformer_preserves_tap_and_shift_in_numerical_snapshot():
    transformer = PreparedTransformer(
        branch_id="T1",
        from_bus_id="B1",
        to_bus_id="B2",
        r_pu=0.01,
        x_pu=0.08,
        b_pu=0.0,
        tap=1.05,
        shift=0.125,
        in_service=True,
    )

    assert transformer.tap == pytest.approx(1.05)
    assert transformer.shift == pytest.approx(0.125)


def test_prepared_power_flow_contains_detached_branch_and_transformer_snapshots():
    branch = PreparedBranch("L1", "B1", "B2", 0.01, 0.05, 0.001, True)
    transformer = PreparedTransformer("T1", "B1", "B2", 0.02, 0.08, 0.0, 1.0, 0.0, True)
    shunt = PreparedShunt("S1", "B2", 0.0, 0.01, True)
    placeholder_ybus = SimpleNamespace(bus_ids=("B1", "B2"))

    prepared = PreparedPowerFlow(
        input=_input(),
        ybus=placeholder_ybus,
        base_mva=100.0,
        bus_voltage_bases={"B1": 11.0, "B2": 11.0},
        branches=(branch,),
        transformers=(transformer,),
        shunts=(shunt,),
    )

    assert prepared.branches == (branch,)
    assert prepared.transformers == (transformer,)
    assert prepared.shunts == (shunt,)
    assert prepared.base_mva == pytest.approx(100.0)


def test_ybus_builder_consumes_only_prepared_pu_snapshot():
    branch = PreparedBranch("L1", "B1", "B2", 0.01, 0.05, 0.001, True)
    prepared = SimpleNamespace(
        bus_ids=("B1", "B2"),
        branches=(branch,),
        transformers=(),
        shunts=(),
    )

    ybus = YBusBuilder().build(prepared)

    assert ybus.bus_ids == ("B1", "B2")
    assert ybus.shape == (2, 2)
    assert ybus[0, 1] != 0
