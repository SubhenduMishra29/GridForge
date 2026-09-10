"""Regression contracts for explicit electrical migration."""

import pytest

from core.persistence.migration import (
    AmbiguousElectricalDataError,
    LegacyElectricalDataMigration,
)


def test_legacy_cable_requires_explicit_units():
    with pytest.raises(AmbiguousElectricalDataError, match="impedance_units"):
        LegacyElectricalDataMigration().migrate(
            "cable", {"r": 0.01, "x": 0.02, "b": 0.0}
        )


def test_legacy_transformer_requires_explicit_impedance_basis():
    with pytest.raises(AmbiguousElectricalDataError, match="impedance_basis"):
        LegacyElectricalDataMigration().migrate(
            "transformer", {"r": 0.01, "x": 0.08}
        )


def test_explicit_legacy_representation_is_detached_without_interpretation():
    payload = {"r": 0.01, "x": 0.02, "b": 0.0, "impedance_units": "pu"}
    result = LegacyElectricalDataMigration().migrate("cable", payload)

    payload["r"] = 99.0
    assert result.values["r"] == 0.01
    assert result.values["impedance_units"] == "pu"
    assert result.migrated is True
