# ============================================================
# File: tests/core/analysis/test_open_partial_preparation_contracts.py
# GridForge V2 — Open/Partial Preparation Contract Tests
# Author: Subhendu Mishra
# ============================================================

from types import SimpleNamespace

import pytest

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.power_flow_preparation import PowerFlowPreparation
from core.model.bus import Bus
from core.model.capacitor import Capacitor
from core.model.reactor import Reactor
from core.model.shunt import Shunt
from core.model.transformer import Transformer
from core.solver.power_flow.input import PowerFlowBusType


def _preparation(buses) -> PowerFlowPreparation:
    network = SimpleNamespace(
        buses=tuple(buses),
        transformers=(),
        shunts=(),
        capacitors=(),
        reactors=(),
        lines=(),
        cables=(),
    )
    configuration = PowerFlowStudyConfiguration(
        bus_types={str(buses[0].id): PowerFlowBusType.SLACK, str(buses[1].id): PowerFlowBusType.PQ},
        base_mva=100.0,
    )
    return PowerFlowPreparation(network, configuration)


def test_pu_transformer_is_converted_once_to_system_base() -> None:
    bus_hv = Bus("B-HV", nominal_voltage_kv=132.0)
    bus_lv = Bus("B-LV", nominal_voltage_kv=11.0)
    transformer = Transformer(
        "T1",
        endpoint_from=bus_hv,
        endpoint_to=bus_lv,
        r=0.01,
        x=0.10,
        impedance_basis="pu",
        rate_mva=50.0,
        impedance_base_voltage_kv=132.0,
    )
    prep = _preparation((bus_hv, bus_lv))
    prep.network.transformers = (transformer,)

    prepared = prep._prepare_transformers({"B-HV": 132.0, "B-LV": 11.0})

    assert prepared[0].r_pu == pytest.approx(0.02)
    assert prepared[0].x_pu == pytest.approx(0.20)


def test_engineering_transformer_ohms_are_converted_in_preparation() -> None:
    bus_hv = Bus("B-HV", nominal_voltage_kv=132.0)
    bus_lv = Bus("B-LV", nominal_voltage_kv=11.0)
    transformer = Transformer(
        "T1",
        endpoint_from=bus_hv,
        endpoint_to=bus_lv,
        r=1.7424,
        x=17.424,
        impedance_basis="engineering",
        rate_mva=100.0,
        impedance_base_voltage_kv=132.0,
    )
    prep = _preparation((bus_hv, bus_lv))
    prep.network.transformers = (transformer,)

    prepared = prep._prepare_transformers({"B-HV": 132.0, "B-LV": 11.0})

    assert prepared[0].r_pu == pytest.approx(1.7424 / (132.0**2 / 100.0))
    assert prepared[0].x_pu == pytest.approx(17.424 / (132.0**2 / 100.0))


def test_transformer_reference_voltage_must_match_from_side() -> None:
    bus_hv = Bus("B-HV", nominal_voltage_kv=132.0)
    bus_lv = Bus("B-LV", nominal_voltage_kv=11.0)
    transformer = Transformer(
        "T1",
        endpoint_from=bus_hv,
        endpoint_to=bus_lv,
        r=0.01,
        x=0.10,
        impedance_basis="pu",
        rate_mva=50.0,
        impedance_base_voltage_kv=11.0,
    )
    prep = _preparation((bus_hv, bus_lv))
    prep.network.transformers = (transformer,)

    with pytest.raises(ValueError, match="reference voltage"):
        prep._prepare_transformers({"B-HV": 132.0, "B-LV": 11.0})


def test_capacitor_and_reactor_become_prepared_shunts() -> None:
    bus = Bus("B1", nominal_voltage_kv=11.0)
    capacitor = Capacitor("C1", bus=bus, reactive_power_injection_mvar=10.0)
    reactor = Reactor("R1", bus=bus, reactive_power_injection_mvar=-5.0)
    generic = Shunt("S1", bus=bus, g_pu=0.01, b_pu=0.02)

    prep = _preparation((bus, Bus("B2", nominal_voltage_kv=11.0)))
    prep.network.shunts = (generic,)
    prep.network.capacitors = (capacitor,)
    prep.network.reactors = (reactor,)

    prepared = prep._prepare_shunts({"B1": 11.0, "B2": 11.0})
    by_id = {item.shunt_id: item for item in prepared}

    assert by_id["S1"].g_pu == pytest.approx(0.01)
    assert by_id["S1"].b_pu == pytest.approx(0.02)
    assert by_id["C1"].b_pu == pytest.approx(-0.10)
    assert by_id["R1"].b_pu == pytest.approx(0.05)
