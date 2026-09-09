# ============================================================
# File: tests/core/analysis/test_power_flow_gf_aud_207_208.py
# GridForge V2 — GF-AUD-207 / GF-AUD-208 Power Flow Boundary Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.power_flow_preparation import PowerFlowPreparation, PreparedPowerFlow
from core.solver.power_flow.input import PowerFlowBusType


BUS_TYPES = {
    "BUS-1": PowerFlowBusType.SLACK,
    "BUS-2": PowerFlowBusType.PQ,
}


def test_study_configuration_requires_positive_finite_base_mva() -> None:
    for value in (0.0, -1.0, float("inf"), float("nan")):
        with pytest.raises(ValueError):
            PowerFlowStudyConfiguration(bus_types=BUS_TYPES, base_mva=value)


def test_study_configuration_exposes_immutable_base_mva() -> None:
    configuration = PowerFlowStudyConfiguration(bus_types=BUS_TYPES, base_mva=50.0)
    assert configuration.base_mva == 50.0
    with pytest.raises(FrozenInstanceError):
        configuration.base_mva = 100.0


def test_preparation_normalizes_engineering_power_using_study_base_mva() -> None:
    """50 MW / 25 MVAr on a 50 MVA study base must become 1.0 / 0.5 pu."""
    network = make_two_bus_network(
        bus1_power=(0.0, 0.0),
        bus2_power=(-50.0, -25.0),
    )
    configuration = PowerFlowStudyConfiguration(bus_types=BUS_TYPES, base_mva=50.0)

    prepared = PowerFlowPreparation.prepare(network, configuration)

    assert prepared.input.p_spec == pytest.approx((0.0, -1.0))
    assert prepared.input.q_spec == pytest.approx((0.0, -0.5))


def test_preparation_normalizes_generator_q_limits_using_study_base_mva() -> None:
    network = make_two_bus_network(
        bus1_power=(0.0, 0.0),
        bus2_power=(-20.0, 0.0),
        bus2_q_limits=(-30.0, 40.0),
    )
    configuration = PowerFlowStudyConfiguration(bus_types=BUS_TYPES, base_mva=50.0)

    prepared = PowerFlowPreparation.prepare(network, configuration)

    assert prepared.input.q_min == pytest.approx((None, -0.6))
    assert prepared.input.q_max == pytest.approx((None, 0.8))


def test_preparation_does_not_use_hard_coded_100_mva_base() -> None:
    network = make_two_bus_network(
        bus1_power=(0.0, 0.0),
        bus2_power=(-25.0, -10.0),
    )
    configuration = PowerFlowStudyConfiguration(bus_types=BUS_TYPES, base_mva=25.0)

    prepared = PowerFlowPreparation.prepare(network, configuration)

    assert prepared.input.p_spec[1] == pytest.approx(-1.0)
    assert prepared.input.q_spec[1] == pytest.approx(-0.4)


def test_voltage_normalization_uses_each_bus_nominal_voltage() -> None:
    network = make_two_bus_network(
        bus1_voltage_kv=11.0,
        bus2_voltage_kv=33.0,
        bus1_voltage_engineering_kv=11.0,
        bus2_voltage_engineering_kv=16.5,
    )
    configuration = PowerFlowStudyConfiguration(bus_types=BUS_TYPES, base_mva=50.0)

    prepared = PowerFlowPreparation.prepare(network, configuration)

    assert prepared.input.initial_vm == pytest.approx((1.0, 0.5))


def test_prepared_power_flow_remains_immutable() -> None:
    prepared = PreparedPowerFlow(input=make_power_flow_input(), ybus=make_ybus())
    with pytest.raises(FrozenInstanceError):
        prepared.input = make_power_flow_input()


def test_preparation_preserves_canonical_bus_order_for_input_and_ybus() -> None:
    network = make_two_bus_network()
    configuration = PowerFlowStudyConfiguration(bus_types=BUS_TYPES, base_mva=50.0)

    prepared = PowerFlowPreparation.prepare(network, configuration)

    assert prepared.input.bus_ids == prepared.ybus.bus_ids
    assert prepared.input.bus_ids == tuple(bus.id for bus in network.buses)


def test_result_conversion_uses_bus_specific_nominal_voltage_not_global_base() -> None:
    """The result boundary must convert each PU voltage using its own Bus base."""
    result = make_power_flow_result(voltage_magnitudes=(1.0, 0.5))
    network = make_two_bus_network(bus1_voltage_kv=11.0, bus2_voltage_kv=33.0)

    engineering = convert_power_flow_result_to_engineering(result, network)

    assert engineering.voltage_kv("BUS-1") == pytest.approx(11.0)
    assert engineering.voltage_kv("BUS-2") == pytest.approx(16.5)


def test_boundary_result_is_structured_engineering_data_not_display_text() -> None:
    result = make_power_flow_result(voltage_magnitudes=(1.0, 0.5))
    network = make_two_bus_network(bus1_voltage_kv=11.0, bus2_voltage_kv=33.0)

    engineering = convert_power_flow_result_to_engineering(result, network)

    assert isinstance(engineering.voltage_kv("BUS-1"), float)
    assert not isinstance(engineering.voltage_kv("BUS-1"), str)


# Test fixtures/helpers intentionally reference the repository's existing model
# constructors. They will be aligned with the actual model API before execution.
def make_two_bus_network(
    *,
    bus1_power=(0.0, 0.0),
    bus2_power=(-50.0, -25.0),
    bus1_voltage_kv=11.0,
    bus2_voltage_kv=33.0,
    bus1_voltage_engineering_kv=None,
    bus2_voltage_engineering_kv=None,
    bus2_q_limits=(None, None),
):
    raise NotImplementedError("RED-phase fixture to be connected to audited Core constructors")


def make_power_flow_input():
    raise NotImplementedError("RED-phase fixture")


def make_ybus():
    raise NotImplementedError("RED-phase fixture")


def make_power_flow_result(*, voltage_magnitudes):
    raise NotImplementedError("RED-phase fixture")


def convert_power_flow_result_to_engineering(result, network):
    raise NotImplementedError("RED-phase result-boundary contract")
