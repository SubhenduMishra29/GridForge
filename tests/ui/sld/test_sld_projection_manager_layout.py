from __future__ import annotations

from core.application.read_models import ElementReadModel
from ui.sld.sld_projection_manager import SLDProjectionManager


def _model(object_id="BUS-001"):
    return ElementReadModel(object_id, "BUS", {"name": "Bus"}, (), {})


def test_manager_can_derive_presentation_positions_for_registered_projection():
    manager = SLDProjectionManager()
    manager.project(_model())
    placements = manager.arrange(("BUS-001",))
    assert placements[0].object_id == "BUS-001"
    assert placements[0].x == 0.0


def test_manager_removes_projection_and_layout_is_derived_state():
    manager = SLDProjectionManager()
    manager.project(_model())
    manager.remove("BUS-001")
    assert manager.get("BUS-001") is None
    assert manager.arrange(("BUS-001",))[0].x == 0.0
