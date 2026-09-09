"""Compatibility alias for the consolidated branch-domain service.

Line is owned by :class:`BranchModelService`. This module remains so existing
imports of ``LineModelService`` continue to work without retaining a second
implementation of Line mutation logic.
"""

from __future__ import annotations

from core.application.services.branch_model_service import BranchModelService


class LineModelService(BranchModelService):
    """Backward-compatible alias over the consolidated branch service."""


__all__ = ["LineModelService"]
