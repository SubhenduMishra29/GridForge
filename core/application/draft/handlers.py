# ============================================================
# File: core/application/draft/handlers.py
# GridForge V2
# Author: Subhendu Mishra
# ============================================================
from __future__ import annotations

from uuid import uuid4
from core.model import EndpointReference, EquipmentType
from ..creation import CreationCommitIntent, CreationCommandPreparer
from ..results import ApplicationResult
from ..services.model_service import ModelService
from ..services.simple_wire_service import SimpleWireConnectionService
from .network import DraftConnection, DraftEndpointReference, DraftEquipment, DraftNetwork


class DraftCommandHandlers:
    def __init__(self, draft_provider): self._draft_provider = draft_provider
    def _draft(self) -> DraftNetwork:
        draft = self._draft_provider()
        if draft is None: raise RuntimeError("Application DraftNetwork is not active.")
        return draft
    def handlers(self):
        return {"draft.add_equipment": self.add_equipment, "draft.update_equipment": self.update_equipment,
                "draft.remove_equipment": self.remove_equipment, "draft.add_connection": self.add_connection, "draft.create_connection": self.add_connection,
                "draft.remove_connection": self.remove_connection}
    def add_equipment(self, command, context, transaction):
        draft=self._draft(); item=DraftEquipment.from_dict(command.payload["equipment"]); draft.add_equipment(item)
        transaction.record_undo(lambda: draft.remove_equipment(item.draft_id))
        return ApplicationResult.success_result(message=f"Draft equipment {item.draft_id} added.", metadata={"draft_id":item.draft_id})
    def update_equipment(self, command, context, transaction):
        draft=self._draft(); item=draft.require_equipment(str(command.payload["draft_id"])); before=item
        draft.update_equipment(item.draft_id, **dict(command.payload["changes"]))
        transaction.record_undo(lambda: draft.update_equipment(before.draft_id, display_name=before.display_name, engineering_data=dict(before.engineering_data), endpoints=dict(before.endpoints), placement=before.placement, presentation=dict(before.presentation), validation_state=dict(before.validation_state)))
        return ApplicationResult.success_result(message=f"Draft equipment {item.draft_id} updated.", metadata={"draft_id":item.draft_id})
    def remove_equipment(self, command, context, transaction):
        draft=self._draft(); draft_id=str(command.payload["draft_id"])
        item=draft.require_equipment(draft_id)
        incident=tuple(connection for connection in draft.connections if connection.source.object_id == draft_id or connection.target.object_id == draft_id)
        draft.remove_equipment(draft_id)
        def restore():
            draft.add_equipment(item)
            for connection in incident: draft.add_connection(connection)
        transaction.record_undo(restore)
        return ApplicationResult.success_result(message=f"Draft equipment {item.draft_id} removed.", metadata={"draft_id":item.draft_id})
    def add_connection(self, command, context, transaction):
        draft=self._draft(); item=DraftConnection.from_dict(command.payload["connection"]); draft.add_connection(item); transaction.record_undo(lambda:draft.remove_connection(item.connection_id))
        return ApplicationResult.success_result(message=f"Draft connection {item.connection_id} added.", metadata={"connection_id":item.connection_id})
    def remove_connection(self, command, context, transaction):
        draft=self._draft(); item=draft.remove_connection(str(command.payload["connection_id"])); transaction.record_undo(lambda:draft.add_connection(item))
        return ApplicationResult.success_result(message=f"Draft connection {item.connection_id} removed.", metadata={"connection_id":item.connection_id})


class CommitNetworkHandler:
    def __init__(self, draft_provider): self._draft_provider = draft_provider

    @staticmethod
    def _endpoint(ref: DraftEndpointReference, core_id_map: dict[str, str]) -> EndpointReference:
        if ref.is_bus:
            # Bus identities are already authoritative Core identities; they
            # never pass through the equipment ID map.
            return EndpointReference.bus(ref.object_id, ref.attachment_id or "")
        try: equipment_type = EquipmentType(ref.equipment_type or "")
        except ValueError as exc: raise ValueError(f"Unsupported draft endpoint equipment type: {ref.equipment_type!r}") from exc
        core_id = core_id_map.get(ref.object_id, ref.object_id)
        return EndpointReference.terminal(equipment_type=equipment_type, equipment_id=core_id, terminal_role=ref.terminal_role or "")

    def __call__(self, command, context, transaction):
        draft=self._draft_provider(); payload=command.payload
        if draft is None: raise RuntimeError("Application DraftNetwork is not active.")
        if payload["project_id"] != draft.project_id or int(payload["activation_generation"]) != draft.activation_generation: raise ValueError("CommitNetworkCommand draft scope does not match the active project generation.")
        errors=draft.validate()
        if errors: raise ValueError("Draft validation failed: "+"; ".join(errors))
        snapshot=DraftNetwork.from_dict(draft.to_dict(), project_id=draft.project_id, activation_generation=draft.activation_generation)
        model=ModelService(context.network); core_ids={item.draft_id:f"{item.equipment_type}-{uuid4().hex}" for item in snapshot.equipment}; created=[]
        from ..command_handlers import ModelCommandHandlers
        model_handlers=ModelCommandHandlers(model).handlers()
        for item in snapshot.equipment:
            endpoints={role:self._endpoint(ref, core_ids) for role,ref in item.endpoints.items()}
            child=CreationCommandPreparer.prepare(CreationCommitIntent(command_type=item.command_type,id_field=item.id_field,object_id=core_ids[item.draft_id],parameter_mapping=dict(item.parameter_mapping),endpoint_mapping=dict(item.endpoint_mapping),values=dict(item.engineering_data),endpoints=endpoints,position=item.placement))
            result=model_handlers[child.command_type](child, context, transaction)
            if not result.success: raise RuntimeError(result.message)
            created.append({"draft_id":item.draft_id,"core_id":core_ids[item.draft_id],"sld_node_id":f"sld-draft-{item.draft_id}","element_type":item.equipment_type,"x":item.placement[0] if item.placement else None,"y":item.placement[1] if item.placement else None,"presentation":dict(item.presentation)})
        wire_service=SimpleWireConnectionService(); committed_connections=[]
        from ..commands.simple_wire_commands import CreateSimpleWireConnectionCommand
        for item in snapshot.connections:
            a=self._endpoint(item.source, core_ids); b=self._endpoint(item.target, core_ids)
            result=wire_service.execute(CreateSimpleWireConnectionCommand(connection_id=item.connection_id, endpoint_a=a, endpoint_b=b), context, transaction)
            if not result.success: raise RuntimeError(result.message)
            committed_connections.append({"connection_id":item.connection_id,"sld_connection_id":f"sld-draft-{item.connection_id}","endpoint_a":dict(a.to_mapping()),"endpoint_b":dict(b.to_mapping()),"source_draft_id":item.source.object_id,"target_draft_id":item.target.object_id,"source_is_draft":item.source.scope == "draft","target_is_draft":item.target.scope == "draft"})
        draft.clear_after_commit(); transaction.record_undo(lambda:draft.restore_snapshot(snapshot.to_dict()))
        return ApplicationResult.success_result(message="Commit Network completed.", metadata={"draft_to_core":core_ids,"created_elements":tuple(created),"committed_connections":tuple(committed_connections),"operation":"network.commit_draft"})


__all__=["DraftCommandHandlers","CommitNetworkHandler"]
