"""Immutable commands and transactional application handler; no Qt imports in this module."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

@dataclass(frozen=True, slots=True)
class AddDraftMotorPlacementCommand:
    motor_id: str
    x: float
    y: float
    parameters: tuple[tuple[str, float], ...] = ()
    def __post_init__(self):
        if not self.motor_id: raise ValueError("motor_id is required")
        if not all(map(lambda v: isinstance(v, (int, float)), (self.x, self.y))): raise TypeError("coordinates must be numeric")

@dataclass(frozen=True, slots=True)
class CommitMotorToNetworkCommand:
    motor_id: str
    wire_id: str
    split_fraction: float = 0.5
    def __post_init__(self):
        if not self.motor_id or not self.wire_id: raise ValueError("motor_id and wire_id are required")
        if not 0.0 < self.split_fraction < 1.0: raise ValueError("split_fraction must be inside (0, 1)")

class MotorPlacementCommandHandler:
    """Adapter over explicit Application services; never edits Core state ad hoc."""
    def __init__(self, application: Any): self.application = application
    def execute(self, command: AddDraftMotorPlacementCommand) -> Any:
        service = getattr(self.application, "motor_draft_service", None)
        if service is None: raise RuntimeError("Application motor_draft_service is not configured")
        return service.add_motor(command.motor_id, (float(command.x), float(command.y)), dict(command.parameters))
    def commit(self, command: CommitMotorToNetworkCommand) -> Any:
        # The service owns snapshot/rollback, topology validation and semantic event emission.
        service = getattr(self.application, "motor_network_service", None)
        if service is None: raise RuntimeError("Application motor_network_service is not configured")
        transaction = service.begin_transaction(command.motor_id, command.wire_id, command.split_fraction)
        try:
            result = transaction.execute()
            transaction.commit()
        except Exception:
            transaction.rollback()  # must restore S0 exactly; rollback errors are surfaced by service
            raise
        if not result: raise RuntimeError("motor topology transaction returned no result")
        return result
