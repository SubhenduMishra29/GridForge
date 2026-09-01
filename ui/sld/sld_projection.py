# ============================================================
# File: ui/sld/sld_projection.py
# GridForge V2 — SLD Projection
# Author: Subhendu Mishra
# ============================================================
"""Presentation projection for an authoritative Core electrical object."""

from __future__ import annotations

from typing import Any

from ui.projection.projection import Projection


class SLDProjection(Projection):
    """Project one Core object into SLD presentation state."""

    def __init__(self, model_object: Any) -> None:
        object_id = getattr(model_object, "id", None)
        super().__init__(object_id)
        self._model_object = model_object

    @property
    def model_object(self) -> Any:
        """Return the latest authoritative model reference."""
        return self._model_object

    def update_from_model(self, model_object: Any) -> None:
        """Refresh the model reference while preserving projection identity."""
        if getattr(model_object, "id", None) != self.object_id:
            raise ValueError("SLD projection cannot change Core object identity")
        self._model_object = model_object
