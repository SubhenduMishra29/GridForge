from __future__ import annotations

import pytest

from core.application.read_models import ElementReadModel
from ui.sld.sld_projection import SLDProjection


def _model(object_id="BUS-001", name="Bus"):
    return ElementReadModel(object_id, "BUS", {"name": name}, (), {})


def test_sld_projection_tracks_core_object_id():
    projection = SLDProjection(_model())
    assert projection.object_id == "BUS-001"
    assert projection.element_type == "BUS"


def test_sld_projection_refreshes_authoritative_read_model_without_replacing_identity():
    projection = SLDProjection(_model())
    projection.update_from_read_model(_model("BUS-001", "Updated"))
    assert projection.object_id == "BUS-001"
    assert projection.state is not None
    assert projection.state.labels == ("Updated",)


def test_sld_projection_rejects_identity_change():
    projection = SLDProjection(_model())
    with pytest.raises(ValueError):
        projection.update_from_read_model(_model("BUS-002"))
