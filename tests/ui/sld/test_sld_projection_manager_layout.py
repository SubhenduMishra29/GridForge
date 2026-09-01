# ============================================================
# File: tests/ui/sld/test_sld_projection_manager_layout.py
# GridForge V2 — SLD Projection/Layout Integration Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from ui.sld.sld_layout import SLDLayout
from ui.sld.sld_projection_manager import SLDProjectionManager


class ModelObject:
    def __init__(self, object_id: str) -> None:
        self.id = object_id


def test_manager_can_position_registered_projection() -> None:
    layout = SLDLayout()
    manager = SLDProjectionManager(layout=layout)
    manager.project(ModelObject("BUS-001"))

    manager.set_position("BUS-001", 50.0, 75.0)

    assert layout.position("BUS-001") == (50.0, 75.0)


def test_manager_removes_projection_and_layout_state_together() -> None:
    layout = SLDLayout()
    manager = SLDProjectionManager(layout=layout)
    manager.project(ModelObject("BUS-001"))
    manager.set_position("BUS-001", 50.0, 75.0)

    manager.remove("BUS-001")

    assert manager.get("BUS-001") is None
    assert layout.position("BUS-001") is None
