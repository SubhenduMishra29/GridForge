# ============================================================
# File: tests/core/numerical/test_ybus_prepared_boundary_gf_aud_215.py
# GridForge V2 — YBus Prepared Numerical Boundary
# Author: Subhendu Mishra
# ============================================================

from types import SimpleNamespace

import numpy as np
import pytest

from core.numerical.ybus import YBusBuilder


def _prepared(branches=(), transformers=(), shunts=()):
    return SimpleNamespace(
        bus_ids=("B1", "B2"),
        branches=tuple(branches),
        transformers=tuple(transformers),
        shunts=tuple(shunts),
        topology_revision=7,
    )


def test_ybus_builder_does_not_require_live_network_or_engineering_units():
    branch = SimpleNamespace(
        branch_id="L1",
        from_bus_id="B1",
        to_bus_id="B2",
        r_pu=0.01,
        x_pu=0.05,
        b_pu=0.002,
        in_service=True,
    )

    ybus = YBusBuilder().build(_prepared(branches=(branch,)))

    assert ybus.bus_ids == ("B1", "B2")
    assert ybus.topology_revision == 7
    assert ybus.shape == (2, 2)
    assert ybus[0, 1] != 0


def test_line_engineering_fields_cannot_be_consumed_as_ybus_inputs():
    branch = SimpleNamespace(
        branch_id="L1",
        from_bus_id="B1",
        to_bus_id="B2",
        resistance_ohm=0.1,
        reactance_ohm=0.5,
        shunt_susceptance_siemens=0.001,
        in_service=True,
    )

    with pytest.raises((AttributeError, TypeError, ValueError)):
        YBusBuilder().build(_prepared(branches=(branch,)))


def test_branch_stamp_uses_half_shunt_susceptance_on_each_terminal():
    branch = SimpleNamespace(
        branch_id="L1",
        from_bus_id="B1",
        to_bus_id="B2",
        r_pu=0.01,
        x_pu=0.05,
        b_pu=0.002,
        in_service=True,
    )

    ybus = YBusBuilder().build(_prepared(branches=(branch,))).toarray()
    y_series = 1.0 / complex(0.01, 0.05)

    assert ybus[0, 0] == pytest.approx(y_series + 1j * 0.001)
    assert ybus[1, 1] == pytest.approx(y_series + 1j * 0.001)
    assert ybus[0, 1] == pytest.approx(-y_series)
    assert ybus[1, 0] == pytest.approx(-y_series)


def test_transformer_stamp_preserves_tap_and_phase_shift_in_prepared_pu_data():
    transformer = SimpleNamespace(
        branch_id="T1",
        from_bus_id="B1",
        to_bus_id="B2",
        r_pu=0.01,
        x_pu=0.08,
        b_pu=0.0,
        tap=1.05,
        shift=0.125,
        in_service=True,
    )

    ybus = YBusBuilder().build(_prepared(transformers=(transformer,))).toarray()
    y_series = 1.0 / complex(0.01, 0.08)
    a = 1.05 * np.exp(1j * 0.125)

    assert ybus[0, 0] == pytest.approx(y_series / abs(a) ** 2)
    assert ybus[0, 1] == pytest.approx(-y_series / np.conj(a))
    assert ybus[1, 0] == pytest.approx(-y_series / a)
    assert ybus[1, 1] == pytest.approx(y_series)
