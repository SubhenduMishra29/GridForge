"""Immutable Application commands for first-class Core Junctions."""
from __future__ import annotations
from uuid import UUID, uuid4
from ..command import Command
from ..reversible import ReversibleCommand

CREATE_JUNCTION = "connectivity.create_junction"
REMOVE_JUNCTION = "connectivity.remove_junction"

def _canonical_junction_id(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("junction_id must be a non-empty string.")
    if value != value.strip():
        raise ValueError("junction_id must already be canonical.")
    return value

class CreateJunctionCommand(ReversibleCommand):
    """Create one first-class topology Junction."""
    def __init__(self, *, junction_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        canonical_id = _canonical_junction_id(junction_id)
        super().__init__(command_type=CREATE_JUNCTION, payload={"junction_id": canonical_id},
                         command_id=command_id or uuid4(), correlation_id=correlation_id,
                         causation_id=causation_id)
    @property
    def junction_id(self) -> str:
        return str(self.payload["junction_id"])
    def inverse(self) -> Command:
        return RemoveJunctionCommand(junction_id=self.junction_id,
                                      correlation_id=self.correlation_id, causation_id=self.command_id)

class RemoveJunctionCommand(ReversibleCommand):
    """Remove a Junction only when Network topology permits it."""
    def __init__(self, *, junction_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        canonical_id = _canonical_junction_id(junction_id)
        super().__init__(command_type=REMOVE_JUNCTION, payload={"junction_id": canonical_id},
                         command_id=command_id or uuid4(), correlation_id=correlation_id,
                         causation_id=causation_id)
    @property
    def junction_id(self) -> str:
        return str(self.payload["junction_id"])
    def inverse(self) -> Command:
        return CreateJunctionCommand(junction_id=self.junction_id,
                                     correlation_id=self.correlation_id, causation_id=self.command_id)

__all__ = ["CREATE_JUNCTION", "REMOVE_JUNCTION", "CreateJunctionCommand", "RemoveJunctionCommand"]
