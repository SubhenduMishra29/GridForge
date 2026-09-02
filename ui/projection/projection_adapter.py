# ============================================================
# File: ui/projection/projection_adapter.py
# GridForge V2 — Projection Adapter Contract
# Author: Subhendu Mishra
# ============================================================
"""Boundary contract for converting authoritative model state to projection state."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .projection_state import ProjectionState


class ProjectionAdapter(ABC):
    """Translate authoritative read data into UI-only projection state."""

    @abstractmethod
    def project(self, model_object: Any) -> ProjectionState:
        """Build presentation state without mutating the supplied model."""
        raise NotImplementedError
