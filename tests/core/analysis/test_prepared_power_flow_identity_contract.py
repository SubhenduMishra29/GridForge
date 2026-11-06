"""Regression contracts for Core-to-solver identity preservation."""

from core.analysis.power_flow_preparation import PreparedBranch, PreparedTransformer


def test_prepared_branch_preserves_core_equipment_id():
    branch = PreparedBranch(
        branch_id="LINE-101",
        from_bus_id="BUS-1",
        to_bus_id="BUS-2",
        r_pu=0.01,
        x_pu=0.05,
        b_pu=0.001,
    )
    assert branch.branch_id == "LINE-101"


def test_prepared_transformer_preserves_core_equipment_id():
    transformer = PreparedTransformer(
        branch_id="TR-101",
        from_bus_id="BUS-1",
        to_bus_id="BUS-2",
        r_pu=0.01,
        x_pu=0.08,
        b_pu=0.0,
        tap=1.0,
        shift=0.0,
    )
    assert transformer.branch_id == "TR-101"
