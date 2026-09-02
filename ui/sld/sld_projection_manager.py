# ============================================================
# File: ui/sld/sld_projection_manager.py
# GridForge V2 — SLD Projection Manager
# Author: Subhendu Mishra
# ============================================================
"""Coordinate SLD projections without owning document geometry."""

from __future__ import annotations

from core.application.read_models import ElementReadModel, NetworkReadModel

from ui.projection.projection_registry import ProjectionRegistry
from ui.sld.sld_layout import SLDLayout
from ui.sld.sld_projection import SLDProjection


class SLDProjectionManager:
    """Own SLD projection lifecycle without owning Core or saved geometry."""

    def __init__(
        self,
        registry: ProjectionRegistry | None = None,
        layout: SLDLayout | None = None,
    ) -> None:
        self._registry = registry or ProjectionRegistry()
        self._layout = layout or SLDLayout()

    @property
    def layout(self) -> SLDLayout:
        """Return the presentation-only layout policy."""
        return self._layout

    def project(self, read_model: ElementReadModel) -> SLDProjection:
        """Create or refresh one projection from an Application read model."""
        if not isinstance(read_model, ElementReadModel):
            raise TypeError("SLD projection requires an ElementReadModel")

        existing = self._registry.get(read_model.object_id)
        if existing is not None:
            if not isinstance(existing, SLDProjection):
                raise TypeError("Registry contains a non-SLD projection for object ID")
            existing.update_from_read_model(read_model)
            return existing

        projection = SLDProjection(read_model)
        self._registry.register(projection)
        return projection

    def project_network(self, read_model: NetworkReadModel) -> tuple[SLDProjection, ...]:
        """Project a complete Application network snapshot deterministically."""
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")
        return tuple(self.project(element) for element in read_model.elements)

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

    def arrange(self, object_ids: tuple[str, ...] | list[str]) -> tuple:
        """Generate deterministic dummy placements without persisting them."""
        return self._layout.arrange(object_ids)

    def remove(self, object_id: str) -> SLDProjection | None:
        """Remove an SLD projection."""
        projection = self._registry.remove(object_id)
        if projection is None:
            return None
        if not isinstance(projection, SLDProjection):
            raise TypeError("Registry contains a non-SLD projection for object ID")
        return projection


__all__ = ["SLDProjectionManager"]
