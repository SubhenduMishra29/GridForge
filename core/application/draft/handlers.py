# ============================================================
# File: core/application/draft/handlers.py
# GridForge V2
# Author: Subhendu Mishra
# ============================================================
"""Application-owned draft authoring and deterministic Draft→Core commit."""

from __future__ import annotations

from typing import Any, Mapping

from core.model import EndpointReference, EquipmentType
from ..creation import CreationCommitIntent, CreationCommandPreparer
from ..results import ApplicationResult
from ..services.simple_wire_service import SimpleWireConnectionService
from .network import DraftConnection, DraftNetwork


def _thaw_payload(value: Any) -> Any:
    """Convert immutable Command containers into canonical mutable containers."""
    if isinstance(value, Mapping):
        return {key: _thaw_payload(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_payload(item) for item in value]
    if isinstance(value, frozenset):
        return {_thaw_payload(item) for item in value}
    return value


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
        equipment = __import__("core.application.draft.network", fromlist=["DraftEquipment"]).DraftEquipment.from_dict(
            _thaw_payload(command.payload["equipment"])
        )
        draft.add_equipment(equipment)
        return ApplicationResult.success_result({"draft_id": equipment.draft_id})

    def update_equipment(self, command, context, transaction):
        draft = self._draft()
        equipment = draft.update_equipment(
            str(command.payload["draft_id"]),
            **_thaw_payload(command.payload["changes"]),
        )
        return ApplicationResult.success_result({"draft_id": equipment.draft_id})

    def remove_equipment(self, command, context, transaction):
        draft = self._draft()
        equipment = draft.remove_equipment(str(command.payload["draft_id"]))
        return ApplicationResult.success_result({"draft_id": equipment.draft_id})

    def add_connection(self, command, context, transaction):
        draft = self._draft()
        connection = DraftConnection.from_dict(_thaw_payload(command.payload["connection"]))
        draft.add_connection(connection)
        return ApplicationResult.success_result({"connection_id": connection.connection_id})

    def remove_connection(self, command, context, transaction):
        draft = self._draft()
        connection = draft.remove_connection(str(command.payload["connection_id"]))
        return ApplicationResult.success_result({"connection_id": connection.connection_id})


class DraftConnectivityResolver:
    def _to_core_endpoint(self, endpoint, core_id_map):
        """Translate one canonical DraftEndpointReference to Core identity."""
        if endpoint.scope == "draft":
            try:
                core_id = core_id_map[endpoint.object_id]
            except KeyError as exc:
                raise ValueError(
                    f"Draft endpoint references unknown draft equipment {endpoint.object_id!r}."
                ) from exc
        else:
            core_id = endpoint.object_id

        if endpoint.is_bus:
            return EndpointReference.bus(
                core_id,
                endpoint.attachment_id or "",
            )

        try:
            equipment_type = EquipmentType(endpoint.equipment_type or "")
        except ValueError as exc:
            raise ValueError(
                f"Unsupported draft endpoint equipment type: {endpoint.equipment_type!r}"
            ) from exc
        return EndpointReference.terminal(
            equipment_type=equipment_type,
            equipment_id=core_id,
            terminal_role=endpoint.terminal_role or "",
        )

    _to_core_connection_endpoint = _to_core_endpoint


class CommitNetworkHandler:
    def __init__(self, draft_provider, command_executor):
        if not callable(command_executor):
            raise TypeError("command_executor must be callable.")
        self._draft_provider = draft_provider
        self._command_executor = command_executor
        self._resolver = DraftConnectivityResolver()

    @staticmethod
    def _core_id_for(item) -> str:
        """Derive the deterministic Application-owned Core identity for a draft."""
        equipment_type = str(item.equipment_type).strip().lower()
        draft_id = str(item.draft_id).strip()
        if not equipment_type or not draft_id:
            raise ValueError("Draft equipment requires non-empty type and draft identity.")
        return f"{equipment_type}-{draft_id}"

    def _resolve_equipment_endpoints(self, item, core_ids):
        resolved = {}
        for semantic_name, endpoint in sorted(item.endpoints.items(), key=lambda pair: str(pair[0])):
            if semantic_name not in item.endpoint_mapping:
                raise ValueError(
                    f"{item.draft_id}: endpoint {semantic_name!r} is not present in the canonical endpoint mapping."
                )
            resolved[str(semantic_name)] = self._resolver._to_core_endpoint(endpoint, core_ids)
        return resolved

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

        draft_payload = _thaw_payload(payload["draft_network"])
        snapshot = DraftNetwork.from_dict(
            draft_payload,
            project_id=project_id,
            activation_generation=activation_generation,
        )
        if snapshot.to_dict() != draft_payload:
            raise ValueError("CommitNetworkCommand draft_network payload is not canonical.")

        errors = snapshot.validate(getattr(context, "network", None))
        if errors:
            raise ValueError("Draft validation failed: " + "; ".join(errors))
        if not snapshot.equipment and not snapshot.connections:
            raise ValueError(
                "DraftNetwork commit is empty; add equipment or connections before committing."
            )

        network = getattr(context, "network", None)
        if network is None:
            raise RuntimeError("CommitNetworkHandler requires the canonical Core Network.")

        # Allocate deterministic identities and detect global Core collisions
        # before any Core mutation is permitted.
        core_ids = {
            item.draft_id: self._core_id_for(item)
            for item in sorted(snapshot.equipment, key=lambda item: item.draft_id)
        }
        if len(set(core_ids.values())) != len(core_ids):
            raise ValueError("Draft equipment maps to duplicate Core identities.")

        for draft_id, core_id in core_ids.items():
            try:
                network.get_by_identity(core_id)
            except KeyError:
                continue
            raise ValueError(
                f"Core identity collision: draft equipment {draft_id!r} "
                f"maps to existing Core identity {core_id!r}."
            )

        # Prepare every Core equipment command before the first transaction
        # mutation. CreationCommandPreparer is the sole creation translation
        # boundary; command construction performs the canonical required-field
        # and payload-shape checks.
        preparer = CreationCommandPreparer()
        prepared_commands = []
        created_elements = []
        for item in sorted(snapshot.equipment, key=lambda value: value.draft_id):
            values = dict(item.engineering_data)
            # display_name is only projected into an existing canonical name
            # parameter mapping; it is never added as an ad-hoc intent field.
            if "name" not in values:
                for parameter_id, command_field in item.parameter_mapping.items():
                    if command_field == "name":
                        values[parameter_id] = item.display_name
                        break

            intent = CreationCommitIntent(
                command_type=item.command_type,
                id_field=item.id_field,
                object_id=core_ids[item.draft_id],
                parameter_mapping=dict(item.parameter_mapping),
                endpoint_mapping=dict(item.endpoint_mapping),
                values=values,
                endpoints=self._resolve_equipment_endpoints(item, core_ids),
                position=item.placement,
            )
            prepared = preparer.prepare(intent)
            prepared_commands.append(prepared)
            x, y = item.placement if item.placement is not None else (None, None)
            created_elements.append({
                "draft_id": item.draft_id,
                "core_id": core_ids[item.draft_id],
                "element_type": item.equipment_type,
                "x": x,
                "y": y,
                "presentation": dict(item.presentation),
                "sld_node_id": f"sld-core-{core_ids[item.draft_id]}",
            })

        # Prepare every Simple Wire command before the first Core mutation as
        # well. DraftConnectivityResolver remains the sole endpoint identity
        # translation boundary; the Simple Wire service owns command creation.
        connection_service = SimpleWireConnectionService()
        prepared_connections = []
        committed_connections = []
        for connection in sorted(snapshot.connections, key=lambda value: value.connection_id):
            source = self._resolver._to_core_connection_endpoint(connection.source, core_ids)
            target = self._resolver._to_core_connection_endpoint(connection.target, core_ids)
            prepared_connections.append(
                connection_service.create_command(
                    connection_id=connection.connection_id,
                    source=source,
                    target=target,
                )
            )
            committed_connections.append({
                "connection_id": connection.connection_id,
                "endpoint_a": dict(source.to_mapping()),
                "endpoint_b": dict(target.to_mapping()),
                "connection_kind": connection.connection_kind,
                "route": dict(connection.route),
            })

        # Draft authoring state is a transaction participant. It is cleared
        # for the successful commit, and the registered inverse restores the
        # exact command snapshot if Core/SLD pre-commit validation fails or if
        # the committed history entry is undone.
        draft_snapshot = active_draft.to_dict()
        transaction.record_undo(
            lambda snapshot=draft_snapshot, draft=active_draft: draft.restore_snapshot(snapshot)
        )

        for prepared_command in prepared_commands:
            self._command_executor(prepared_command, transaction)

        for prepared_command in prepared_connections:
            self._command_executor(prepared_command, transaction)

        active_draft.clear_after_commit()
        return ApplicationResult.success_result(
            value={
                "project_id": project_id,
                "equipment_count": len(snapshot.equipment),
                "connection_count": len(snapshot.connections),
            },
            metadata={
            "created_elements": tuple(created_elements),
                "committed_connections": tuple(committed_connections),
            },
        )


__all__ = ["DraftCommandHandlers", "DraftConnectivityResolver", "CommitNetworkHandler"]
