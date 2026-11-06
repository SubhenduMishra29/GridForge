from __future__ import annotations

from core.application.read_models import ElementReadModel
from ui.projection.projection_registry import ProjectionDomain
from ui.sld.sld_projection_manager import SLDProjectionManager


def _model(object_id="BUS-001"):
    return ElementReadModel(object_id, "BUS", {"name": "Bus"}, (), {})


def test_manager_creates_and_registers_projection():
    manager = SLDProjectionManager()
    projection = manager.project(_model())
    assert projection.object_id == "BUS-001"
    assert manager.projection("BUS-001") is projection


def test_manager_refreshes_existing_projection_without_replacing_it():
    manager = SLDProjectionManager()
    projection = manager.project(_model())
    refreshed = manager.project(ElementReadModel("BUS-001", "BUS", {"name": "Updated"}, (), {}))
    assert refreshed is projection
    assert projection.state is not None
    assert projection.state.labels == ("Updated",)


def test_manager_removes_projection():
    manager = SLDProjectionManager()
    manager.project(_model())
    removed = manager.remove("BUS-001", domain=ProjectionDomain.NETWORK)
    assert removed is not None
    assert manager.projection("BUS-001") is None
