# ============================================================
# GridForge V2 — SLD connection presentation adapter
# ============================================================
"""Bridge snapped presentation identity into the existing SLD command boundary."""

from __future__ import annotations

from typing import Any

from core.application.commands.sld_commands import AddSLDConnectionCommand


class SLDConnectionPresentationAdapter:
    """Create presentation connection state without mutating electrical truth."""

    @staticmethod
    def execute(
        application: Any,
        execute_command: Any,
        *,
        connection_id: str,
        source_snap: Any,
        target_snap: Any,
    ) -> Any:
        service = getattr(application, "sld_service", None)
        if service is None:
            return None
        document = service.document
        source_endpoint = SLDConnectionPresentationAdapter._endpoint(document, source_snap)
        target_endpoint = SLDConnectionPresentationAdapter._endpoint(document, target_snap)
        return execute_command(AddSLDConnectionCommand(
            connection_id=connection_id,
            source_node_id=source_endpoint["node_id"],
            target_node_id=target_endpoint["node_id"],
            source_endpoint=source_endpoint,
            target_endpoint=target_endpoint,
            route={"routing_mode": "orthogonal", "ownership": "auto", "points": []},
        ))

    @staticmethod
    def _endpoint(document: Any, snap: Any) -> dict[str, Any]:
        source = getattr(snap, "source", None)
        object_id = getattr(snap, "object_id", None)
        if source is None or object_id is None:
            raise ValueError("SLD presentation connection requires an object snap")
        node = document.model.get_node_by_equipment_id_optional(str(object_id))
        if node is None:
            raise ValueError(f"No SLD node exists for snapped object {object_id!r}")
        bus_id = getattr(snap, "bus_id", None)
        attachment_id = getattr(snap, "attachment_id", None)
        if bus_id is not None:
            if attachment_id is None:
                raise ValueError("Bus presentation connection requires attachment_id")
            return {"kind": "bus", "node_id": node.node_id, "bus_id": str(bus_id), "attachment_id": str(attachment_id)}
        terminal_name = getattr(snap, "terminal_name", None)
        if not isinstance(terminal_name, str) or not terminal_name:
            raise ValueError("Equipment presentation connection requires terminal_name")
        return {"kind": "equipment", "node_id": node.node_id, "equipment_id": str(object_id), "terminal_role": terminal_name}


__all__ = ["SLDConnectionPresentationAdapter"]
