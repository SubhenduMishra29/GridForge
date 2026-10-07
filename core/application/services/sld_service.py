# ============================================================
# File: core/application/services/sld_service.py
# GridForge V2 — Application SLD presentation service
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Mapping
from typing import Any

from ..command import Command
from ..results import ApplicationResult
from ..transaction import Transaction


@dataclass(frozen=True, slots=True)
class SLDState:
    """Immutable snapshot of presentation-only SLD state."""
    nodes: tuple[dict[str, Any], ...] = ()
    connections: tuple[dict[str, Any], ...] = ()


class SLDService:
    """Application boundary for persistent SLD presentation state.

    The service performs presentation mutation only inside the Application
    transaction supplied by CommandManager. It never owns history or undo/redo.
    """

    COMMAND_TYPES = frozenset({
        "sld.set_node_position",
        "sld.set_node_presentation",
        "sld.add_node",
        "sld.remove_node",
        "sld.add_connection",
        "sld.remove_connection",
        "sld.set_connection_route",
        "sld.set_node_properties",
    })

    def __init__(
        self,
        document: Any,
        *,
        application: Any = None,
        symbol_presentation_factory: Callable[[str], Mapping[str, Any]] | None = None,
    ) -> None:
        self._document = None
        self._application = application
        self._symbol_presentation_factory = symbol_presentation_factory
        if application is not None:
            self.attach_application(application)
        self.bind_document(document)

    @property
    def document(self) -> Any:
        if self._document is None:
            raise RuntimeError("SLD service has no active document.")
        return self._document

    @property
    def is_bound(self) -> bool:
        return self._document is not None

    def bind_document(self, document: Any) -> None:
        """Bind only the Application-authoritative active presentation document."""
        if document is None:
            raise TypeError("SLDService requires an SLD document.")
        if self._application is not None:
            presentation = getattr(self._application, "presentation", None)
            if presentation is not document:
                raise RuntimeError(
                    "SLDService cannot bind a document that is not the "
                    "Application-authoritative active presentation."
                )
        self._document = document

    @staticmethod
    def presentation_connection_id(core_connection_id: str) -> str:
        """Return the deterministic persistent SLD presentation identity for a Core connection."""
        if not isinstance(core_connection_id, str) or not core_connection_id:
            raise ValueError("core_connection_id must be a non-empty string")
        return f"sld-wire-{core_connection_id}"

    def reconcile_simple_wire_projection(self, network: Any) -> Callable[[], None]:
        """Reconcile persistent projection companions against authoritative Core Simple Wires.
        
        This is a project-activation boundary operation. It does not create a
        command/history entry; the returned rollback restores the exact
        persistent SLD connection snapshot if activation fails.
        """
        if network is None or not hasattr(network, "connectivity"):
            raise TypeError("network must expose the authoritative connectivity aggregate")

        previous = tuple(connection.to_dict() for connection in self.document.model.connections)
        core_connections = tuple(network.connectivity.connections)
        core_by_id = {str(connection.connection_id): connection for connection in core_connections}

        companions = {}
        changed = False
        for connection in self.document.model.connections:
            kind = str(connection.properties.get("connection_kind", "")).upper()
            lifecycle = str(connection.properties.get("lifecycle_state", "BOUND")).upper()
            core_id = connection.properties.get("core_connection_id")

            if kind != "SIMPLE_WIRE" and not core_id:
                continue
            if kind != "SIMPLE_WIRE":
                raise ValueError(
                    f"SLD connection {connection.connection_id!r} has Core connection mapping but kind {kind!r}, expected SIMPLE_WIRE."
                )

            # An engineer-owned presentation intentionally survives Core
            # deletion as a document artifact. It is not an active companion
            # and therefore must never participate in Core-ID reconciliation.
            if lifecycle == "ORPHANED":
                if connection.properties.get("presentation_owner") != "engineer":
                    raise ValueError(
                        f"SLD Simple Wire {connection.connection_id!r} is ORPHANED "
                        "but is not engineer-owned."
                    )
                if core_id is not None:
                    raise ValueError(
                        f"ORPHANED SLD Simple Wire {connection.connection_id!r} "
                        "must not retain an active Core connection binding."
                    )
                continue

            if lifecycle != "BOUND":
                raise ValueError(
                    f"SLD Simple Wire {connection.connection_id!r} has unsupported lifecycle state {lifecycle!r}."
                )

            if not core_id and str(connection.connection_id).startswith("sld-wire-"):
                # Deterministic legacy migration is centralized here; UI never
                # reconstructs Core identity from a presentation string.
                core_id = str(connection.connection_id)[len("sld-wire-"):]
                connection.properties["core_connection_id"] = core_id
                changed = True
            if not core_id:
                raise ValueError(
                    f"SLD Simple Wire {connection.connection_id!r} has no Core connection mapping."
                )
            core_id = str(core_id)
            if core_id in companions:
                raise ValueError(
                    f"Multiple SLD Simple Wire companions map to Core connection {core_id!r}."
                )
            companions[core_id] = connection

        for core_id, core in core_by_id.items():
            if core_id in companions:
                connection = companions[core_id]
                expected_a = self._sld_endpoint_from_mapping(core.endpoint_a.to_mapping())
                expected_b = self._sld_endpoint_from_mapping(core.endpoint_b.to_mapping())
                actual_a = connection.source_endpoint.to_dict() if connection.source_endpoint is not None else None
                actual_b = connection.target_endpoint.to_dict() if connection.target_endpoint is not None else None
                if connection.properties.get("connection_kind") != "SIMPLE_WIRE":
                    raise ValueError(f"SLD connection {connection.connection_id!r} has an invalid connection kind.")
                if actual_a != expected_a or actual_b != expected_b:
                    if connection.properties.get("presentation_owner") != "projection":
                        raise ValueError(
                            f"Engineer-owned SLD Simple Wire {connection.connection_id!r} conflicts with Core endpoints."
                        )
                    snapshot = connection.to_dict()
                    self.document.model.remove_connection(connection.connection_id)
                    self.document.model.create_connection(
                        connection_id=snapshot["connection_id"],
                        source_node_id=snapshot["source_node_id"],
                        target_node_id=snapshot["target_node_id"],
                        source_endpoint=expected_a,
                        target_endpoint=expected_b,
                        route=snapshot.get("route"),
                        properties=dict(snapshot.get("properties", {}), core_connection_id=core_id),
                    )
                    companions[core_id] = self.document.model.get_connection(snapshot["connection_id"])
                    changed = True
                continue

            presentation_id = self.presentation_connection_id(core_id)
            if self.document.model.get_connection_optional(presentation_id) is not None:
                raise ValueError(
                    f"SLD connection identity collision for Core Simple Wire {core_id!r}: {presentation_id!r}."
                )
            source = self._sld_node_for_endpoint_mapping(core.endpoint_a.to_mapping())
            target = self._sld_node_for_endpoint_mapping(core.endpoint_b.to_mapping())
            self.document.model.create_connection(
                connection_id=presentation_id,
                source_node_id=source,
                target_node_id=target,
                source_endpoint=self._sld_endpoint_from_mapping(core.endpoint_a.to_mapping()),
                target_endpoint=self._sld_endpoint_from_mapping(core.endpoint_b.to_mapping()),
                properties={
                    "connection_kind": "SIMPLE_WIRE",
                    "presentation_owner": "projection",
                    "projection_source": "core_reconciliation",
                    "core_connection_id": core_id,
                },
            )
            companions[core_id] = self.document.model.get_connection(presentation_id)
            changed = True

        for core_id, connection in companions.items():
            if core_id not in core_by_id:
                raise ValueError(
                    f"SLD Simple Wire {connection.connection_id!r} has no authoritative Core connection {core_id!r}."
                )

        if changed:
            self.document.mark_modified()

        def rollback() -> None:
            for connection in tuple(self.document.model.connections):
                self.document.model.remove_connection(connection.connection_id)
            for snapshot in previous:
                self._restore_connection_snapshot(snapshot)

        return rollback

    def _sld_node_for_endpoint_mapping(self, mapping: Mapping[str, Any]) -> str:
        object_id = str(mapping.get("object_id") or "")
        if not object_id:
            raise ValueError("Simple Wire endpoint mapping requires object_id.")
        nodes = tuple(
            node for node in self.document.model.nodes
            if str(getattr(node, "equipment_id", "") or "") == object_id
        )
        if len(nodes) != 1:
            raise ValueError(
                f"Expected exactly one SLD node for Core endpoint object {object_id!r}; found {len(nodes)}."
            )
        return str(nodes[0].node_id)

    @staticmethod
    def _sld_endpoint_from_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "kind": "bus" if mapping.get("kind") == "bus" else "equipment",
            "node_id": str(mapping.get("object_id") or ""),
            "equipment_id": mapping.get("object_id") if mapping.get("kind") != "bus" else None,
            "terminal_role": mapping.get("terminal_role") if mapping.get("kind") != "bus" else None,
            "bus_id": mapping.get("object_id") if mapping.get("kind") == "bus" else None,
            "attachment_id": mapping.get("attachment_id") if mapping.get("kind") == "bus" else None,
        }

    def attach_application(self, application: Any) -> None:
        """Attach the Application whose presentation state is authoritative."""
        if application is None:
            raise TypeError("application must not be None")
        self._application = application
        if self._document is not None:
            presentation = getattr(application, "presentation", None)
            # Permit composition before the project-lifecycle presentation
            # contract is wired. Once an Application presentation exists, the
            # service remains bound to that exact authoritative document.
            if presentation is not None and presentation is not self._document:
                raise RuntimeError(
                    "Existing SLD document does not match the Application presentation."
                )

    @property
    def application(self) -> Any:
        return self._application

    def detach_document(self) -> Any:
        """Detach the active document so closed projects cannot be mutated."""
        document = self._document
        self._document = None
        return document

    def supports(self, command: Command) -> bool:
        return command.command_type in self.COMMAND_TYPES

    def execute(
        self,
        command: Command,
        transaction: Transaction,
        *,
        context: Any = None,
        authoritative_value: Any = None,
    ) -> ApplicationResult:
        """Apply one SLD command inside the canonical Application transaction.

        authoritative_value is the transaction-visible result of an
        originating Core mutation when SLD binding occurs before commit.
        """
        if not isinstance(command, Command):
            raise TypeError("command must be a Command")
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction")
        if not self.supports(command):
            raise ValueError(f"Unsupported SLD command: {command.command_type}")
        handler = {
            "sld.set_node_position": self._set_node_position,
            "sld.set_node_presentation": self._set_node_presentation,
            "sld.add_node": lambda cmd, tx: self._add_node(
                cmd, tx, authoritative_value=authoritative_value
            ),
            "sld.remove_node": self._remove_node,
            "sld.add_connection": self._add_connection,
            "sld.remove_connection": lambda cmd, tx: self._remove_connection(cmd, tx, context=context),
            "sld.set_connection_route": self._set_connection_route,
            "sld.set_node_properties": self._set_node_properties,
        }[command.command_type]
        return handler(command, transaction)

    def _set_node_position(self, command: Command, transaction: Transaction) -> ApplicationResult:
        p = command.payload
        node = self.document.model.get_node(p["node_id"])
        previous = node.position
        previous_properties = dict(node.properties)
        self.document.set_node_position(p["node_id"], float(p["x"]), float(p["y"]))
        node.properties["position_owner"] = "engineer"

        def restore() -> None:
            target = self.document.model.get_node(p["node_id"])
            self.document.set_node_position(p["node_id"], *previous)
            target.properties.clear()
            target.properties.update(previous_properties)
            self.document.mark_modified()

        transaction.record_undo(restore)
        return ApplicationResult.success_result(
            message="SLD node position updated.",
            metadata={"presentation_operation": "set_node_position", "node_id": p["node_id"]},
        )

    def _set_node_presentation(self, command: Command, transaction: Transaction) -> ApplicationResult:
        p = command.payload
        node = self.document.model.get_node(p["node_id"])
        previous = None if node.presentation is None else node.presentation.to_dict()
        previous_properties = dict(node.properties)
        node.set_presentation(p["presentation"])
        node.properties["symbol_owner"] = "engineer"
        node.properties.setdefault("presentation_owner", "projection" if node.properties.get("projection_source") else "engineer")
        self.document.mark_modified()
        def restore() -> None:
            target = self.document.model.get_node(p["node_id"])
            if previous is None:
                target.clear_presentation()
            else:
                target.set_presentation(previous)
            target.properties.clear()
            target.properties.update(previous_properties)
            self.document.mark_modified()
        transaction.record_undo(restore)
        return ApplicationResult.success_result(
            message="SLD node presentation updated.",
            metadata={"presentation_operation": "set_node_presentation", "node_id": p["node_id"]},
        )

    def _add_node(
        self,
        command: Command,
        transaction: Transaction,
        *,
        authoritative_value: Any = None,
    ) -> ApplicationResult:
        p = command.payload
        equipment_id = p.get("equipment_id")
        if equipment_id is not None:
            self._validate_equipment_reference(
                str(equipment_id),
                authoritative_value=authoritative_value,
            )
        presentation_owner = str(p.get("presentation_owner", "engineer"))
        projection_source = p.get("projection_source")
        if presentation_owner not in {"engineer", "projection"}:
            raise ValueError("presentation_owner must be 'engineer' or 'projection'.")
        if projection_source is not None and presentation_owner != "projection":
            raise ValueError("projection_source requires presentation_owner='projection'.")
        properties = {"presentation_owner": presentation_owner}
        element_type = p.get("element_type")
        if element_type is not None:
            properties["element_type"] = str(element_type)
        if projection_source is not None:
            properties["projection_source"] = str(projection_source)
        if equipment_id is not None:
            properties["lifecycle_state"] = "BOUND"
        presentation_properties = p.get("presentation_properties", {})
        if not isinstance(presentation_properties, Mapping):
            raise TypeError("presentation_properties must be a mapping")
        properties.update(dict(presentation_properties))

        presentation = p.get("presentation")
        if presentation is None and self._symbol_presentation_factory is not None:
            if not isinstance(element_type, str) or not element_type.strip():
                raise ValueError(
                    "SLD node creation requires element_type when a default "
                    "symbol presentation factory is configured."
                )
            presentation = self._symbol_presentation_factory(element_type)

        self.document.model.create_node(
            node_id=p["node_id"],
            equipment_id=equipment_id,
            x=float(p["x"]),
            y=float(p["y"]),
            presentation=presentation,
            properties=properties,
        )
        self.document.mark_modified()
        transaction.record_undo(lambda node_id=p["node_id"]: self.document.model.remove_node(node_id))
        return ApplicationResult.success_result(
            message="SLD node added.",
            metadata={"presentation_operation": "add_node", "node_id": p["node_id"]},
        )

    def _validate_equipment_reference(
        self,
        equipment_id: str,
        *,
        authoritative_value: Any = None,
    ) -> None:
        """Validate an SLD equipment association at the Application boundary.

        For an in-flight Core mutation, authoritative_value is the
        transaction-visible Core result. ReadModels remain post-commit
        projections and are not used for that binding.
        """
        if authoritative_value is not None:
            authoritative_id = getattr(authoritative_value, "id", None)
            if authoritative_id is None or str(authoritative_id) != equipment_id:
                raise ValueError(
                    f"SLD node equipment reference {equipment_id!r} does not "
                    "match the transaction-visible Core identity."
                )
            return

        if self._application is None:
            raise RuntimeError("SLDService requires an Application to validate equipment references.")
        read_model = self._application.read_network()
        if any(element.object_id == equipment_id for element in read_model.elements):
            return
        protection = self._application.read_protection()
        protection_elements = getattr(protection, "elements", None)
        if protection_elements is None:
            protection_elements = getattr(protection, "relays", ())
        if any(element.object_id == equipment_id for element in protection_elements):
            return
        raise ValueError(
            f"SLD node equipment reference {equipment_id!r} does not resolve to current Application read state."
        )

    @staticmethod
    def has_engineer_presentation_overrides(node: Any) -> bool:
        """Return whether a node contains authored presentation state."""
        properties = getattr(node, "properties", {}) or {}
        if properties.get("position_owner") == "engineer": return True
        if properties.get("symbol_owner") == "engineer": return True
        for key in ("labels_owner", "visual_properties_owner", "manual_geometry_owner", "presentation_fields_owner"):
            if properties.get(key) == "engineer": return True
        overrides = properties.get("engineer_presentation_overrides")
        if isinstance(overrides, Mapping) and bool(overrides): return True
        if properties.get("presentation_owner") == "engineer": return True
        return False

    @staticmethod
    def has_engineer_presentation_overrides_for_connection(connection: Any) -> bool:
        """Return whether a connection contains authored route/presentation state."""
        properties = getattr(connection, "properties", {}) or {}
        if properties.get("route_owner") == "engineer": return True
        route = getattr(connection, "route", None)
        if route is not None and getattr(route, "ownership", None) == "engineer": return True
        for key in ("labels_owner", "visual_properties_owner", "manual_geometry_owner", "presentation_fields_owner"):
            if properties.get(key) == "engineer": return True
        overrides = properties.get("engineer_presentation_overrides")
        if isinstance(overrides, Mapping) and bool(overrides): return True
        if properties.get("presentation_owner") == "engineer": return True
        return False

    @staticmethod
    def _set_node_lifecycle_state(node: Any, state: str) -> None:
        if state not in {"BOUND", "ORPHANED", "REMOVED"}: raise ValueError(f"Unsupported SLD node lifecycle state: {state!r}")
        node.properties["lifecycle_state"] = state

    @staticmethod
    def _set_connection_lifecycle_state(connection: Any, state: str) -> None:
        if state not in {"BOUND", "ORPHANED", "REMOVED"}: raise ValueError(f"Unsupported SLD connection lifecycle state: {state!r}")
        connection.properties["lifecycle_state"] = state
    def reconcile_element_update(
        self,
        *,
        equipment_id: str,
        element_type: str,
        core_object: Any,
        transaction: Transaction,
    ) -> None:
        """Reconcile presentation from the authoritative transaction-visible Core object.

        This is intentionally a service operation, not a second command/history
        mechanism. It is invoked by the Application pre-commit hook inside the
        transaction opened for the originating Core command. The Core object is
        the mutation result; ReadModels are never queried to establish the
        authoritative updated state.
        """
        if not isinstance(equipment_id, str) or not equipment_id:
            raise ValueError("equipment_id must be a non-empty string")
        node = self.document.model.get_node_by_equipment_id_optional(equipment_id)
        if node is None:
            return
        previous = node.to_dict()
        # Convert the already-mutated Core object into the existing
        # presentation projection shape without querying Application
        # ReadService. The Core object remains the authoritative source.
        from ..read_service import NetworkReadService
        projected = NetworkReadService._to_read_model(element_type, core_object)
        attributes = dict(projected.attributes)
        labels = dict(projected.labels)
        connectivity = tuple(projected.connectivity_refs)
        node.properties.update({
            "element_type": str(element_type),
            "labels": labels,
            "attributes": attributes,
            "terminal_ids": connectivity,
            "terminal_connectivity": tuple(attributes.get("terminal_connectivity", ())),
        })
        self._set_node_lifecycle_state(node, "BOUND")
        node.equipment_id = equipment_id
        transaction.record_undo(
            lambda snapshot=previous: self._restore_node_snapshot(snapshot)
        )
        self.document.mark_modified()

    def reconcile_element_delete(
        self,
        *,
        equipment_id: str,
        transaction: Transaction,
    ) -> str:
        """Remove or orphan a Core-bound SLD node using field-level ownership."""
        node = self.document.model.get_node_by_equipment_id_optional(equipment_id)
        if node is None:
            return "REMOVED"
        snapshot = node.to_dict()
        attached = tuple(
            connection for connection in self.document.model.connections
            if connection.source_node_id == node.node_id or connection.target_node_id == node.node_id
        )
        connection_snapshots = tuple(connection.to_dict() for connection in attached)

        if not self.has_engineer_presentation_overrides(node):
            self.document.model.remove_node(node.node_id)
            self.document.mark_modified()
            def restore(snapshot=snapshot, connection_snapshots=connection_snapshots) -> None:
                self._restore_node_snapshot(snapshot)
                for item in connection_snapshots:
                    if self.document.model.get_connection_optional(item["connection_id"]) is None:
                        self._restore_connection_snapshot(item)
            transaction.record_undo(restore)
            return "REMOVED"

        node.equipment_id = None
        node.properties.pop("projection_source", None)
        node.properties["lifecycle_state"] = "ORPHANED"
        node.properties["orphaned_equipment_id"] = equipment_id

        for connection in attached:
            if self.has_engineer_presentation_overrides_for_connection(connection):
                if connection.source_node_id == node.node_id:
                    connection.source_endpoint = None
                if connection.target_node_id == node.node_id:
                    connection.target_endpoint = None
                connection.properties.pop("projection_source", None)
                self._set_connection_lifecycle_state(connection, "ORPHANED")
            else:
                self.document.model.remove_connection(connection.connection_id)

        self.document.mark_modified()
        def restore(snapshot=snapshot, connection_snapshots=connection_snapshots) -> None:
            self._restore_node_snapshot(snapshot)
            for connection in tuple(self.document.model.connections):
                if connection.connection_id in {item["connection_id"] for item in connection_snapshots}:
                    self.document.model.remove_connection(connection.connection_id)
            for item in connection_snapshots:
                self._restore_connection_snapshot(item)
        transaction.record_undo(restore)
        return "ORPHANED"

    def reconcile_connection_delete(
        self,
        *,
        connection_id: str,
        transaction: Transaction,
    ) -> str:
        """Remove or orphan a Core-bound SLD connection by route ownership."""
        connection = self.document.model.get_connection_optional(connection_id)
        if connection is None:
            # Core Simple Wire identity and persistent SLD presentation identity
            # are distinct. Resolve the active companion through its persisted
            # Core mapping, or resolve an already-orphaned authored presentation
            # through its non-authoritative deletion provenance so redo can record
            # the same SLD inverse without resurrecting a Core binding.
            candidates = tuple(
                item
                for item in self.document.model.connections
                if item.properties.get("core_connection_id") == connection_id
                or (
                    str(item.properties.get("lifecycle_state", "")).upper() == "ORPHANED"
                    and item.properties.get("orphaned_from_core_connection_id") == connection_id
                )
            )
            if len(candidates) > 1:
                raise ValueError(
                    f"Multiple SLD connection companions map to Core connection {connection_id!r}."
                )
            connection = candidates[0] if candidates else None
        if connection is None:
            return "REMOVED"
        presentation_id = connection.connection_id
        snapshot = connection.to_dict()
        if not self.has_engineer_presentation_overrides_for_connection(connection):
            self.document.model.remove_connection(presentation_id)
            self.document.mark_modified()
            transaction.record_undo(lambda snapshot=snapshot: self._restore_connection_snapshot(snapshot))
            return "REMOVED"
        connection.source_endpoint = None
        connection.target_endpoint = None
        connection.properties.pop("projection_source", None)
        # Core deletion severs the binding. The authored SLD presentation
        # remains, but its old Core ID is no longer authoritative identity.
        connection.properties.pop("core_connection_id", None)
        connection.properties["orphaned_from_core_connection_id"] = connection_id
        connection.properties["lifecycle_state"] = "ORPHANED"
        self.document.mark_modified()
        transaction.record_undo(lambda snapshot=snapshot: self._restore_connection_snapshot(snapshot))
        return "ORPHANED"

    def _restore_node_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        self.document.model.create_node(
            node_id=snapshot["node_id"],
            equipment_id=snapshot.get("equipment_id"),
            x=snapshot.get("x", 0.0),
            y=snapshot.get("y", 0.0),
            presentation=snapshot.get("presentation"),
            properties=snapshot.get("properties", {}),
        )
        for item in snapshot.get("connections", ()):
            self._restore_connection_snapshot(item)
        self.document.mark_modified()

    def _restore_connection_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        self.document.model.create_connection(
            connection_id=snapshot["connection_id"],
            source_node_id=snapshot["source_node_id"],
            target_node_id=snapshot["target_node_id"],
            source_endpoint=snapshot.get("source_endpoint"),
            target_endpoint=snapshot.get("target_endpoint"),
            route=snapshot.get("route"),
            properties=snapshot.get("properties", {}),
        )
        self.document.mark_modified()

    def _remove_node(self, command: Command, transaction: Transaction) -> ApplicationResult:
        node_id = command.payload["node_id"]
        node = self.document.model.get_node(node_id)
        projection_source = command.payload.get("projection_source")
        if projection_source is None:
            self._require_engineer_owned_node(node)
        else:
            if node.properties.get("projection_source") != projection_source:
                raise ValueError("SLD node projection ownership does not match the removal command.")
        node_snapshot = node.to_dict()
        connection_snapshots = tuple(
            connection.to_dict()
            for connection in self.document.model.connections
            if connection.source_node_id == node_id or connection.target_node_id == node_id
        )
        self.document.model.remove_node(node_id)
        self.document.mark_modified()

        def restore() -> None:
            self.document.model.create_node(
                node_id=node_snapshot["node_id"],
                equipment_id=node_snapshot.get("equipment_id"),
                x=node_snapshot.get("x", 0.0),
                y=node_snapshot.get("y", 0.0),
                presentation=node_snapshot.get("presentation"),
                properties=node_snapshot.get("properties", {}),
            )
            for snapshot in connection_snapshots:
                self.document.model.create_connection(
                    connection_id=snapshot["connection_id"],
                    source_node_id=snapshot["source_node_id"],
                    target_node_id=snapshot["target_node_id"],
                    source_endpoint=snapshot.get("source_endpoint"),
                    target_endpoint=snapshot.get("target_endpoint"),
                    route=snapshot.get("route"),
                    properties=snapshot.get("properties", {}),
                )

        transaction.record_undo(restore)
        return ApplicationResult.success_result(
            message="SLD node removed.",
            metadata={"presentation_operation": "remove_node", "node_id": node_id},
        )

    def _add_connection(self, command: Command, transaction: Transaction) -> ApplicationResult:
        p = command.payload
        source_endpoint = p.get("source_endpoint")
        target_endpoint = p.get("target_endpoint")
        route = p.get("route")
        presentation_owner = str(p.get("presentation_owner", "engineer"))
        projection_source = p.get("projection_source")
        if presentation_owner not in {"engineer", "projection"}:
            raise ValueError("presentation_owner must be 'engineer' or 'projection'.")
        if projection_source is not None and presentation_owner != "projection":
            raise ValueError("projection_source requires presentation_owner='projection'.")
        properties = {"presentation_owner": presentation_owner}
        connection_kind = p.get("connection_kind")
        if connection_kind is not None:
            properties["connection_kind"] = str(connection_kind)
        core_connection_id = p.get("core_connection_id")
        if core_connection_id is not None:
            core_connection_id = str(core_connection_id).strip()
            if not core_connection_id:
                raise ValueError("core_connection_id must be a non-empty string when provided.")
            properties["core_connection_id"] = core_connection_id
        if projection_source is not None:
            properties["projection_source"] = str(projection_source)
        if connection_kind is not None:
            properties["lifecycle_state"] = "BOUND"
        if isinstance(route, Mapping) and route.get("ownership") == "engineer":
            properties["route_owner"] = "engineer"
        self.document.model.create_connection(
            connection_id=p["connection_id"],
            source_node_id=p["source_node_id"],
            target_node_id=p["target_node_id"],
            source_endpoint=source_endpoint,
            target_endpoint=target_endpoint,
            route=route,
            properties=properties,
        )
        self.document.mark_modified()
        transaction.record_undo(lambda connection_id=p["connection_id"]: self.document.model.remove_connection(connection_id))
        return ApplicationResult.success_result(
            message="SLD connection added.",
            metadata={"presentation_operation": "add_connection", "connection_id": p["connection_id"]},
        )

    def _set_node_properties(self, command: Command, transaction: Transaction) -> ApplicationResult:
        p = command.payload
        node = self.document.model.get_node(p["node_id"])
        previous = dict(node.properties)
        properties = p["properties"]
        if not isinstance(properties, Mapping):
            raise TypeError("properties must be a mapping")
        semantic_keys = {
            "equipment_id", "element_type", "terminal_ids", "terminal_connectivity",
            "attributes", "labels", "projection_source", "lifecycle_state",
        }
        if semantic_keys.intersection(properties):
            raise ValueError("SLD semantic binding fields are Application-owned and cannot be edited as presentation properties.")
        node.properties.update(dict(properties))
        if "labels" in properties and "labels_owner" not in properties:
            node.properties["labels_owner"] = "engineer"
        if "visual_properties" in properties and "visual_properties_owner" not in properties:
            node.properties["visual_properties_owner"] = "engineer"
        if "manual_geometry" in properties and "manual_geometry_owner" not in properties:
            node.properties["manual_geometry_owner"] = "engineer"
        self.document.mark_modified()
        transaction.record_undo(lambda node=node, snapshot=previous: (node.properties.clear(), node.properties.update(snapshot)))
        return ApplicationResult.success_result(
            message="SLD node presentation properties updated.",
            metadata={"presentation_operation": "set_node_properties", "node_id": p["node_id"]},
        )

    def _set_connection_route(self, command: Command, transaction: Transaction) -> ApplicationResult:
        p = command.payload
        connection = self.document.model.get_connection(p["connection_id"])
        owner = connection.properties.get("presentation_owner")
        if owner not in (None, "engineer", "projection"):
            raise ValueError("SLD connection ownership is unknown; route edit is rejected.")
        previous = connection.route
        previous_properties = dict(connection.properties)
        updated = self.document.model.get_connection(p["connection_id"]).route.__class__.from_dict(p["route"])
        if updated.ownership != "engineer":
            updated = updated.__class__(routing_mode=updated.routing_mode, ownership="engineer", points=updated.points)
        connection.route = updated
        connection.properties["route_owner"] = "engineer"
        connection.properties.setdefault("presentation_owner", "projection" if connection.properties.get("projection_source") else "engineer")
        self.document.mark_modified()
        transaction.record_undo(lambda connection=connection, route=previous, properties=previous_properties: (setattr(connection, "route", route), connection.properties.clear(), connection.properties.update(properties)))
        return ApplicationResult.success_result(
            message="SLD connection route updated.",
            metadata={"presentation_operation": "set_connection_route", "connection_id": p["connection_id"]},
        )

    @staticmethod
    def _require_engineer_owned_node(node: Any) -> None:
        source = node.properties.get("projection_source")
        owner = node.properties.get("presentation_owner")
        if source in {"application_read_model", "protection_read_model"}:
            raise ValueError(
                "Projection-owned SLD nodes cannot be removed through "
                "engineer-owned presentation commands."
            )
        if source is not None or owner not in (None, "engineer"):
            raise ValueError(
                "SLD node ownership is unknown or invalid; removal is rejected."
            )

    @staticmethod
    def _require_engineer_owned_connection(connection: Any) -> None:
        source = connection.properties.get("projection_source")
        owner = connection.properties.get("presentation_owner")
        if source in {"application_read_model", "protection_read_model"}:
            raise ValueError(
                "Projection-owned SLD connections cannot be removed through "
                "engineer-owned presentation commands."
            )
        if owner != "engineer":
            raise ValueError(
                "SLD connection ownership is unknown; removal is rejected."
            )

    def _remove_connection(self, command: Command, transaction: Transaction, *, context: Any = None) -> ApplicationResult:
        connection_id = command.payload["connection_id"]
        connection = self.document.model.get_connection(connection_id)

        # Projection-owned Simple Wire presentation is not an independent
        # electrical authority. Electrical deletion must originate from the
        # Core SimpleWire command; Application pre-commit then removes the
        # persistent SLD companion in the same transaction.
        if (
            connection.properties.get("projection_source") == "application_read_model"
            and connection.properties.get("connection_kind") == "SIMPLE_WIRE"
        ):
            raise ValueError(
                "Projection-owned Simple Wire SLD connections cannot be removed "
                "through an SLD-only command; use the Application Simple Wire "
                "deletion command."
            )

        self._require_engineer_owned_connection(connection)
        snapshot = connection.to_dict()
        self.document.model.remove_connection(connection_id)
        self.document.mark_modified()

        def restore() -> None:
            self.document.model.create_connection(
                connection_id=snapshot["connection_id"],
                source_node_id=snapshot["source_node_id"],
                target_node_id=snapshot["target_node_id"],
                source_endpoint=snapshot.get("source_endpoint"),
                target_endpoint=snapshot.get("target_endpoint"),
                route=snapshot.get("route"),
                properties=snapshot.get("properties", {}),
            )

        transaction.record_undo(restore)
        return ApplicationResult.success_result(
            message="SLD connection removed.",
            metadata={"presentation_operation": "remove_connection", "connection_id": connection_id},
        )


__all__ = ["SLDService", "SLDState"]
