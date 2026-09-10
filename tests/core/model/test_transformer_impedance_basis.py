# ============================================================
# File: tests/core/model/test_transformer_impedance_basis.py
# GridForge V2 — Transformer Impedance Basis Contract Tests
# Author: Subhendu Mishra
# ============================================================

import pytest

from core.model.transformer import Transformer


def test_transformer_requires_explicit_impedance_basis() -> None:
    with pytest.raises(TypeError):
        Transformer(id="T1", r=0.01, x=0.10)


def test_transformer_requires_explicit_original_base() -> None:
    with pytest.raises(ValueError, match="base MVA"):
        Transformer(id="T1", r=0.01, x=0.10, impedance_basis="pu")


def test_transformer_preserves_declared_impedance_basis_and_base() -> None:
    transformer = Transformer(
        id="T2",
        r=0.01,
        x=0.10,
        b=0.0,
        impedance_basis="pu",
        rate_mva=25.0,
        impedance_base_voltage_kv=11.0,
        tap=1.02,
        shift=0.05,
    )

    assert transformer.impedance_basis == "pu"
    assert transformer.impedance_base_mva == 25.0
    assert transformer.impedance_base_voltage_kv == 11.0
    assert transformer.rated_mva == 25.0
    assert transformer.r == 0.01
    assert transformer.x == 0.10
    assert transformer.tap == 1.02
    assert transformer.shift == 0.05
    assert transformer.summary()["impedance_basis"] == "pu"


def test_transformer_engineering_basis_requires_reference_voltage() -> None:
    with pytest.raises(ValueError, match="impedance_base_voltage_kv"):
        Transformer(id="T3", r=0.1, x=0.2, impedance_basis="engineering", rate_mva=10.0)


def test_transformer_accepts_explicit_engineering_reference() -> None:
    transformer = Transformer(
        id="T4",
        r=0.5,
        x=2.0,
        b=0.0,
        impedance_basis="engineering",
        rate_mva=10.0,
        impedance_base_voltage_kv=11.0,
    )
    assert transformer.impedance_basis == "engineering"
    assert transformer.impedance_base_mva == 10.0
    assert transformer.impedance_base_voltage_kv == 11.0


def test_transformer_rejects_unknown_impedance_basis() -> None:
    with pytest.raises(ValueError):
        Transformer(
            id="T5",
            r=0.01,
            x=0.10,
            impedance_basis="unknown",
            rate_mva=10.0,
            impedance_base_voltage_kv=11.0,
        )
