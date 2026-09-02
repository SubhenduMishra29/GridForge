# ============================================================
# File: ui/sld/sld_projection.py
# GridForge V2 — SLD Projection
# Author: Subhendu Mishra
# ============================================================
"""SLD presentation projection backed by Application read data."""

from __future__ import annotations

from core.application.read_models import ElementReadModel

from ui.projection.projection import Projection
from ui.projection.projection_state import ProjectionState


class SLDProjection(Projection):
    """Project one immutable Application element snapshot into SLD state."""

    def __init__(self, read_model: ElementReadModel) -> None:
        super().__init__(read_model.object_id)
        self.update_from_read_model(read_model)

    def update_from_read_model(self, read_model: ElementReadModel) -> None:
        """Refresh this projection from an Application read snapshot."""
        if read_model.object_id != self.object_id:
            raise ValueError("SLD projection cannot change object identity")

        labels = tuple(
            str(value)
            for _, value in sorted(read_model.labels.items())
        )
        self.set_state(
            ProjectionState(
                object_id=read_model.object_id,
                display_type=read_model.element_type,
                labels=labels,
                connectivity_refs=read_model.connectivity_refs,
            )
        )


__all__ = ["SLDProjection"]
