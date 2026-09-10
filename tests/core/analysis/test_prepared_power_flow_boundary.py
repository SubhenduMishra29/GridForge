"""Regression contracts for the detached Power Flow numerical boundary."""

from types import MappingProxyType, SimpleNamespace

import pytest

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.power_flow_preparation import PowerFlowPreparation, PreparedPowerFlow
from core.model.injection import Injection
from core.solver.power_flow.input import PowerFlowBusType


def test_prepared_power_flow_voltage_bases_are_detached_and_immutable():
    """Prepared voltage-base metadata must not retain a mutable source mapping."""
    bases = {"bus-1": 11.0}
    snapshot = object.__new__(PreparedPowerFlow)
    object.__setattr__(snapshot, "bus_voltage_bases", MappingProxyType(dict(bases)))

    bases["bus-1"] = 33.0
    assert snapshot.bus_voltage_bases["bus-1"] == 11.0

    with pytest.raises(TypeError):
        snapshot.bus_voltage_bases["bus-1"] = 33.0


def test_power_flow_preparation_does_not_require_mutable_bus_index_api():
    """Study preparation must not depend on mutating Network-derived bus indexing."""
    network = SimpleNamespace(buses=())
    configuration = PowerFlowStudyConfiguration.from_mapping(
        {"bus-1": PowerFlowBusType.SLACK},
        base_mva=100.0,
    )

    preparation = PowerFlowPreparation(network, configuration)

    assert preparation.network is network


class _ReactiveInjection(Injection):
    def __init__(self, object_id: str, bus: object, reactive_mvar: float) -> None:
        self.id = object_id
        self.terminal = SimpleNamespace(endpoint=bus)
        self.in_service = True
        self.reactive_mvar = reactive_mvar

    def get_power(self) -> tuple[float, float]:
        return 0.0, self.reactive_mvar


def test_power_flow_bus_spec_includes_capacitor_and_reactor_collections():
    """Reactive equipment registered in dedicated collections must enter bus P/Q specs."""
    bus = SimpleNamespace(id="bus-1")
    capacitor = _ReactiveInjection("cap-1", bus, 20.0)
    reactor = _ReactiveInjection("reactor-1", bus, -8.0)
    network = SimpleNamespace(
        buses=(bus,),
        grids=(),
        generators=(),
        synchronous_machines=(),
        loads=(),
        motors=(),
        solar=(),
        batteries=(),
        capacitors=(capacitor,),
        reactors=(reactor,),
    )
    configuration = PowerFlowStudyConfiguration.from_mapping(
        {"bus-1": PowerFlowBusType.SLACK},
        base_mva=100.0,
    )
    preparation = PowerFlowPreparation(network, configuration)

    assert preparation._bus_power_spec(bus) == (0.0, 12.0, None, None)
