# ============================================================
# File: tests/ui/sld/test_sld_projection_manager.py
# GridForge V2 — SLD Projection Manager Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from ui.sld.sld_projection_manager import SLDProjectionManager


class ModelObject:
    def __init__(self, object_id: str) -> None:
        self.id = object_id


def test_manager_creates_and_registers_projection() -> None:
    manager = SLDProjectionManager()
    model = ModelObject("BUS-001")

    projection = manager.project(model)

    assert projection.object_id == "BUS-001"
    assert manager.projection("BUS-001") is projection


def test_manager_refreshes_existing_projection_without_replacing_it() -> None:
    manager = SLDProjectionManager()
    first = ModelObject("BUS-001")
    second = ModelObject("BUS-001")

    projection = manager.project(first)
    refreshed = manager.project(second)

    assert refreshed is projection
    assert projection.model_object is second


def test_manager_removes_projection() -> None:
    manager = SLDProjectionManager()
    manager.project(ModelObject("BUS-001"))

    removed = manager.remove("BUS-001")

    assert removed is not None
    assert manager.projection("BUS-001") is None
