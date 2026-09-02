# ============================================================
# File: ui/projection/projection_adapter.py
# GridForge V2 — Projection Adapter Contract
# Author: Subhendu Mishra
# ============================================================
"""Boundary contract for converting Application read data to UI state.

The adapter deliberately consumes immutable Application read models rather
than authoritative Core objects. This keeps the Presentation layer from
bypassing the Application read boundary.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.application.read_models import ElementReadModel

from .projection_state import ProjectionState


class ProjectionAdapter(ABC):
    """Translate Application read data into UI-only projection state."""

    @abstractmethod
    def project(self, read_model: ElementReadModel) -> ProjectionState:
        """Build presentation state without mutating the supplied snapshot."""
        raise NotImplementedError
