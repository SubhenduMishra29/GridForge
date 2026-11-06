from __future__ import annotations

import pytest

from ui.projection.projection_registry import ProjectionDomain, ProjectionRegistry


class FakeProjection:
    def __init__(self, object_id: str) -> None:
        self.object_id = object_id


def test_registry_keys_projections_by_stable_core_object_id():
    registry = ProjectionRegistry()
    projection = FakeProjection("BUS-001")
    registry.register(projection, ProjectionDomain.NETWORK)
    assert registry.get("BUS-001") is projection
    assert registry.contains("BUS-001", ProjectionDomain.NETWORK)


def test_registry_rejects_duplicate_core_object_id():
    registry = ProjectionRegistry()
    registry.register(FakeProjection("BUS-001"), ProjectionDomain.NETWORK)
    with pytest.raises(ValueError, match="BUS-001"):
        registry.register(FakeProjection("BUS-001"), ProjectionDomain.NETWORK)


def test_registry_remove_returns_projection_and_forgets_id():
    registry = ProjectionRegistry()
    projection = FakeProjection("BUS-001")
    registry.register(projection, ProjectionDomain.NETWORK)
    removed = registry.remove("BUS-001", ProjectionDomain.NETWORK)
    assert removed is projection
    assert registry.contains("BUS-001") is False
    assert registry.get("BUS-001") is None
