# ============================================================
# File: core/application/draft/handlers.py
# GridForge V2
# Author: Subhendu Mishra
# ============================================================
"""Application-owned draft authoring and deterministic Draft→Core commit."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from core.model import EndpointReference, EquipmentType
from core.network.electrical_boundary import EndpointCompatibility, EndpointCompatibilityError

from ..creation import CreationCommitIntent, CreationCommandPreparer
from ..results import ApplicationResult
from ..services.model_service import ModelService
from ..services.simple_wire_service import SimpleWireConnectionService
from .network import DraftConnection, DraftEndpointReference, DraftEquipment, DraftNetwork


class DraftCommandHandlers:
    def __init__(self, draft_provider):
        self._draft_provider = draft_provider

    def _draft(self) -> DraftNetwork:
        draft = self._draft_provider()
        if draft is None:
            raise RuntimeError("Application DraftNetwork is not active.")
        return draft

    def handlers(self):
        return {
            "draft.add_equipment": self.add_equipment,
            "draft.update_equipment": self.update_equipment,
            "draft.remove_equipment": self.remove_equipment,
            "draft.add_connection": self.add_connection,
            "draft.create_connection": self.add_connection,
            "draft.remove_connection": self.remove_connection,
        }

    def add_equipment(self, command, context, transaction):
        draft = self._draft()
        item = DraftEquipment.from_dict(command.payload["equipment"])
        draft.add_equipment(item)
        transaction.record_undo(lambda: draft.remove_equipment(item.draft_id))
        return ApplicationResult.success_result(
            message=f"Draft equipment {item.draft_id} added.",
            metadata={"draft_id": item.draft_id},
        )

    def update_equipment(self, command, context, transaction):
        draft = self._draft()
        item = draft.require_equipment(str(command.payload["draft_id"]))
        before = item
        draft.update_equipment(item.draft_id, **dict(command.payload["changes"]))
        transaction.record_undo(
            lambda: draft.update_equipment(
                before.draft_id,
                display_name=before.display_name,
                engineering_data=dict(before.engineering_data),
                endpoints=dict(before.endpoints),
                placement=before.placement,
                presentation=dict(before.presentation),
                validation_state=dict(before.validation_state),
            )
        )
        return ApplicationResult.success_result(
            message=f"Draft equipment {item.draft_id} updated.",
            metadata={"draft_id": item.draft_id},
        )

    def remove_equipment(self, command, context, transaction):
        draft = self._draft()
        draft_id = str(command.payload["draft_id"])
        item = draft.require_equipment(draft_id)
        incident = tuple(
            connection for connection in draft.connections
            if connection.source.object_id == draft_id or connection.target.object_id == draft_id
        )
        draft.remove_equipment(draft_id)

        def restore():
            draft.add_equipment(item)
            for connection in incident:
                draft.add_connection(connection)

        transaction.record_undo(restore)
        return ApplicationResult.success_result(
            message=f"Draft equipment {item.draft_id} removed.",
            metadata={"draft_id": item.draft_id},
        )

    def add_connection(self, command, context, transaction):
        draft = self._draft()
        item = DraftConnection.from_dict(command.payload["connection"])
        draft.add_connection(item)
        transaction.record_undo(lambda: draft.remove_connection(item.connection_id))
        return ApplicationResult.success_result(
            message=f"Draft connection {item.connection_id} added.",
            metadata={"connection_id": item.connection_id},
        )

    def remove_connection(self, command, context, transaction):
        draft = self._draft()
        item = draft.remove_connection(str(command.payload["connection_id"]))
        transaction.record_undo(lambda: draft.add_connection(item))
        return ApplicationResult.success_result(
            message=f"Draft connection {item.connection_id} removed.",
            metadata={"connection_id": item.connection_id},
        )


@dataclass(frozen=True, slots=True)
class DraftEquipmentCommitPlan:
    draft_id: str
    core_id: str
    intent: CreationCommitIntent
    command: Any
    resolved_endpoints: Mapping[str, EndpointReference]

    def __post_init__(self):
        object.__setattr__(self, "resolved_endpoints", MappingProxyType(dict(self.resolved_endpoints)))


@dataclass(frozen=True, slots=True)
class DraftConnectionCommitPlan:
    connection_id: str
    endpoint_a: EndpointReference
    endpoint_b: EndpointReference


@dataclass(frozen=True, slots=True)
class DraftCommitPlan:
    """Immutable, transaction-local interpretation of one DraftNetwork snapshot."""

    project_id: str
    activation_generation: int
    equipment: tuple[DraftEquipmentCommitPlan, ...]
    connections: tuple[DraftConnectionCommitPlan, ...]

    def __post_init__(self):
        object.__setattr__(self, "equipment", tuple(self.equipment))
        object.__setattr__(self, "connections", tuple(self.connections))


class DraftConnectivityResolver:
    """Resolve draft terminal components to deterministic Core Bus boundaries.

    DraftConnection remains the sole authoring topology. This resolver builds
    only an ephemeral transaction-local graph and never persists another
    topology representation.
    """

    @staticmethod
    def _terminal(item: DraftEquipment, role: str) -> DraftEndpointReference:
        if role not in item.terminal_contract:
            raise ValueError(
                f"Invalid terminal role {role!r} for draft equipment {item.draft_id!r}."
            )
        return DraftEndpointReference.terminal(
            draft_id=item.draft_id,
            equipment_type=item.equipment_type,
            terminal_role=role,
        )

    def resolve(
        self,
        snapshot: DraftNetwork,
        core_id_map: Mapping[str, str],
        network: Any,
    ) -> tuple[dict[str, Mapping[str, EndpointReference]], tuple[DraftConnectionCommitPlan, ...]]:
        equipment_by_id = {item.draft_id: item for item in snapshot.equipment}
        adjacency: dict[DraftEndpointReference, set[DraftEndpointReference]] = {}
        all_terminals: dict[DraftEndpointReference, DraftEquipment] = {}

        for item in snapshot.equipment:
            for role in item.terminal_contract:
                endpoint = self._terminal(item, role)
                all_terminals[endpoint] = item
                adjacency.setdefault(endpoint, set())

        for connection in snapshot.connections:
            adjacency.setdefault(connection.source, set()).add(connection.target)
            adjacency.setdefault(connection.target, set()).add(connection.source)

        def component_boundaries(start: DraftEndpointReference) -> set[DraftEndpointReference]:
            seen: set[DraftEndpointReference] = set()
            stack = [start]
            boundaries: set[DraftEndpointReference] = set()
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                if current.is_bus:
                    boundaries.add(current)
                    continue
                for neighbour in adjacency.get(current, ()):
                    if neighbour not in seen:
                        stack.append(neighbour)
            return boundaries

        resolved: dict[str, dict[str, EndpointReference]] = {
            item.draft_id: {} for item in snapshot.equipment
        }

        for terminal, item in sorted(
            all_terminals.items(),
            key=lambda pair: (pair[1].draft_id, pair[0].terminal_role or ""),
        ):
            role = terminal.terminal_role or ""
            declared = item.endpoints.get(role)
            boundaries = component_boundaries(terminal)

            declared_bus = None
            if declared is not None and declared.is_bus:
                declared_bus = declared.to_core_reference()

            if len(boundaries) > 1:
                bus_ids = sorted(
                    f"{boundary.object_id}/{boundary.attachment_id}"
                    for boundary in boundaries
                )
                raise ValueError(
                    f"Ambiguous electrical boundary: equipment={item.draft_id!r} "
                    f"terminal={role!r} reaches multiple Buses {bus_ids!r}."
                )

            if boundaries:
                boundary = next(iter(boundaries))
                resolved_ref = boundary.to_core_reference()
                # An explicit endpoint declaration is an acquired external
                # electrical fact.  The authoring graph may refine/agree with
                # it, but it may never silently override it.  A Core terminal
                # declaration and a Bus boundary are therefore contradictory.
                if declared is not None:
                    if declared.is_bus:
                        declared_ref = declared.to_core_reference()
                    elif declared.scope == "core":
                        declared_ref = self._to_core_endpoint(declared, core_id_map)
                    else:
                        declared_ref = None
                    if declared_ref is not None and declared_ref != resolved_ref:
                        raise ValueError(
                            f"Contradictory endpoint declaration: equipment={item.draft_id!r} "
                            f"terminal={role!r} declares {declared_ref!r} but draft "
                            f"connectivity resolves to {resolved_ref!r}."
                        )
                resolved[item.draft_id][role] = resolved_ref
                continue

            if declared is not None:
                if declared.is_terminal and declared.scope == "draft":
                    # A stored draft terminal declaration cannot replace the
                    # authoring graph; without a Bus boundary it is unresolved.
                    pass
                else:
                    resolved[item.draft_id][role] = self._to_core_endpoint(
                        declared, core_id_map
                    )
                    continue

            # endpoint_mapping is the authoritative creation contract carried
            # by the DraftEquipment snapshot. Every mapped role is required to
            # have a resolved electrical endpoint before its Core command can
            # be prepared.
            if role in item.endpoint_mapping:
                raise ValueError(
                    f"Unresolved electrical endpoint: equipment={item.draft_id!r} "
                    f"terminal={role!r} has no Bus boundary."
                )

        connection_plan: list[DraftConnectionCommitPlan] = []
        for connection in sorted(snapshot.connections, key=lambda item: item.connection_id):
            a = self._to_core_connection_endpoint(connection.source, core_id_map)
            b = self._to_core_connection_endpoint(connection.target, core_id_map)
            try:
                # Existing Core endpoints (including explicitly acquired
                # external terminals) must be proven against the active Core
                # network during preparation.  Draft endpoints are mapped to
                # deterministic future Core identities and are validated by
                # their DraftEquipment contract plus pair compatibility now;
                # their concrete Core existence is checked immediately before
                # the wire mutation after all equipment creations succeed.
                for endpoint in (a, b):
                    if endpoint.is_bus or endpoint.object_id not in core_id_map.values():
                        EndpointCompatibility.validate_reference(endpoint, network)
                EndpointCompatibility.validate_pair(a, b, None)
            except EndpointCompatibilityError as exc:
                raise ValueError(
                    f"Invalid DraftConnection {connection.connection_id!r}: {exc}"
                ) from exc
            connection_plan.append(
                DraftConnectionCommitPlan(connection.connection_id, a, b)
            )

        return resolved, tuple(connection_plan)

    @staticmethod
    def _to_core_endpoint(
        endpoint: DraftEndpointReference,
        core_id_map: Mapping[str, str],
    ) -> EndpointReference:
        if endpoint.is_bus:
            return endpoint.to_core_reference()
        try:
            equipment_type = EquipmentType(endpoint.equipment_type or "")
        except ValueError as exc:
            raise ValueError(
                f"Unsupported draft endpoint equipment type: {endpoint.equipment_type!r}"
            ) from exc
        core_id = core_id_map.get(endpoint.object_id, endpoint.object_id)
        return EndpointReference.terminal(
            equipment_type=equipment_type,
            equipment_id=core_id,
            terminal_role=endpoint.terminal_role or "",
        )

    _to_core_connection_endpoint = _to_core_endpoint


class CommitNetworkHandler:
    def __init__(self, draft_provider):
        self._draft_provider = draft_provider
        self._resolver = DraftConnectivityResolver()

    def __call__(self, command, context, transaction):
        payload = command.payload
        active_draft = self._draft_provider()
        if active_draft is None:
            raise RuntimeError("Application DraftNetwork is not active.")

        project_id = str(payload["project_id"])
        activation_generation = int(payload["activation_generation"])
        if project_id != active_draft.project_id:
            raise ValueError("CommitNetworkCommand project_id does not match the active project.")
        if activation_generation != active_draft.activation_generation:
            raise ValueError(
                "CommitNetworkCommand activation_generation does not match the active project."
            )

        snapshot = DraftNetwork.from_dict(
            payload["draft_network"],
            project_id=project_id,
            activation_generation=activation_generation,
        )
        if snapshot.to_dict() != dict(payload["draft_network"]):
            raise ValueError("CommitNetworkCommand draft_network payload is not canonical.")

        errors = snapshot.validate(getattr(context, "network", None))
        if errors:
            raise ValueError("Draft validation failed: " + "; ".join(errors))

        model = ModelService(context.network)
        core_ids = {
            item.draft_id: f"{item.equipment_type}-{item.draft_id}"
            for item in sorted(snapshot.equipment, key=lambda item: item.draft_id)
        }

        # Identity validation is part of the prepare phase. A deterministic
        # redo identity must never collide with an existing Core object after
        # another object has already been created in this transaction.
        for draft_id, core_id in core_ids.items():
            try:
                context.network.get_by_identity(core_id)
            except KeyError:
                continue
            raise ValueError(
                f"Core identity collision: draft equipment {draft_id!r} "
                f"maps to existing Core identity {core_id!r}."
            )

        resolved_endpoints, connection_plan = self._resolver.resolve(
            snapshot, core_ids, context.network
        )

        # Full prepare/validation phase: no Core mutation is allowed before
        # every creation command and every Simple Wire intent is valid.
        equipment_plan: list[DraftEquipmentCommitPlan] = []
        model_handlers = None
        from ..command_handlers import ModelCommandHandlers
        model_handlers = ModelCommandHandlers(model).handlers()

        for item in sorted(snapshot.equipment, key=lambda value: value.draft_id):
            endpoints = resolved_endpoints[item.draft_id]
            intent = CreationCommitIntent(
                command_type=item.command_type,
                id_field=item.id_field,
                object_id=core_ids[item.draft_id],
                parameter_mapping=dict(item.parameter_mapping),
                endpoint_mapping=dict(item.endpoint_mapping),
                values=dict(item.engineering_data),
                endpoints=endpoints,
                position=item.placement,
            )
            child = CreationCommandPreparer.prepare(intent)
            equipment_plan.append(
                DraftEquipmentCommitPlan(
                    draft_id=item.draft_id,
                    core_id=core_ids[item.draft_id],
                    intent=intent,
                    command=child,
                    resolved_endpoints=endpoints,
                )
            )

        commit_plan = DraftCommitPlan(
            project_id=project_id,
            activation_generation=activation_generation,
            equipment=tuple(equipment_plan),
            connections=connection_plan,
        )

        created: list[dict[str, Any]] = []
        for item in commit_plan.equipment:
            result = model_handlers[item.command.command_type](
                item.command, context, transaction
            )
            if not result.success:
                raise RuntimeError(result.message)
            created.append(
                {
                    "draft_id": item.draft_id,
                    "core_id": item.core_id,
                    "sld_node_id": f"sld-core-{item.core_id}",
                    "element_type": next(
                        equipment.equipment_type
                        for equipment in snapshot.equipment
                        if equipment.draft_id == item.draft_id
                    ),
                    "x": item.intent.position[0] if item.intent.position else None,
                    "y": item.intent.position[1] if item.intent.position else None,
                    "presentation": dict(
                        next(
                            equipment.presentation
                            for equipment in snapshot.equipment
                            if equipment.draft_id == item.draft_id
                        )
                    ),
                }
            )

        wire_service = SimpleWireConnectionService()
        committed_connections: list[dict[str, Any]] = []
        for item in commit_plan.connections:
            # All creation intents have already been prepared.  At this point
            # deterministic Core identities exist, so every wire endpoint can
            # now be resolved against the actual transaction-visible Core
            # network before Simple Wire mutation is attempted.
            EndpointCompatibility.validate_reference(item.endpoint_a, context.network)
            EndpointCompatibility.validate_reference(item.endpoint_b, context.network)
            result = wire_service.execute(
                __import__(
                    "core.application.commands.simple_wire_commands",
                    fromlist=["CreateSimpleWireConnectionCommand"],
                ).CreateSimpleWireConnectionCommand(
                    connection_id=item.connection_id,
                    endpoint_a=item.endpoint_a,
                    endpoint_b=item.endpoint_b,
                ),
                context,
                transaction,
            )
            if not result.success:
                raise RuntimeError(result.message)
            committed_connections.append(
                {
                    "connection_id": item.connection_id,
                    "sld_connection_id": f"sld-wire-{item.connection_id}",
                    "endpoint_a": dict(item.endpoint_a.to_mapping()),
                    "endpoint_b": dict(item.endpoint_b.to_mapping()),
                }
            )

        active_draft.clear_after_commit()
        transaction.record_undo(
            lambda snapshot=snapshot, draft=active_draft: draft.restore_snapshot(
                snapshot.to_dict()
            )
        )
        return ApplicationResult.success_result(
            message="Commit Network completed.",
            metadata={
                "draft_to_core": MappingProxyType(dict(core_ids)),
                "created_elements": tuple(created),
                "committed_connections": tuple(committed_connections),
                "operation": "network.commit_draft",
                "commit_plan": commit_plan,
            },
        )


__all__ = [
    "DraftCommandHandlers",
    "DraftConnectivityResolver",
    "DraftEquipmentCommitPlan",
    "DraftConnectionCommitPlan",
    "DraftCommitPlan",
    "CommitNetworkHandler",
]
