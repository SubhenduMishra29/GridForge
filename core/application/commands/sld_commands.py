# ============================================================
# File: core/application/commands/sld_commands.py
# GridForge V2 — Immutable SLD presentation commands
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from uuid import UUID, uuid4

from ..command import Command


SET_SLD_NODE_POSITION = "sld.set_node_position"
ADD_SLD_NODE = "sld.add_node"
REMOVE_SLD_NODE = "sld.remove_node"
ADD_SLD_CONNECTION = "sld.add_connection"
REMOVE_SLD_CONNECTION = "sld.remove_connection"


class SetSLDNodePositionCommand(Command):
    def __init__(self, *, node_id: str, x: float, y: float,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(command_type=SET_SLD_NODE_POSITION,
                         payload={"node_id": node_id, "x": float(x), "y": float(y)},
                         command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class AddSLDNodeCommand(Command):
    def __init__(self, *, node_id: str, equipment_id: str | None = None,
                 x: float = 0.0, y: float = 0.0,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(command_type=ADD_SLD_NODE,
                         payload={"node_id": node_id, "equipment_id": equipment_id, "x": float(x), "y": float(y)},
                         command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class RemoveSLDNodeCommand(Command):
    def __init__(self, *, node_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=REMOVE_SLD_NODE, payload={"node_id": node_id},
                         command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class AddSLDConnectionCommand(Command):
    def __init__(self, *, connection_id: str, source_node_id: str, target_node_id: str,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(command_type=ADD_SLD_CONNECTION,
                         payload={"connection_id": connection_id, "source_node_id": source_node_id, "target_node_id": target_node_id},
                         command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class RemoveSLDConnectionCommand(Command):
    def __init__(self, *, connection_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=REMOVE_SLD_CONNECTION, payload={"connection_id": connection_id},
                         command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


__all__ = [
    "SET_SLD_NODE_POSITION", "ADD_SLD_NODE", "REMOVE_SLD_NODE",
    "ADD_SLD_CONNECTION", "REMOVE_SLD_CONNECTION",
    "SetSLDNodePositionCommand", "AddSLDNodeCommand", "RemoveSLDNodeCommand",
    "AddSLDConnectionCommand", "RemoveSLDConnectionCommand",
]
