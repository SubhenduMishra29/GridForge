"""Targeted Power Flow study configuration contract tests.

Author: Subhendu Mishra
"""

import pytest

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.solver.power_flow.input import PowerFlowBusType


def test_power_flow_configuration_is_single_explicit_study_contract():
    config = PowerFlowStudyConfiguration.from_mapping(
        {"B1": PowerFlowBusType.SLACK, "B2": PowerFlowBusType.PQ},
        base_mva=100.0,
        tolerance=1e-7,
        max_iterations=40,
        voltage_bases_kv={"B1": 132.0, "B2": 33.0},
        numerical_options={"method": "newton-raphson"},
    )

    assert config.base_mva == 100.0
    assert config.slack_bus_id == "B1"
    assert config.tolerance == 1e-7
    assert config.max_iterations == 40
    assert config.voltage_base_of("B2") == 33.0
    assert config.numerical_options["method"] == "newton-raphson"


def test_power_flow_configuration_requires_exactly_one_slack():
    with pytest.raises(ValueError, match="exactly one SLACK"):
        PowerFlowStudyConfiguration.from_mapping(
            {"B1": "PQ", "B2": "PV"},
            base_mva=100.0,
        )
