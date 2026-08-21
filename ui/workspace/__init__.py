"""
GridForge V2 — Workspace / Layout Layer.
"""

from .panel_area import PanelArea
from .workspace_definition import (
    WorkspaceDefinition,
    WorkspacePlacement,
)
from .workspace_layout import WorkspaceLayout
from .workspace_manager import WorkspaceManager
from .workspace_state import WorkspaceState

__all__ = [
    "PanelArea",
    "WorkspaceDefinition",
    "WorkspacePlacement",
    "WorkspaceLayout",
    "WorkspaceManager",
    "WorkspaceState",
]
