# ============================================================
# File: core/application/commands/draft_commands.py
# GridForge V2 — Document-scoped Draft/Commit Application Commands
# Author: Subhendu Mishra
# ============================================================
from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID, uuid4

from ..command import Command

ADD_DRAFT_EQUIPMENT = "draft.add_equipment"
UPDATE_DRAFT_EQUIPMENT = "draft.update_equipment"
REMOVE_DRAFT_EQUIPMENT = "draft.remove_equipment"
ADD_DRAFT_CONNECTION = "draft.add_connection"
CREATE_DRAFT_CONNECTION = "draft.create_connection"
REMOVE_DRAFT_CONNECTION = "draft.remove_connection"
UPDATE_DRAFT_CONNECTION_ROUTE = "draft.update_connection_route"
COMMIT_NETWORK = "network.commit_draft"
PASTE_DRAFT_SELECTION = "draft.paste_selection"


def _document_payload(document_id: str | None) -> dict[str, str]:
    if document_id is None:
        return {}
    if not isinstance(document_id, str) or not document_id.strip():
        raise ValueError("Draft command document_id must be a non-empty string.")
    return {"document_id": document_id.strip()}


class _DraftCommand(Command):
    def __init__(
        self,
        command_type: str,
        payload: Mapping[str, Any],
        *,
        document_id: str | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ):
        data = dict(payload)
        data.update(_document_payload(document_id))
        super().__init__(
            command_type=command_type,
            payload=data,
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class AddDraftEquipmentCommand(_DraftCommand):
    def __init__(self, *, equipment: Mapping[str, Any], document_id: str | None = None, command_id=None, correlation_id=None, causation_id=None):
        super().__init__(ADD_DRAFT_EQUIPMENT, {"equipment": dict(equipment)}, document_id=document_id, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class UpdateDraftEquipmentCommand(_DraftCommand):
    def __init__(self, *, draft_id: str, changes: Mapping[str, Any], document_id: str | None = None, command_id=None, correlation_id=None, causation_id=None):
        super().__init__(UPDATE_DRAFT_EQUIPMENT, {"draft_id": draft_id, "changes": dict(changes)}, document_id=document_id, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class RemoveDraftEquipmentCommand(_DraftCommand):
    def __init__(self, *, draft_id: str, document_id: str | None = None, command_id=None, correlation_id=None, causation_id=None):
        super().__init__(REMOVE_DRAFT_EQUIPMENT, {"draft_id": draft_id}, document_id=document_id, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class CreateDraftConnectionCommand(_DraftCommand):
    """Immutable authoring command for one canonical DraftConnection."""
    def __init__(self, *, connection: Mapping[str, Any], document_id: str | None = None, command_id=None, correlation_id=None, causation_id=None):
        super().__init__(CREATE_DRAFT_CONNECTION, {"connection": dict(connection)}, document_id=document_id, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class AddDraftConnectionCommand(_DraftCommand):
    def __init__(self, *, connection: Mapping[str, Any], document_id: str | None = None, command_id=None, correlation_id=None, causation_id=None):
        super().__init__(ADD_DRAFT_CONNECTION, {"connection": dict(connection)}, document_id=document_id, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class RemoveDraftConnectionCommand(_DraftCommand):
    def __init__(self, *, connection_id: str, document_id: str | None = None, command_id=None, correlation_id=None, causation_id=None):
        super().__init__(REMOVE_DRAFT_CONNECTION, {"connection_id": connection_id}, document_id=document_id, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class UpdateDraftConnectionRouteCommand(_DraftCommand):
    """Replace route geometry on an existing DraftConnection."""
    def __init__(
        self,
        *,
        project_id: str,
        activation_generation: int,
        connection_id: str,
        route: Mapping[str, Any],
        document_id: str | None = None,
        command_id=None,
        correlation_id=None,
        causation_id=None,
    ):
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("Draft route update requires a project_id.")
        if isinstance(activation_generation, bool) or not isinstance(activation_generation, int) or activation_generation < 1:
            raise ValueError("Draft route update requires a positive integer activation_generation.")
        if not isinstance(connection_id, str) or not connection_id.strip():
            raise ValueError("Draft route update requires a connection_id.")
        if not isinstance(route, Mapping):
            raise TypeError("Draft route update route must be a mapping.")
        super().__init__(
            UPDATE_DRAFT_CONNECTION_ROUTE,
            {
                "project_id": project_id.strip(),
                "activation_generation": int(activation_generation),
                "connection_id": connection_id.strip(),
                "route": dict(route),
            },
            document_id=document_id,
            command_id=command_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class PasteDraftSelectionCommand(_DraftCommand):
    """Atomically add a semantic clipboard selection to one document's DraftNetwork."""

    def __init__(
        self,
        *,
        equipment: tuple[Mapping[str, Any], ...],
        connections: tuple[Mapping[str, Any], ...],
        document_id: str,
        command_id=None,
        correlation_id=None,
        causation_id=None,
    ):
        if not isinstance(equipment, (tuple, list)) or not equipment:
            raise ValueError("A draft clipboard paste requires at least one equipment item.")
        if not isinstance(connections, (tuple, list)):
            raise TypeError("Draft clipboard connections must be a sequence.")
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError("Draft clipboard paste requires the active SLD document identity.")
        if any(not isinstance(item, Mapping) for item in (*equipment, *connections)):
            raise TypeError("Draft clipboard equipment and connections must be mappings.")
        super().__init__(
            PASTE_DRAFT_SELECTION,
            {
                "equipment": tuple(dict(item) for item in equipment),
                "connections": tuple(dict(item) for item in connections),
            },
            document_id=document_id,
            command_id=command_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class CommitNetworkCommand(_DraftCommand):
    """One immutable boundary crossing from one document's DraftNetwork to Core."""
    def __init__(self, *, project_id: str, activation_generation: int, draft_network: Mapping[str, Any], document_id: str | None = None, command_id=None, correlation_id=None, causation_id=None):
        super().__init__(
            COMMIT_NETWORK,
            {"project_id": project_id, "activation_generation": int(activation_generation), "draft_network": dict(draft_network)},
            document_id=document_id,
            command_id=command_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


__all__ = [
    "ADD_DRAFT_EQUIPMENT", "UPDATE_DRAFT_EQUIPMENT", "REMOVE_DRAFT_EQUIPMENT",
    "ADD_DRAFT_CONNECTION", "CREATE_DRAFT_CONNECTION", "REMOVE_DRAFT_CONNECTION",
    "UPDATE_DRAFT_CONNECTION_ROUTE", "COMMIT_NETWORK", "PASTE_DRAFT_SELECTION", "PasteDraftSelectionCommand", "AddDraftEquipmentCommand",
    "UpdateDraftEquipmentCommand", "RemoveDraftEquipmentCommand",
    "CreateDraftConnectionCommand", "AddDraftConnectionCommand",
    "RemoveDraftConnectionCommand", "UpdateDraftConnectionRouteCommand",
    "CommitNetworkCommand",
]
