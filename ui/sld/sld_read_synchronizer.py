# ============================================================
# File: ui/sld/sld_read_synchronizer.py
# GridForge V2 — SLD Read Synchronizer
# Author: Subhendu Mishra
# ============================================================
"""Synchronize Application read snapshots into the SLD document model.

This adapter is presentation-owned. It consumes immutable Application read
models and updates only structural SLD document state. It never receives or
stores Core electrical model objects.
"""

from __future__ import annotations

from core.application.read_models import ElementReadModel, NetworkReadModel

from .sld_document import SLDDocument
from .sld_model import SLDNode
from .sld_projection_manager import SLDProjectionManager


_PROJECTION_SOURCE = "application_read_model"


class SLDReadSynchronizer:
    """Reconcile Application read data with an SLD document."""

    def __init__(
        self,
        projection_manager: SLDProjectionManager,
    ) -> None:
        if not isinstance(projection_manager, SLDProjectionManager):
            raise TypeError("projection_manager must be an SLDProjectionManager")
        self._projection_manager = projection_manager

    @property
    def projection_manager(self) -> SLDProjectionManager:
        """Return the projection manager used for read-side state."""
        return self._projection_manager

    def synchronize_network(
        self,
        document: SLDDocument,
        read_model: NetworkReadModel,
    ) -> tuple[SLDNode, ...]:
        """Reconcile all read-side elements into the SLD document."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")

        projected = self._projection_manager.project_network(read_model)
        active_ids = {element.object_id for element in read_model.elements}

        for node in tuple(document.model.nodes):
            if (
                node.properties.get("projection_source") == _PROJECTION_SOURCE
                and node.equipment_id not in active_ids
            ):
                document.model.remove_node(node.node_id)

        nodes = tuple(
            self._synchronize_element(document, element)
            for element in read_model.elements
        )
        # Do not call document.mark_clean() here. Read synchronization is an
        # external authoritative update, not a user presentation save. A
        # user's SLD layout/editing dirtiness must survive a Core refresh.
        return nodes

    def synchronize_element(
        self,
        document: SLDDocument,
        read_model: ElementReadModel,
    ) -> SLDNode:
        """Reconcile one Application element into the SLD document."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        if not isinstance(read_model, ElementReadModel):
            raise TypeError("read_model must be an ElementReadModel")

        self._projection_manager.project(read_model)
        return self._synchronize_element(document, read_model)

    def _synchronize_element(
        self,
        document: SLDDocument,
        read_model: ElementReadModel,
    ) -> SLDNode:
        node = document.model.get_node_optional(read_model.object_id)
        if node is None:
            position = self._projection_manager.layout.position(read_model.object_id)
            x, y = position if position is not None else (0.0, 0.0)
            node = SLDNode(
                node_id=read_model.object_id,
                equipment_id=read_model.object_id,
                x=x,
                y=y,
                properties={
                    "projection_source": _PROJECTION_SOURCE,
                    "element_type": read_model.element_type,
                    "labels": dict(read_model.labels),
                    "attributes": dict(read_model.attributes),
                },
            )
            document.model.add_node(node)
            return node

        if node.equipment_id not in (None, read_model.object_id):
            raise ValueError(
                f"SLD node ID conflicts with equipment ID: {read_model.object_id!r}"
            )

        node.equipment_id = read_model.object_id
        node.properties.update(
            {
                "projection_source": _PROJECTION_SOURCE,
                "element_type": read_model.element_type,
                "labels": dict(read_model.labels),
                "attributes": dict(read_model.attributes),
            }
        )
        return node


__all__ = ["SLDReadSynchronizer"]
