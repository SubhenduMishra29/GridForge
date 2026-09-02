# ============================================================
# File: ui/sld/sld_read_synchronizer.py
# GridForge V2 — SLD Read Synchronizer
# Author: Subhendu Mishra
# ============================================================
"""Synchronize Application read snapshots into the SLD document model.

This presentation-owned adapter consumes immutable Application snapshots and
updates structural SLD state. Existing SLD graphical positions are preserved;
network synchronization never replaces saved presentation geometry.
"""

from __future__ import annotations

from core.application.read_models import ElementReadModel, NetworkReadModel

from .sld_document import SLDDocument
from .sld_model import SLDConnection, SLDNode
from .sld_projection_manager import SLDProjectionManager


_PROJECTION_SOURCE = "application_read_model"
_BRANCH_TYPES = frozenset({"lines", "cables", "transformers"})


class SLDReadSynchronizer:
    """Reconcile Application read data with an SLD document."""

    def __init__(self, projection_manager: SLDProjectionManager) -> None:
        if not isinstance(projection_manager, SLDProjectionManager):
            raise TypeError("projection_manager must be an SLDProjectionManager")
        self._projection_manager = projection_manager

    @property
    def projection_manager(self) -> SLDProjectionManager:
        return self._projection_manager

    def synchronize_network(
        self,
        document: SLDDocument,
        read_model: NetworkReadModel,
    ) -> tuple[SLDNode, ...]:
        """Reconcile read-side elements and authoritative branch connectivity."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")

        self._projection_manager.project_network(read_model)
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
        self._synchronize_connections(document, read_model)
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
            node = SLDNode(
                node_id=read_model.object_id,
                equipment_id=read_model.object_id,
                x=0.0,
                y=0.0,
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

    def _synchronize_connections(
        self,
        document: SLDDocument,
        read_model: NetworkReadModel,
    ) -> None:
        """Project unambiguous branch endpoint identities into SLD structure."""
        active_connection_ids: set[str] = set()
        active_node_ids = {node.node_id for node in document.model.nodes}

        for element in read_model.elements:
            if element.element_type not in _BRANCH_TYPES:
                continue

            source_id = element.attributes.get("endpoint_from_id")
            target_id = element.attributes.get("endpoint_to_id")
            if not isinstance(source_id, str) or not isinstance(target_id, str):
                continue
            if source_id not in active_node_ids or target_id not in active_node_ids:
                continue

            connection_id = element.object_id
            active_connection_ids.add(connection_id)
            connection = document.model.get_connection_optional(connection_id)
            properties = {
                "projection_source": _PROJECTION_SOURCE,
                "element_type": element.element_type,
                "equipment_id": element.object_id,
            }

            if connection is None:
                document.model.add_connection(
                    SLDConnection(
                        connection_id=connection_id,
                        source_node_id=source_id,
                        target_node_id=target_id,
                        properties=properties,
                    )
                )
            elif (
                connection.source_node_id != source_id
                or connection.target_node_id != target_id
            ):
                document.model.remove_connection(connection_id)
                document.model.add_connection(
                    SLDConnection(
                        connection_id=connection_id,
                        source_node_id=source_id,
                        target_node_id=target_id,
                        properties=properties,
                    )
                )
            else:
                connection.properties.update(properties)

        for connection in tuple(document.model.connections):
            if (
                connection.properties.get("projection_source") == _PROJECTION_SOURCE
                and connection.connection_id not in active_connection_ids
            ):
                document.model.remove_connection(connection.connection_id)


__all__ = ["SLDReadSynchronizer"]
