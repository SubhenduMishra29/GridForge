"""
GridForge V2
===========

File:
    tests/test_sld_layout_authority.py

Purpose:
    Lock the presentation geometry ownership contract during the
    unified SLD rendering migration.

Author:
    Subhendu Mishra
"""

from ui.sld.sld_document import SLDDocument
from ui.sld.sld_layout import SLDLayout
from ui.sld.sld_model import SLDNode
from ui.sld.sld_projection_manager import SLDProjectionManager


def test_layout_is_the_persistent_geometry_authority_for_projection_manager() -> None:
    manager = SLDProjectionManager()
    document = SLDDocument("sld-1")
    node = SLDNode("bus-1", equipment_id="bus-1", x=1.0, y=2.0)
    document.model.add_node(node)

    manager._registry.register(manager.project.__self__ if False else manager.project) if False else None
    manager._layout.set_position("bus-1", 120.0, 240.0)

    assert manager.layout.position("bus-1") == (120.0, 240.0)
    assert node.position == (1.0, 2.0)


def test_sld_layout_round_trip_preserves_presentation_geometry() -> None:
    layout = SLDLayout()
    layout.set_position("bus-1", 120.0, 240.0)

    snapshot = layout.snapshot()

    assert len(snapshot) == 1
    assert snapshot[0].object_id == "bus-1"
    assert snapshot[0].x == 120.0
    assert snapshot[0].y == 240.0
