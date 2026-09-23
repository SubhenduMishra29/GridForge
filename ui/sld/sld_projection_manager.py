# ============================================================
# File: ui/sld/sld_projection_manager.py
# GridForge V2 — SLD Projection Manager
# Author: Subhendu Mishra
# ============================================================
"""Coordinate SLD projections without owning document geometry."""

from __future__ import annotations

from core.application.read_models import ElementReadModel, NetworkReadModel, ProtectionReadModel

from ui.projection.projection_registry import ProjectionDomain, ProjectionRegistry
from ui.sld.sld_layout import SLDLayout
from ui.sld.sld_projection import SLDProjection


class SLDProjectionManager:
    """Own SLD projection lifecycle and domain-scoped reconciliation."""

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

    def project(self, read_model: ElementReadModel, *, domain: ProjectionDomain = ProjectionDomain.NETWORK) -> SLDProjection:
        """Create or refresh one projection in an explicit presentation domain."""
        if not isinstance(read_model, ElementReadModel):
            raise TypeError("SLD projection requires an ElementReadModel")
        if not isinstance(domain, ProjectionDomain):
            raise TypeError("domain must be a ProjectionDomain")

        existing = self._registry.get(read_model.object_id)
        if existing is not None:
            existing_domain = self._registry.domain_of(read_model.object_id)
            if existing_domain is not domain:
                raise ValueError(
                    f"Projection {read_model.object_id!r} already belongs to "
                    f"{existing_domain.value if existing_domain else 'unknown'} domain"
                )
            if not isinstance(existing, SLDProjection):
                raise TypeError("Registry contains a non-SLD projection for object ID")
            existing.update_from_read_model(read_model)
            return existing

        projection = SLDProjection(read_model)
        self._registry.register(projection, domain)
        return projection

    def project_network_element(self, read_model: ElementReadModel) -> SLDProjection:
        """Project one network-domain Application read model."""
        return self.project(read_model, domain=ProjectionDomain.NETWORK)

    def project_protection_element(self, read_model: ElementReadModel) -> SLDProjection:
        """Project one protection-domain Application read model."""
        return self.project(read_model, domain=ProjectionDomain.PROTECTION)

    def project_network(self, read_model: NetworkReadModel) -> tuple[SLDProjection, ...]:
        """Project a complete Application network snapshot deterministically."""
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")
        return tuple(self.project_network_element(element) for element in read_model.elements)

    def project_protection(self, read_model: NetworkReadModel) -> tuple[SLDProjection, ...]:
        """Project an adapted protection-domain snapshot deterministically."""
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")
        return tuple(self.project_protection_element(element) for element in read_model.elements)

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

    def reconcile_network(self, active_ids: set[str] | frozenset[str]) -> tuple[str, ...]:
        """Remove only stale projections owned by the network domain."""
        if not isinstance(active_ids, (set, frozenset)):
            raise TypeError("active_ids must be a set or frozenset")
        removed: list[str] = []
        for object_id in self._registry.object_ids(ProjectionDomain.NETWORK):
            if object_id not in active_ids:
                self._registry.remove(object_id, ProjectionDomain.NETWORK)
                removed.append(object_id)
        return tuple(removed)

    def reconcile_protection(self, active_ids: set[str] | frozenset[str]) -> tuple[str, ...]:
        """Remove only stale projections owned by the protection domain."""
        if not isinstance(active_ids, (set, frozenset)):
            raise TypeError("active_ids must be a set or frozenset")
        removed: list[str] = []
        for object_id in self._registry.object_ids(ProjectionDomain.PROTECTION):
            if object_id not in active_ids:
                self._registry.remove(object_id, ProjectionDomain.PROTECTION)
                removed.append(object_id)
        return tuple(removed)

    def clear(self) -> None:
        """Clear all projection-domain state at the lifecycle boundary."""
        self._registry.clear()

    def arrange(self, object_ids: tuple[str, ...] | list[str]) -> tuple:
        """Generate deterministic dummy placements without persisting them."""
        return self._layout.arrange(object_ids)

    def remove(self, object_id: str, *, domain: ProjectionDomain | None = None) -> SLDProjection | None:
        """Remove an SLD projection, optionally constrained to its domain."""
        projection = self._registry.remove(object_id, domain)
        if projection is None:
            return None
        if not isinstance(projection, SLDProjection):
            raise TypeError("Registry contains a non-SLD projection for object ID")
        return projection


__all__ = ["SLDProjectionManager"]
