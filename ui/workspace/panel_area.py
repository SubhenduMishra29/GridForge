"""
GridForge V2 — Workspace Logical Panel Areas.

Defines the canonical logical workspace areas used by GridForge.

This module is intentionally Qt-independent.
"""
# ui/workspace/panel_area.py
from __future__ import annotations

from enum import Enum


class PanelArea(str, Enum):
    """
    Canonical logical workspace areas.

    These values belong to GridForge's workspace model and must not
    be confused with Qt.DockWidgetArea.
    """

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    FLOATING = "floating"


__all__ = [
    "PanelArea",
]
