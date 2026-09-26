# ============================================================
# File: ui/sld/sld_read_synchronizer.py
# GridForge V2 — SLD Read Synchronizer
# Author: Subhendu Mishra
# ============================================================
"""Project Application read models into SLD presentation projections only."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

from core.application.read_models import ElementReadModel, NetworkReadModel, ProtectionReadModel

from ui.projection.projection_registry import ProjectionDomain
from .sld_projection import SLDProjection
from .sld_vocabulary import semantic_type
from .sld_projection_manager import SLDProjectionManager
from .sld_document import SLDDocument
from .sld_model import SLDConnection, SLDNode, SLDEndpoint, SLDEndpointKind
from .sld_read_adapter import SLDReadAdapter


_PROJECTION_SOURCE = "application_read_model"
_PROTECTION_PROJECTION_SOURCE = "protection_read_model"


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
        document = self._require_document()
        return self.synchronize_network(document, self._require_application().read_network())

    def synchronize_protection_from_application(self) -> tuple[SLDProjection, ...]:
        """Synchronize the protection projection from the Application read model."""
        document = self._require_document()
        return self.synchronize_protection(document, self._require_application().read_protection())

    def synchronize_element_from_application(
        self,
        element_type: str,
        object_id: str,
    ) -> SLDProjection:
        """Synchronize one NETWORK projection from the Application read model."""
        read_model = self._require_application().read_element(element_type, object_id)
        if semantic_type(read_model.element_type) == "RELAY":
            raise ValueError(
                "Relay presentation is owned by the protection projection "
                "domain; use synchronize_protection() instead."
            )
        document = self._require_document()
        return self._synchronize_element(document, read_model)

    def synchronize_network(
        self,
        document: SLDDocument,
        read_model: NetworkReadModel,
        *,
        initial_positions: Mapping[str, tuple[float, float]] | None = None,
    ) -> tuple[SLDNode, ...]:
        """Reconcile network read data and branch connectivity."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")
        adapted = self._read_adapter.network(read_model)
        projections = self._projection_manager.project_network(adapted)
        active_ids = {element.object_id for element in adapted.elements}
        positions = dict(initial_positions or {})

        for node in tuple(document.model.nodes):
            if node.properties.get("projection_source") == _PROJECTION_SOURCE and node.equipment_id not in active_ids:
                self._remove_stale_projection_node(document, node)

        nodes = tuple(
            self._synchronize_element(
                document,
                element,
                initial_position=positions.get(element.object_id),
            )
            for element in adapted.elements
            if (
                document.model.get_node_by_equipment_id_optional(element.object_id) is not None
                or element.object_id in positions
            )
        )
        self._synchronize_connections(document, adapted)
        document.materialize_missing_symbol_presentations()
        self._projection_manager.reconcile_network(active_ids)
        return nodes

    def synchronize_protection(self, document: SLDDocument, read_model: ProtectionReadModel) -> tuple[SLDNode, ...]:
        """Reconcile protection-domain Relay snapshots into SLD presentation state."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        if not isinstance(read_model, ProtectionReadModel):
            raise TypeError("read_model must be a ProtectionReadModel")
        adapted = self._read_adapter.protection(read_model)
        projections = self._projection_manager.project_protection(adapted)
        active_ids = {element.object_id for element in adapted.elements}

        for node in tuple(document.model.nodes):
            if (
                node.properties.get("projection_source") == _PROTECTION_PROJECTION_SOURCE
                and node.equipment_id not in active_ids
            ):
                self._remove_stale_projection_node(document, node)

        nodes = tuple(
            self._synchronize_element(
                document,
                element,
                initial_position=None,
                projection_source=_PROTECTION_PROJECTION_SOURCE,
            )
            for element in adapted.elements
            if document.model.get_node_by_equipment_id_optional(element.object_id) is not None
        )
        document.materialize_missing_symbol_presentations()
        self._projection_manager.reconcile_protection(active_ids)
        return nodes

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

    def _require_document(self) -> SLDDocument:
        application = self._require_application()
        presentation = application.presentation
        if not isinstance(presentation, SLDDocument):
            raise RuntimeError("Active Application presentation is not an SLDDocument")
        return presentation

    def _require_application(self) -> Any:
        if self._application is None:
            raise RuntimeError("SLD Application read facade is not configured")
        return self._application

    def _synchronize_element(
        self,
        document: SLDDocument,
        read_model: ElementReadModel,
        *,
        initial_position: tuple[float, float] | None = None,
        projection_source: str = _PROJECTION_SOURCE,
    ) -> SLDNode:
        # Identity contract:
        #   * equipment_id is the canonical engineering identity.
        #   * node_id is the independent SLD/document namespace identity.
        #
        # Existing persisted documents may use any presentation node_id;
        # equipment_id lookup preserves that mapping. New projection nodes
        # receive an independent presentation identifier.
        equipment_id = read_model.object_id
        node = document.model.get_node_by_equipment_id_optional(equipment_id)

        # Backward-compatible reconciliation for older documents whose
        # presentation node ID was also the equipment ID but equipment_id
        # had not been persisted explicitly. Legacy recovery is allowed only
        # when the persisted ownership domain exactly matches the requested
        # projection domain. Ownership is never converted during migration.
        if node is None:
            legacy_node = document.model.get_node_optional(equipment_id)
            if legacy_node is not None:
                self._require_projection_ownership(
                    legacy_node,
                    projection_source=projection_source,
                    equipment_id=equipment_id,
                )
                if legacy_node.equipment_id not in (None, equipment_id):
                    raise ValueError(
                        f"SLD node ID conflicts with equipment ID: {equipment_id!r}"
                    )
                legacy_node.equipment_id = equipment_id
                node = legacy_node

        if node is None:
            x, y = initial_position if initial_position is not None else (0.0, 0.0)

            # A newly materialized projection receives an SLD/document identity
            # that is independent of the authoritative Core equipment identity.
            # Reconciliation is keyed by the persisted equipment_id association,
            # not by node_id. This prevents a Core object ID collision from
            # converting an engineer-authored/persisted SLD node into a
            # projection merely because both strings happen to match.
            node_id = f"sld-node-{uuid4().hex}"
            while document.model.has_node(node_id):
                node_id = f"sld-node-{uuid4().hex}"

            node = SLDNode(
                node_id=node_id,
                equipment_id=equipment_id,
                x=float(x),
                y=float(y),
                properties={
                    "projection_source": projection_source,
                    "element_type": read_model.element_type,
                    "labels": dict(read_model.labels),
                    "attributes": dict(read_model.attributes),
                    "terminal_ids": tuple(read_model.connectivity_refs),
                    "terminal_connectivity": tuple(read_model.attributes.get("terminal_connectivity", ())),
                },
            )
            document.model.add_node(node)
            return node

        if node.equipment_id not in (None, read_model.object_id):
            raise ValueError(f"SLD node ID conflicts with equipment ID: {read_model.object_id!r}")

        # Engineer-authored nodes may bind to real equipment but are not
        # generated projection objects. Preserve their node identity, geometry,
        # and authored properties while allowing the read projection to continue
        # reconciling independently.
        if node.properties.get("presentation_ownership") == "engineer_authored" or node.properties.get("presentation_owner") == "engineer":
            if node.equipment_id != read_model.object_id:
                raise ValueError(f"SLD authored node equipment binding conflicts with {read_model.object_id!r}")
            return node

        self._require_projection_ownership(
            node,
            projection_source=projection_source,
            equipment_id=read_model.object_id,
        )

        node.equipment_id = read_model.object_id
        node.properties.update({
            "projection_source": projection_source,
            "element_type": read_model.element_type,
            "labels": dict(read_model.labels),
            "attributes": dict(read_model.attributes),
            "terminal_ids": tuple(read_model.connectivity_refs),
            "terminal_connectivity": tuple(read_model.attributes.get("terminal_connectivity", ())),
        })
        return node

    @staticmethod
    def _require_projection_ownership(
        node: SLDNode,
        *,
        projection_source: str,
        equipment_id: str,
    ) -> None:
        """Enforce one projection-domain ownership invariant for reconciliation."""
        existing_source = node.properties.get("projection_source")
        if existing_source != projection_source:
            raise ValueError(
                f"SLD node ownership collision for equipment ID: {equipment_id!r}; "
                f"requested projection source is {projection_source!r}, "
                f"existing presentation source is {existing_source!r}"
            )

    def _remove_stale_projection_node(self, document: SLDDocument, node: SLDNode) -> None:
        """Remove a stale projection without deleting engineer-owned structure."""
        attached_connections = tuple(
            connection
            for connection in document.model.connections
            if connection.source_node_id == node.node_id
            or connection.target_node_id == node.node_id
        )
        connection_ownership = {
            connection.connection_id: self._connection_ownership(connection)
            for connection in attached_connections
        }
        engineer_owned_connections = tuple(
            connection
            for connection in attached_connections
            if connection_ownership[connection.connection_id] == "engineer"
        )

        source = node.properties.get("projection_source")
        domain = self._projection_domain_for_source(source)
        equipment_id = node.equipment_id

        if engineer_owned_connections:
            # The node is no longer projection-owned, but its persisted
            # presentation structure is still engineer-owned. Remove the
            # stale semantic registry entry before clearing projection
            # metadata; preserve node identity, geometry, and engineer-owned
            # connections.
            if equipment_id is not None:
                registered = self._projection_manager.get(equipment_id)
                if registered is not None:
                    removed = self._projection_manager.remove(
                        equipment_id,
                        domain=domain,
                    )
                    if removed is None:
                        raise ValueError(
                            f"Projection ownership mismatch during stale cleanup "
                            f"for equipment ID: {equipment_id!r}"
                        )
            node.equipment_id = None
            for key in (
                "projection_source",
                "element_type",
                "labels",
                "attributes",
            ):
                node.properties.pop(key, None)
            node.properties["presentation_owner"] = "engineer"
            return

        for connection in attached_connections:
            # Ownership was established above for every attached connection;
            # unknown ownership therefore cannot be silently deleted.
            if connection_ownership[connection.connection_id] != "projection":
                raise ValueError(
                    f"Unexpected connection ownership during stale cleanup: "
                    f"{connection.connection_id!r}"
                )
            document.model.remove_connection(connection.connection_id)

        if equipment_id is not None:
            registered = self._projection_manager.get(equipment_id)
            if registered is not None:
                removed = self._projection_manager.remove(
                    equipment_id,
                    domain=domain,
                )
                if removed is None:
                    raise ValueError(
                        f"Projection ownership mismatch during stale cleanup "
                        f"for equipment ID: {equipment_id!r}"
                    )
        document.model.remove_node(node.node_id)

    @staticmethod
    def _connection_ownership(connection: SLDConnection) -> str:
        """Classify connection ownership without silently adopting unknown data."""
        projection_source = connection.properties.get("projection_source")
        engineer_owner = connection.properties.get("presentation_owner")

        if projection_source in (_PROJECTION_SOURCE, _PROTECTION_PROJECTION_SOURCE):
            if engineer_owner is not None:
                raise ValueError(
                    f"Connection {connection.connection_id!r} has conflicting "
                    "projection and engineer ownership metadata."
                )
            return "projection"

        if engineer_owner == "engineer":
            return "engineer"

        if projection_source is None and engineer_owner is None:
            raise ValueError(
                f"Connection {connection.connection_id!r} has unknown ownership; "
                "stale reconciliation cannot classify it safely."
            )

        raise ValueError(
            f"Connection {connection.connection_id!r} has invalid ownership metadata."
        )

    @staticmethod
    def _projection_domain_for_source(source: str | None) -> ProjectionDomain:
        if source == _PROJECTION_SOURCE:
            return ProjectionDomain.NETWORK
        if source == _PROTECTION_PROJECTION_SOURCE:
            return ProjectionDomain.PROTECTION
        raise ValueError(
            f"Cannot determine projection domain for source: {source!r}"
        )

    @staticmethod
    def _terminal_role(attributes: Mapping[str, Any], side: str, endpoint_id: str) -> str | None:
        keys = (
            f"endpoint_{side}_terminal_role",
            f"endpoint_{side}_role",
            f"{side}_terminal_role",
            f"terminal_role_{side}",
        )
        for key in keys:
            value = attributes.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        connectivity = attributes.get("terminal_connectivity", ())
        for entry in connectivity if isinstance(connectivity, (tuple, list)) else ():
            if not isinstance(entry, Mapping):
                continue
            object_id = entry.get("object_id") or entry.get("equipment_id")
            role = entry.get("terminal_role") or entry.get("terminal_name") or entry.get(side)
            if str(object_id) == str(endpoint_id) and isinstance(role, str) and role.strip():
                return role.strip()
        return None

    @staticmethod
    def _sld_endpoint(node_id: str, endpoint: Mapping[str, Any], *, fallback_role: str | None = None, fallback_bus_attachment: str | None = None) -> SLDEndpoint | None:
        kind = str(endpoint.get("kind", "")).lower()
        object_id = endpoint.get("object_id") or endpoint.get("equipment_id") or endpoint.get("bus_id")
        if not isinstance(object_id, str) or not object_id:
            return None
        if kind == "bus":
            attachment_id = endpoint.get("attachment_id") or fallback_bus_attachment or "attachment-0"
            return SLDEndpoint(kind=SLDEndpointKind.BUS, node_id=node_id, bus_id=object_id, attachment_id=str(attachment_id))
        role = endpoint.get("terminal_role") or endpoint.get("terminal_name") or fallback_role
        if kind == "terminal" and isinstance(role, str) and role:
            return SLDEndpoint(kind=SLDEndpointKind.EQUIPMENT, node_id=node_id, equipment_id=object_id, terminal_role=role)
        return None

    def _project_connection(self, document: SLDDocument, *, connection_id: str, source_node_id: str, target_node_id: str, properties: Mapping[str, Any], source_endpoint: SLDEndpoint | None, target_endpoint: SLDEndpoint | None) -> None:
        existing = document.model.get_connection_optional(connection_id)
        if existing is None:
            document.model.add_connection(SLDConnection(
                connection_id=connection_id,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                source_endpoint=source_endpoint,
                target_endpoint=target_endpoint,
                properties=dict(properties),
            ))
            return
        if existing.properties.get("presentation_owner") == "engineer":
            # Reconcile semantic endpoint identity only. Engineer ownership
            # deliberately excludes projection_source so the next refresh
            # cannot classify the route as projection-owned and overwrite it.
            existing.source_node_id = source_node_id
            existing.target_node_id = target_node_id
            if source_endpoint is not None:
                existing.source_endpoint = source_endpoint
            if target_endpoint is not None:
                existing.target_endpoint = target_endpoint
            semantic_properties = dict(properties)
            semantic_properties.pop("projection_source", None)
            existing.properties.update(semantic_properties)
            return
        route = existing.route
        existing.source_node_id = source_node_id
        existing.target_node_id = target_node_id
        existing.source_endpoint = source_endpoint
        existing.target_endpoint = target_endpoint
        existing.route = route
        existing.properties.update(dict(properties))

    def _synchronize_connections(self, document: SLDDocument, read_model: NetworkReadModel) -> None:
        """Project semantic endpoint identities without replacing presentation-owned route state."""
        active_connection_ids: set[str] = set()
        node_ids_by_equipment_id = {
            node.equipment_id: node.node_id
            for node in document.model.nodes
            if node.equipment_id is not None
        }
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
            source_node_id = node_ids_by_equipment_id.get(source_id)
            target_node_id = node_ids_by_equipment_id.get(target_id)
            if source_node_id is None or target_node_id is None:
                continue
            active_connection_ids.add(element.object_id)
            source_mapping = {"kind": str(element.attributes.get("endpoint_from_kind", "terminal")), "object_id": source_id, "terminal_role": self._terminal_role(element.attributes, "from", source_id)}
            target_mapping = {"kind": str(element.attributes.get("endpoint_to_kind", "terminal")), "object_id": target_id, "terminal_role": self._terminal_role(element.attributes, "to", target_id)}
            properties = {"projection_source": _PROJECTION_SOURCE, "element_type": semantic, "equipment_id": element.object_id}
            self._project_connection(
                document,
                connection_id=element.object_id,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                source_endpoint=self._sld_endpoint(source_node_id, source_mapping),
                target_endpoint=self._sld_endpoint(target_node_id, target_mapping),
                properties=properties,
            )

        for simple_wire in getattr(read_model, "simple_wires", ()):
            endpoint_a = dict(simple_wire.endpoint_a)
            endpoint_b = dict(simple_wire.endpoint_b)
            source_equipment = endpoint_a.get("object_id")
            target_equipment = endpoint_b.get("object_id")
            source_node_id = node_ids_by_equipment_id.get(source_equipment)
            target_node_id = node_ids_by_equipment_id.get(target_equipment)
            if source_node_id is None or target_node_id is None:
                continue
            active_connection_ids.add(simple_wire.connection_id)
            properties = {
                "projection_source": _PROJECTION_SOURCE,
                "connection_kind": simple_wire.kind,
                "endpoint_a": endpoint_a,
                "endpoint_b": endpoint_b,
            }
            self._project_connection(
                connection_id=simple_wire.connection_id,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                source_endpoint=self._sld_endpoint(source_node_id, endpoint_a),
                target_endpoint=self._sld_endpoint(target_node_id, endpoint_b),
                properties=properties,
            )

        for connection in tuple(document.model.connections):
            if connection.properties.get("projection_source") == _PROJECTION_SOURCE and connection.connection_id not in active_connection_ids:
                if connection.properties.get("presentation_owner") == "engineer":
                    continue
                document.model.remove_connection(connection.connection_id)


__all__ = ["SLDReadSynchronizer"]
