# ============================================================
# File: tests/core/analysis/test_power_flow_configuration_gf_aud_209.py
# GridForge V2 — GF-AUD-209 Power Flow Configuration Contract Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import inspect

import pytest

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.solver.power_flow.input import PowerFlowBusType


BUS_TYPES = {
    "BUS-1": PowerFlowBusType.SLACK,
    "BUS-2": PowerFlowBusType.PQ,
}


def test_from_mapping_accepts_only_authoritative_study_inputs() -> None:
    signature = inspect.signature(PowerFlowStudyConfiguration.from_mapping)

    assert tuple(signature.parameters) == ("bus_types", "base_mva")
    assert "slack_bus_id" not in signature.parameters


def test_from_mapping_derives_slack_bus_id_from_bus_types() -> None:
    configuration = PowerFlowStudyConfiguration.from_mapping(
        BUS_TYPES,
        base_mva=50.0,
    )

    assert configuration.slack_bus_id == "BUS-1"
    assert configuration.bus_types["BUS-1"] is PowerFlowBusType.SLACK


def test_from_mapping_rejects_obsolete_slack_bus_id_argument() -> None:
    with pytest.raises(TypeError):
        PowerFlowStudyConfiguration.from_mapping(
            BUS_TYPES,
            slack_bus_id="BUS-2",
            base_mva=50.0,
        )


def test_from_mapping_preserves_constructor_validation() -> None:
    with pytest.raises(ValueError, match="exactly one SLACK"):
        PowerFlowStudyConfiguration.from_mapping(
            {"BUS-1": PowerFlowBusType.PQ},
            base_mva=50.0,
        )

    with pytest.raises(ValueError, match="finite and positive"):
        PowerFlowStudyConfiguration.from_mapping(
            BUS_TYPES,
            base_mva=0.0,
        )
