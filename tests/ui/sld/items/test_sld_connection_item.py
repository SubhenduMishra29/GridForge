# ============================================================
# File: tests/ui/sld/items/test_sld_connection_item.py
# GridForge V2 — SLD Connection Item Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from ui.sld.items.sld_connection_item import SLDConnectionItem


def test_connection_item_exposes_stable_connection_identity() -> None:
    item = SLDConnectionItem("CONN-001", "BUS-001", "BUS-002")

    assert item.object_id == "CONN-001"
    assert item.source_object_id == "BUS-001"
    assert item.target_object_id == "BUS-002"


def test_connection_item_tracks_visual_endpoints() -> None:
    item = SLDConnectionItem("CONN-001", "BUS-001", "BUS-002")

    item.set_visual_endpoints(10.0, 20.0, 100.0, 200.0)

    assert item.visual_endpoints() == ((10.0, 20.0), (100.0, 200.0))
