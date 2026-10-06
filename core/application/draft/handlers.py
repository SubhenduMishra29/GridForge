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
from ..services.model_service import ModelService
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

        model = ModelService(context.network)
        core_ids = {
            item.draft_id: f"{item.equipment_type}-{item.draft_id}"
            for item in sorted(snapshot.equipment, key=lambda item: item.draft_id)
        }

        for draft_id, core_id in core_ids.items():
            try:
                context.network.get_by_identity(core_id)
            except KeyError:
                continue
            raise ValueError(
                f"Core identity collision: draft equipment {draft_id!r} "
                f"maps to existing Core identity {core_id!r}."
            )

        intents = [
            CreationCommitIntent(
                equipment_type=item.equipment_type,
                draft_id=item.draft_id,
                display_name=item.display_name,
                engineering_data=dict(item.engineering_data),
                placement=item.placement,
                command_type=item.command_type,
                id_field=item.id_field,
                parameter_mapping=dict(item.parameter_mapping),
                endpoint_mapping=dict(item.endpoint_mapping),
            )
            for item in sorted(snapshot.equipment, key=lambda value: value.draft_id)
        ]

        prepared = CreationCommandPreparer(model=model).prepare_many(intents)
        for prepared_command in prepared:
            transaction.execute(prepared_command)

        connection_service = SimpleWireConnectionService(model)
        for connection in sorted(snapshot.connections, key=lambda value: value.connection_id):
            source = self._resolver._to_core_connection_endpoint(connection.source, core_ids)
            target = self._resolver._to_core_connection_endpoint(connection.target, core_ids)
            transaction.execute(
                connection_service.create_command(
                    source=source,
                    target=target,
                    route=dict(connection.route),
                )
            )

        active_draft.clear_after_commit()
        return ApplicationResult.success_result({
            "project_id": project_id,
            "equipment_count": len(snapshot.equipment),
            "connection_count": len(snapshot.connections),
        })


__all__ = ["DraftCommandHandlers", "DraftConnectivityResolver", "CommitNetworkHandler"]
