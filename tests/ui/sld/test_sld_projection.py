# ============================================================
# File: tests/ui/sld/test_sld_projection.py
# GridForge V2 — SLD Projection Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from ui.sld.sld_projection import SLDProjection


class ModelObject:
    id = "BUS-001"


def test_sld_projection_tracks_core_object_id() -> None:
    projection = SLDProjection(ModelObject())

    assert projection.object_id == "BUS-001"


def test_sld_projection_refreshes_model_reference() -> None:
    first = ModelObject()
    second = ModelObject()
    second.id = "BUS-002"
    projection = SLDProjection(first)

    projection.update_from_model(second)

    assert projection.object_id == "BUS-001"
    assert projection.model_object is second
