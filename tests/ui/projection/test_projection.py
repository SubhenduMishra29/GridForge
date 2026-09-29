from __future__ import annotations

import pytest

from core.application.read_models import ElementReadModel
from ui.projection.projection import Projection


class ConcreteProjection(Projection):
    def update_from_read_model(self, read_model: ElementReadModel) -> None:
        self.set_state(
            __import__("ui.projection.projection_state", fromlist=["ProjectionState"]).ProjectionState(
                object_id=read_model.object_id,
                display_type=read_model.element_type,
                labels=tuple(read_model.labels.values()),
                connectivity_refs=read_model.connectivity_refs,
            )
        )


def _model(object_id="BUS-001"):
    return ElementReadModel(object_id, "BUS", {"name": "Bus"}, (), {})


def test_projection_exposes_stable_object_id():
    projection = ConcreteProjection("BUS-001")
    assert projection.object_id == "BUS-001"


def test_projection_rejects_empty_object_id():
    with pytest.raises(ValueError):
        ConcreteProjection("")


def test_projection_updates_from_authoritative_read_model():
    projection = ConcreteProjection("BUS-001")
    projection.update_from_read_model(_model())
    assert projection.state is not None
    assert projection.state.object_id == "BUS-001"


def test_projection_rejects_identity_change():
    projection = ConcreteProjection("BUS-001")
    with pytest.raises(ValueError):
        projection.update_from_read_model(_model("BUS-002"))
