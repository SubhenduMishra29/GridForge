# ============================================================
# File: tests/ui/projection/test_projection.py
# GridForge V2 — Projection Contract Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import pytest

from ui.projection.projection import Projection


class ConcreteProjection(Projection):
    def __init__(self, object_id: str) -> None:
        super().__init__(object_id)
        self.updated_with = None

    def update_from_model(self, model_object) -> None:
        self.updated_with = model_object


def test_projection_exposes_stable_object_id() -> None:
    projection = ConcreteProjection("BUS-001")

    assert projection.object_id == "BUS-001"


def test_projection_rejects_empty_object_id() -> None:
    with pytest.raises(ValueError):
        ConcreteProjection("")


def test_projection_updates_from_authoritative_model_object() -> None:
    projection = ConcreteProjection("BUS-001")
    model_object = object()

    projection.update_from_model(model_object)

    assert projection.updated_with is model_object
