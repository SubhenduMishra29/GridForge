# ============================================================
# File: ui/sld/sld_projection_manager.py
# GridForge V2 — SLD Projection Manager
# Author: Subhendu Mishra
# ============================================================
"""Coordinate SLD model projections without owning Core truth."""

from __future__ import annotations

from typing import Any

from ui.projection.projection_registry import ProjectionRegistry
from ui.sld.sld_layout import SLDLayout
from ui.sld.sld_projection import SLDProjection


class SLDProjectionManager:
    """Own the lifecycle of SLD projections and presentation layout."""

    def __init__(
        self,
        registry: ProjectionRegistry | None = None,
        layout: SLDLayout | None = None,
    ) -> None:
        self._registry = registry or ProjectionRegistry()
        self._layout = layout or SLDLayout()

    @property
    def layout(self) -> SLDLayout:
        """Return the presentation-only layout owned by this SLD surface."""
        return self._layout

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

    def get(self, object_id: str) -> SLDProjection | None:
        """Alias for projection lookup used by presentation clients."""
        return self.projection(object_id)

    def set_position(self, object_id: str, x: float, y: float) -> None:
        """Set presentation geometry for an existing projected object."""
        if self.projection(object_id) is None:
            raise KeyError(f"No SLD projection registered for {object_id!r}")
        self._layout.set_position(object_id, x, y)

    def remove(self, object_id: str) -> SLDProjection | None:
        """Remove an SLD projection and its associated layout state."""
        projection = self._registry.remove(object_id)
        if projection is None:
            return None
        if not isinstance(projection, SLDProjection):
            raise TypeError("Registry contains a non-SLD projection for object ID")
        self._layout.remove(object_id)
        return projection
