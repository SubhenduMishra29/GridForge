"""Regression contracts for the detached Power Flow numerical boundary."""

from types import MappingProxyType

import pytest

from core.analysis.power_flow_preparation import PreparedPowerFlow


def test_prepared_power_flow_voltage_bases_are_detached_and_immutable():
    """Prepared voltage-base metadata must not retain a mutable source mapping."""
    bases = {"bus-1": 11.0}
    snapshot = object.__new__(PreparedPowerFlow)
    object.__setattr__(snapshot, "bus_voltage_bases", MappingProxyType(dict(bases)))

    bases["bus-1"] = 33.0
    assert snapshot.bus_voltage_bases["bus-1"] == 11.0

    with pytest.raises(TypeError):
        snapshot.bus_voltage_bases["bus-1"] = 33.0
