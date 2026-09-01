# ============================================================
# File: ui/sld/sld_projection_manager.py
# GridForge V2 — SLD Projection Manager
# Author: Subhendu Mishra
# ============================================================
"""Coordinate SLD model projections without owning Core truth."""

from __future__ import annotations

from typing import Any

from ui.projection.projection_registry import ProjectionRegistry
from ui.sld.sld_projection import SLDProjection


class SLDProjectionManager:
    """Own the lifecycle of SLD projections for a presentation surface."""

    def __init__(self, registry: ProjectionRegistry | None = None) -> None:
        self._registry = registry or ProjectionRegistry()

    def project(self, model_object: Any) -> SLDProjection:
        """Create or refresh the projection for one Core model object."""
        object_id = getattr(model_object, "id", None)
        if not isinstance(object_id, str) or not object_id:
            raise ValueError("SLD model object must provide a non-empty id")

        existing = self._registry.get(object_id)
        if existing is not None:
            if not isinstance(existing, SLDProjection):
                raise TypeError("Registry contains a non-SLD projection for object ID")
            existing.update_from_model(model_object)
            return existing

        projection = SLDProjection(model_object)
        self._registry.register(projection)
        return projection

    def projection(self, object_id: str) -> SLDProjection | None:
        """Return the registered SLD projection for an object ID."""
        projection = self._registry.get(object_id)
        if projection is None:
            return None
        if not isinstance(projection, SLDProjection):
            raise TypeError("Registry contains a non-SLD projection for object ID")
        return projection

    def remove(self, object_id: str) -> SLDProjection | None:
        """Remove an SLD projection from the presentation registry."""
        projection = self._registry.remove(object_id)
        if projection is None:
            return None
        if not isinstance(projection, SLDProjection):
            raise TypeError("Registry contains a non-SLD projection for object ID")
        return projection
