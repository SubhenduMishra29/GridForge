# ============================================================
# File: tests/ui/sld/test_sld_layout.py
# GridForge V2 — SLD Layout Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import pytest

from ui.sld.sld_layout import SLDLayout


def test_layout_stores_position_by_stable_object_id() -> None:
    layout = SLDLayout()

    layout.set_position("BUS-001", 100.0, 200.0)

    assert layout.position("BUS-001") == (100.0, 200.0)


def test_layout_returns_none_for_unknown_object() -> None:
    assert SLDLayout().position("MISSING") is None


def test_layout_rejects_invalid_object_id() -> None:
    with pytest.raises(ValueError):
        SLDLayout().set_position("", 1.0, 2.0)
