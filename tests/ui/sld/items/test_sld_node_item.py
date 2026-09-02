# ============================================================
# File: tests/ui/sld/items/test_sld_node_item.py
# GridForge V2 — SLD Node Item Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from ui.sld.items.sld_node_item import SLDNodeItem


def test_node_item_exposes_projection_identity() -> None:
    item = SLDNodeItem("BUS-001")

    assert item.object_id == "BUS-001"


def test_node_item_tracks_visual_position() -> None:
    item = SLDNodeItem("BUS-001")

    item.set_visual_position(10.0, 20.0)

    assert item.visual_position() == (10.0, 20.0)
