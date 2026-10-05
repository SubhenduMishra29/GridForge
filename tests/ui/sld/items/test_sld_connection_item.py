# ============================================================
# File: tests/ui/sld/items/test_sld_connection_item.py
# GridForge V2 — SLD Connection Item Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from ui.core.qt import QPointF, QGraphicsItem
from ui.sld.items.sld_connection_item import SLDConnectionItem


def test_connection_item_preserves_distinct_presentation_and_core_identity() -> None:
    item = SLDConnectionItem("CONN-001", "BUS-001", "BUS-002", core_connection_id="SIMPLE-WIRE-001")
    assert item.presentation_id == "CONN-001"
    assert item.core_connection_id == "SIMPLE-WIRE-001"
    assert item.object_id == "SIMPLE-WIRE-001"
    assert item.source_object_id == "BUS-001"
    assert item.target_object_id == "BUS-002"


def test_connection_item_tracks_visual_endpoints() -> None:
    item = SLDConnectionItem("CONN-001", "BUS-001", "BUS-002")
    item.set_visual_route(QPointF(10.0, 20.0), QPointF(100.0, 200.0))
    assert item.visual_endpoints() == ((10.0, 20.0), (100.0, 200.0))


def test_connection_item_never_synthesizes_core_identity() -> None:
    item = SLDConnectionItem("CONN-001", "BUS-001", "BUS-002")
    assert item.presentation_id == "CONN-001"
    assert item.core_connection_id is None
    assert item.object_id is None
    assert not bool(item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)


def test_orphan_connection_route_edit_is_non_interactive() -> None:
    item = SLDConnectionItem("CONN-001", "BUS-001", "BUS-002")
    item.set_visual_route(QPointF(0.0, 0.0), QPointF(10.0, 10.0), ((5.0, 5.0),))
    try:
        item.set_bend(0, 6.0, 6.0)
    except RuntimeError as exc:
        assert "explicit Core connection identity" in str(exc)
    else:
        raise AssertionError("orphan SLD connection must not permit route editing")
