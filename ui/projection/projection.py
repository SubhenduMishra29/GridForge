# ============================================================
# File: ui/projection/projection.py
# GridForge V2 — Generic Projection Contract
# Author: Subhendu Mishra
# ============================================================
"""Framework-neutral contract for projecting Application read state."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.application.read_models import ElementReadModel

from .projection_state import ProjectionState


class Projection(ABC):
    """Presentation projection identified by stable object identity."""

    def __init__(self, object_id: str) -> None:
        if not isinstance(object_id, str) or not object_id:
            raise ValueError("Projection object_id must be a non-empty string")
        self._object_id = object_id
        self._state: ProjectionState | None = None

    @property
    def object_id(self) -> str:
        """Return the immutable identity represented by this projection."""
        return self._object_id

    @property
    def state(self) -> ProjectionState | None:
        """Return the latest UI-facing state snapshot."""
        return self._state

    def set_state(self, state: ProjectionState) -> None:
        """Replace presentation state after an Application read step."""
        if state.object_id != self._object_id:
            raise ValueError("Projection state identity does not match projection object_id")
        self._state = state

    @abstractmethod
    def update_from_read_model(self, read_model: ElementReadModel) -> None:
        """Refresh presentation state from an immutable Application snapshot."""
        raise NotImplementedError


__all__ = ["Projection"]
