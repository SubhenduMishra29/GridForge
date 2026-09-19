# ============================================================
# File: ui/sld/sld_read_synchronizer.py
# GridForge V2 — SLD Read Synchronizer
# Author: Subhendu Mishra
# ============================================================
"""Project Application read models into SLD presentation projections only."""

from __future__ import annotations

from typing import Any

from core.application.read_models import ElementReadModel, NetworkReadModel, ProtectionReadModel

from .sld_document import SLDDocument
from .sld_projection import SLDProjection
from .sld_projection_manager import SLDProjectionManager
from .sld_read_adapter import SLDReadAdapter
from .sld_vocabulary import semantic_type


_PROJECTION_SOURCE = "application_read_model"
_BRANCH_TYPES = frozenset({"LINE", "CABLE", "TRANSFORMER"})


class SLDReadSynchronizer:
    """Project Application read data without mutating persistent SLDDocument state."""

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

    def synchronize_network_from_application(
        self,
        document: SLDDocument,
    ) -> tuple[SLDProjection, ...]:
        return self.synchronize_network(document, self._require_application().read_network())

    def synchronize_protection_from_application(
        self,
        document: SLDDocument,
    ) -> tuple[SLDProjection, ...]:
        return self.synchronize_protection(document, self._require_application().read_protection())

    def synchronize_element_from_application(
        self,
        document: SLDDocument,
        element_type: str,
        object_id: str,
    ) -> SLDProjection:
        read_model = self._require_application().read_element(element_type, object_id)
        return self.synchronize_element(document, read_model)

    def synchronize_network(
        self,
        document: SLDDocument,
        read_model: NetworkReadModel,
    ) -> tuple[SLDProjection, ...]:
        """Synchronize the read-side projection registry; document is never mutated."""
        self._require_document(document)
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")

        adapted = self._read_adapter.network(read_model)
        projections = self._projection_manager.project_network(adapted)
        active_ids = {element.object_id for element in adapted.elements}
        for projection_id in self._projection_ids():
            if projection_id not in active_ids:
                self._projection_manager.remove(projection_id)

        self._project_connections(adapted)
        return projections

    def synchronize_protection(
        self,
        document: SLDDocument,
        read_model: ProtectionReadModel,
    ) -> tuple[SLDProjection, ...]:
        self._require_document(document)
        if not isinstance(read_model, ProtectionReadModel):
            raise TypeError("read_model must be a ProtectionReadModel")
        adapted = self._read_adapter.protection(read_model)
        return tuple(self._synchronize_element(element) for element in adapted.elements)

    def synchronize_element(
        self,
        document: SLDDocument,
        read_model: ElementReadModel,
    ) -> SLDProjection:
        self._require_document(document)
        if not isinstance(read_model, ElementReadModel):
            raise TypeError("read_model must be an ElementReadModel")
        adapted = self._read_adapter.element(read_model)
        return self._synchronize_element(adapted)

    def _require_document(self, document: SLDDocument) -> None:
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        # The document is accepted only for compatibility with existing callers.
        # It is deliberately never read or mutated by the read synchronizer.

    def _projection_ids(self) -> tuple[str, ...]:
        registry = getattr(self._projection_manager, "_registry", None)
        values = getattr(registry, "values", None)
        if not callable(values):
            return ()
        return tuple(
            projection.object_id
            for projection in tuple(values())
            if isinstance(projection, SLDProjection)
        )

    def _require_application(self) -> Any:
        if self._application is None:
            raise RuntimeError("SLD Application read facade is not configured")
        return self._application

    def _synchronize_element(self, read_model: ElementReadModel) -> SLDProjection:
        return self._projection_manager.project(read_model)

    def _project_connections(self, read_model: NetworkReadModel) -> tuple[dict[str, Any], ...]:
        """Return topology projection data without creating persistent connections."""
        projected: list[dict[str, Any]] = []
        for element in read_model.elements:
            try:
                semantic = semantic_type(element.element_type)
            except ValueError:
                continue
            if semantic not in _BRANCH_TYPES:
                continue
            source_id = element.attributes.get("endpoint_from_id")
            target_id = element.attributes.get("endpoint_to_id")
            if not isinstance(source_id, str) or not isinstance(target_id, str):
                continue
            projected.append(
                {
                    "connection_id": element.object_id,
                    "source_node_id": source_id,
                    "target_node_id": target_id,
                    "element_type": semantic,
                    "equipment_id": element.object_id,
                    "projection_source": _PROJECTION_SOURCE,
                }
            )
        return tuple(projected)


__all__ = ["SLDReadSynchronizer"]
