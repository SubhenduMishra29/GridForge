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


def test_transformer_preserves_declared_impedance_basis() -> None:
    transformer = Transformer(
        id="T2",
        r=0.01,
        x=0.10,
        b=0.0,
        impedance_basis="pu",
        tap=1.02,
        shift=0.05,
    )

    assert transformer.impedance_basis == "pu"
    assert transformer.r == 0.01
    assert transformer.x == 0.10
    assert transformer.tap == 1.02
    assert transformer.shift == 0.05
    assert transformer.summary()["impedance_basis"] == "pu"


def test_transformer_rejects_unknown_impedance_basis() -> None:
    with pytest.raises(ValueError):
        Transformer(
            id="T3",
            r=0.01,
            x=0.10,
            impedance_basis="unknown",
        )
