"""Compatibility alias for the consolidated branch-domain service.

Cable is owned by :class:`BranchModelService`. This module remains so existing
imports of ``CableModelService`` continue to work without retaining a second
implementation of Cable mutation logic.
"""

from __future__ import annotations

from core.application.services.branch_model_service import BranchModelService


class CableModelService(BranchModelService):
    """Backward-compatible alias over the consolidated branch service."""


__all__ = ["CableModelService"]
