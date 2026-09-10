"""Regression contract for detached prepared metadata."""

from types import MappingProxyType


def test_prepared_voltage_bases_are_detached_from_source_mapping():
    bases = {"bus-1": 11.0}
    detached = MappingProxyType(dict(bases))
    bases["bus-1"] = 33.0
    assert detached["bus-1"] == 11.0
    assert isinstance(detached, MappingProxyType)
