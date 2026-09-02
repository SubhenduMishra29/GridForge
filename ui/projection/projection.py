# ============================================================
# File: ui/projection/projection.py
# GridForge V2 — Generic Projection Contract
# Author: Subhendu Mishra
# ============================================================
"""Framework-neutral contract for projecting authoritative model state.

A projection translates authoritative application/core state into a UI-facing
representation. It owns no engineering truth and performs no core mutation.
Concrete projections may add presentation-specific behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .projection_state import ProjectionState


class Projection(ABC):
    """Presentation projection identified by stable Core object identity."""

    def __init__(self, object_id: str) -> None:
        if not isinstance(object_id, str) or not object_id:
            raise ValueError("Projection object_id must be a non-empty string")
        self._object_id = object_id
        self._state: ProjectionState | None = None

    @property
    def object_id(self) -> str:
        """Return the immutable Core object identity represented by this projection."""
        return self._object_id

    @property
    def state(self) -> ProjectionState | None:
        """Return the latest UI-facing state snapshot, if one has been projected."""
        return self._state

    def set_state(self, state: ProjectionState) -> None:
        """Replace presentation state after an authoritative read/projection step."""
        if state.object_id != self._object_id:
            raise ValueError("Projection state identity does not match projection object_id")
        self._state = state

    @abstractmethod
    def update_from_model(self, model_object: Any) -> None:
        """Refresh presentation state from authoritative model state."""
        raise NotImplementedError
