# ============================================================
# File: tests/ui/projection/test_projection_registry.py
# GridForge V2 — Projection Registry Contract Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import pytest

from ui.projection.projection_registry import ProjectionRegistry


class FakeProjection:
    """Minimal projection contract used by registry tests."""

    def __init__(self, object_id: str) -> None:
        self.object_id = object_id


def test_registry_keys_projections_by_stable_core_object_id() -> None:
    registry = ProjectionRegistry()
    projection = FakeProjection("BUS-001")

    registry.register(projection)

    assert registry.get("BUS-001") is projection
    assert registry.contains("BUS-001") is True


def test_registry_rejects_duplicate_core_object_id() -> None:
    registry = ProjectionRegistry()
    registry.register(FakeProjection("BUS-001"))

    with pytest.raises(ValueError, match="BUS-001"):
        registry.register(FakeProjection("BUS-001"))


def test_registry_remove_returns_projection_and_forgets_id() -> None:
    registry = ProjectionRegistry()
    projection = FakeProjection("BUS-001")
    registry.register(projection)

    removed = registry.remove("BUS-001")

    assert removed is projection
    assert registry.contains("BUS-001") is False
    assert registry.get("BUS-001") is None
