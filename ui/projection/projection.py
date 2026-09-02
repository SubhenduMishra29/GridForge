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


class Projection(ABC):
    """Base contract for a projection identified by a stable Core object ID."""

    def __init__(self, object_id: str) -> None:
        if not isinstance(object_id, str) or not object_id:
            raise ValueError("Projection object_id must be a non-empty string")
        self._object_id = object_id

    @property
    def object_id(self) -> str:
        """Return the immutable Core object identity represented by this projection."""
        return self._object_id

    @abstractmethod
    def update_from_model(self, model_object: Any) -> None:
        """Refresh presentation state from authoritative model state."""
        raise NotImplementedError
