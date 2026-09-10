# ============================================================
# File: tests/core/analysis/test_power_flow_preparation_orchestration_gf_aud_216.py
# GridForge V2 — Power Flow Preparation Orchestration Contract
# Author: Subhendu Mishra
# ============================================================

"""Contract tests for the preparation -> YBus -> solver boundary."""

from __future__ import annotations

import pytest

from core.analysis.power_flow import PowerFlowAnalysis
from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.power_flow_preparation import PowerFlowPreparation
from core.model.bus import Bus
from core.model.line import Line
from core.network.endpoint import Terminal
from core.network.network import Network
from core.solver.power_flow.input import PowerFlowBusType


def _configuration(*bus_ids: str) -> PowerFlowStudyConfiguration:
    return PowerFlowStudyConfiguration.from_mapping(
        {bus_ids[0]: PowerFlowBusType.SLACK, **{bus_id: PowerFlowBusType.PQ for bus_id in bus_ids[1:]}},
        base_mva=100.0,
    )


def test_analysis_from_network_prepares_before_solver_and_preserves_input_result_contract() -> None:
    network = Network()
    bus_1 = Bus(id="B1", name="B1", nominal_voltage_kv=11.0, voltage_pu=1.0)
    bus_2 = Bus(id="B2", name="B2", nominal_voltage_kv=11.0, voltage_pu=1.0)
    network.add_bus(bus_1)
    network.add_bus(bus_2)
    network.add_line(
        Line(
            id="L1",
            name="L1",
            from_terminal=Terminal(bus_id="B1"),
            to_terminal=Terminal(bus_id="B2"),
            resistance_ohm=0.2,
            reactance_ohm=0.4,
            shunt_susceptance_siemens=0.0,
        )
    )

    analysis = PowerFlowAnalysis.from_network(network, _configuration("B1", "B2"))

    assert analysis.input.bus_ids == ("B1", "B2")
    assert analysis.Ybus.bus_ids == analysis.input.bus_ids
    assert analysis.prepared.bus_ids == analysis.input.bus_ids
    assert analysis.prepared.branches[0].r_pu != 0.0
    assert analysis.prepared.branches[0].x_pu != 0.0

    result = analysis.solve()

    assert len(result.voltage_magnitudes) == analysis.input.bus_count
    assert len(result.voltage_angles) == analysis.input.bus_count
    assert isinstance(result.message, str)


def test_line_engineering_values_are_converted_once_at_power_flow_preparation() -> None:
    network = Network()
    network.add_bus(Bus(id="B1", name="B1", nominal_voltage_kv=11.0, voltage_pu=1.0))
    network.add_bus(Bus(id="B2", name="B2", nominal_voltage_kv=11.0, voltage_pu=1.0))
    network.add_line(
        Line(
            id="L1",
            name="L1",
            from_terminal=Terminal(bus_id="B1"),
            to_terminal=Terminal(bus_id="B2"),
            resistance_ohm=0.2,
            reactance_ohm=0.4,
            shunt_susceptance_siemens=0.001,
        )
    )

    prepared = PowerFlowPreparation.prepare(network, _configuration("B1", "B2"))
    branch = prepared.branches[0]

    # Zbase = 11^2 / 100 = 1.21 ohm; Ybase = 1 / 1.21 S.
    assert branch.r_pu == pytest.approx(0.2 / 1.21)
    assert branch.x_pu == pytest.approx(0.4 / 1.21)
    assert branch.b_pu == pytest.approx(0.001 * 1.21)


def test_analysis_from_prepared_uses_detached_ybus_without_rebuilding_from_live_network() -> None:
    network = Network()
    network.add_bus(Bus(id="B1", name="B1", nominal_voltage_kv=11.0, voltage_pu=1.0))
    network.add_bus(Bus(id="B2", name="B2", nominal_voltage_kv=11.0, voltage_pu=1.0))
    prepared = PowerFlowPreparation.prepare(network, _configuration("B1", "B2"))

    analysis = PowerFlowAnalysis.from_prepared(prepared)

    assert analysis.input is prepared.input
    assert analysis.Ybus is prepared.ybus
    assert analysis.prepared is prepared
