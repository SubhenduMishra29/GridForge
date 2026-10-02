# ============================================================
# File: ui/workspace/workspace_legacy.py
# GridForge V2 — Legacy Workspace Compatibility
# Author: Subhendu Mishra
# ============================================================
"""Explicit compatibility contracts retired from canonical workspace policy."""

from __future__ import annotations

from dataclasses import dataclass

from .panel_area import PanelArea


@dataclass(frozen=True, slots=True)
class WorkspacePlacement:
    """Legacy panel placement retained only for external migration callers."""

    panel_id: str
    area: PanelArea
    group: str | None = None
    visible: bool = True
    order: int = 0


__all__ = ["WorkspacePlacement"]
