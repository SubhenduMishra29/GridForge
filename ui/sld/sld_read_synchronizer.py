# ============================================================
# File: ui/sld/sld_read_synchronizer.py
# GridForge V2 — SLD Read Synchronizer
# Author: Subhendu Mishra
# ============================================================
"""Project Application read models into SLD presentation projections only."""

from __future__ import annotations

from typing import Any

from core.application.read_models import ElementReadModel, NetworkReadModel, ProtectionReadModel

from ui.projection.projection_registry import ProjectionDomain
from .sld_projection import SLDProjection
from .sld_vocabulary import semantic_type
from .sld_projection_manager import SLDProjectionManager
from .sld_read_adapter import SLDReadAdapter


class SLDReadSynchronizer:
    """Project Application read data without persistent SLDDocument dependencies."""

    def __init__(
        self,
        projection_manager: SLDProjectionManager,
        application: Any = None,
    ) -> None:
        if not isinstance(projection_manager, SLDProjectionManager):
            raise TypeError("projection_manager must be an SLDProjectionManager")
        self._projection_manager = projection_manager
        self._read_adapter = SLDReadAdapter()
        self._application = application

    @property
    def projection_manager(self) -> SLDProjectionManager:
        return self._projection_manager

    @property
    def application(self) -> Any:
        return self._application

    def attach_application(self, application: Any) -> None:
        if application is None:
            raise TypeError("application must not be None")
        self._application = application

    def detach_application(self) -> Any:
        application = self._application
        self._application = None
        return application

    def synchronize_network_from_application(self) -> tuple[SLDProjection, ...]:
        """Synchronize the network projection from the Application read model."""
        return self.synchronize_network(self._require_application().read_network())

    def synchronize_protection_from_application(self) -> tuple[SLDProjection, ...]:
        """Synchronize the protection projection from the Application read model."""
        return self.synchronize_protection(self._require_application().read_protection())

    def synchronize_element_from_application(
        self,
        element_type: str,
        object_id: str,
    ) -> SLDProjection:
        """Synchronize one network projection from the Application read model."""
        read_model = self._require_application().read_element(element_type, object_id)
        return self.synchronize_element(read_model)

    def synchronize_network(
        self,
        read_model: NetworkReadModel,
    ) -> tuple[SLDProjection, ...]:
        """Synchronize only the network-owned projection domain."""
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")
        adapted = self._read_adapter.network(read_model)
        projections = self._projection_manager.project_network(adapted)
        active_ids = {element.object_id for element in adapted.elements}
        self._projection_manager.reconcile_network(active_ids)
        return projections

    def synchronize_protection(
        self,
        read_model: ProtectionReadModel,
    ) -> tuple[SLDProjection, ...]:
        """Synchronize only the protection-owned projection domain."""
        if not isinstance(read_model, ProtectionReadModel):
            raise TypeError("read_model must be a ProtectionReadModel")
        adapted = self._read_adapter.protection(read_model)
        projections = self._projection_manager.project_protection(adapted)
        active_ids = {element.object_id for element in adapted.elements}
        self._projection_manager.reconcile_protection(active_ids)
        return projections

    def synchronize_element(
        self,
        read_model: ElementReadModel,
    ) -> SLDProjection:
        """Synchronize one NETWORK-owned projection.

        Relay is deliberately excluded from this generic path. A Relay
        ElementReadModel is only valid here when its presentation ownership
        is NETWORK, which the frozen contract does not permit. Protection
        Relay presentation must enter through synchronize_protection(), where
        SLDReadAdapter.protection() establishes the PROTECTION-domain source.
        """
        if not isinstance(read_model, ElementReadModel):
            raise TypeError("read_model must be an ElementReadModel")
        if semantic_type(read_model.element_type) == "RELAY":
            raise ValueError(
                "Relay presentation is owned by the protection projection "
                "domain; use synchronize_protection() instead."
            )
        adapted = self._read_adapter.element(read_model)
        return self._projection_manager.project_network_element(adapted)

    def _require_application(self) -> Any:
        if self._application is None:
            raise RuntimeError("SLD Application read facade is not configured")
        return self._application


__all__ = ["SLDReadSynchronizer"]
