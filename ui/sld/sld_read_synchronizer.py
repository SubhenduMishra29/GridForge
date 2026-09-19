# ============================================================
# File: ui/sld/sld_read_synchronizer.py
# GridForge V2 — SLD Read Synchronizer
# Author: Subhendu Mishra
# ============================================================
"""Read-only adapter from Application read models to SLD projections.

This class deliberately has no persistent SLDDocument mutation capability.
Persistent SLD edits belong exclusively to SLDService/Application commands.
"""

from __future__ import annotations

from typing import Any

from core.application.read_models import ElementReadModel, NetworkReadModel, ProtectionReadModel

from .sld_document import SLDDocument
from .sld_projection import SLDProjection
from .sld_projection_manager import SLDProjectionManager
from .sld_read_adapter import SLDReadAdapter


class SLDReadSynchronizer:
    """Project authoritative Application read data without mutating persistence."""

    TOPOLOGY_PRESENTATION_TYPES = frozenset({
        "LINE",
        "CABLE",
        "TRANSFORMER",
        "SWITCH",
        "BREAKER",
        "DISCONNECTOR",
        "FUSE",
    })

    def __init__(self, projection_manager: SLDProjectionManager, application: Any = None) -> None:
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

    def synchronize_network_from_application(self, document: SLDDocument) -> tuple[SLDProjection, ...]:
        """Compatibility-named read operation; it never mutates document."""
        return self.synchronize_network(document, self._require_application().read_network())

    def synchronize_protection_from_application(self, document: SLDDocument) -> tuple[SLDProjection, ...]:
        return self.synchronize_protection(document, self._require_application().read_protection())

    def synchronize_element_from_application(
        self,
        document: SLDDocument,
        element_type: str,
        object_id: str,
    ) -> SLDProjection:
        read_model = self._require_application().read_element(element_type, object_id)
        return self.synchronize_element(document, read_model)

    def project_network(self, read_model: NetworkReadModel) -> tuple[SLDProjection, ...]:
        """Project the complete network read model, including all topology types."""
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")
        adapted = self._read_adapter.network(read_model)
        return self._projection_manager.project_network(adapted)

    def synchronize_network(
        self,
        document: SLDDocument,
        read_model: NetworkReadModel,
    ) -> tuple[SLDProjection, ...]:
        """Legacy entry point retained as a read-only projection adapter.

        The document argument is accepted for source compatibility only. It is
        intentionally never inspected or mutated.
        """
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        return self.project_network(read_model)

    def project_protection(self, read_model: ProtectionReadModel) -> tuple[SLDProjection, ...]:
        if not isinstance(read_model, ProtectionReadModel):
            raise TypeError("read_model must be a ProtectionReadModel")
        adapted = self._read_adapter.protection(read_model)
        return self._projection_manager.project_network(adapted)

    def synchronize_protection(
        self,
        document: SLDDocument,
        read_model: ProtectionReadModel,
    ) -> tuple[SLDProjection, ...]:
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        return self.project_protection(read_model)

    def project_element(self, read_model: ElementReadModel) -> SLDProjection:
        if not isinstance(read_model, ElementReadModel):
            raise TypeError("read_model must be an ElementReadModel")
        return self._projection_manager.project(self._read_adapter.element(read_model))

    def synchronize_element(
        self,
        document: SLDDocument,
        read_model: ElementReadModel,
    ) -> SLDProjection:
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        return self.project_element(read_model)

    def _require_application(self) -> Any:
        if self._application is None:
            raise RuntimeError("SLD Application read facade is not configured")
        return self._application


__all__ = ["SLDReadSynchronizer"]
