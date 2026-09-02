# ============================================================
# File: tests/ui/projection/test_projection_context.py
# GridForge V2 — Projection Context Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import pytest

from ui.projection.projection_context import ProjectionContext


def test_context_resolves_through_supplied_read_boundary() -> None:
    objects = {"BUS-001": object()}
    context = ProjectionContext(objects.get)

    assert context.resolve("BUS-001") is objects["BUS-001"]
    assert context.resolve("MISSING") is None


def test_context_requires_callable_resolver() -> None:
    with pytest.raises(TypeError):
        ProjectionContext(None)
