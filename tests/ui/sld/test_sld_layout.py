from __future__ import annotations

import pytest

from ui.sld.sld_layout import SLDLayout


def test_layout_arranges_stable_object_ids():
    placements = SLDLayout().arrange(["BUS-001", "BUS-002"])
    assert placements[0].object_id == "BUS-001"
    assert placements[0].x == 0.0
    assert placements[1].x == 160.0


def test_layout_applies_external_geometry_without_persisting_it():
    placements = SLDLayout().apply({"BUS-001": (100.0, 200.0)})
    assert len(placements) == 1
    assert placements[0].object_id == "BUS-001"
    assert placements[0].x == 100.0
    assert placements[0].y == 200.0


def test_layout_rejects_invalid_object_id():
    with pytest.raises(ValueError):
        SLDLayout().apply({"": (1.0, 2.0)})
