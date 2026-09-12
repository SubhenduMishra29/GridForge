# ============================================================
# File: ui/workspace/__init__.py
# GridForge V2 — Workspace / Layout Layer
# Author: Subhendu Mishra
# ============================================================
"""Public API for GridForge Project / Document / Workspace boundaries."""

from .project import Project
from .document import Document
from .document_manager import DocumentManager
from .panel_area import PanelArea
from .view_manager import ViewManager, ViewRecord
from .viewport_state import ViewportState
from .workspace import Workspace
from .workspace_definition import WorkspaceDefinition, WorkspacePlacement
from .workspace_layout import WorkspaceLayout
from .workspace_manager import WorkspaceManager
from .workspace_state import WorkspaceState
from .workspace_realizer import DockBinding, WorkspaceRealizationError, WorkspaceRealizer
from .workspace_controller import WorkspaceController
from .project_workspace import ProjectWorkspaceLifecycle, ProjectWorkspaceState
from .project_workspace_adapter import (
    ProjectWorkspaceApplicationAdapter,
    ProjectWorkspaceChanged,
    WorkspaceUpdateHandler,
)

__all__ = [
    "Project", "Document", "DocumentManager", "PanelArea",
    "ViewManager", "ViewRecord", "ViewportState", "Workspace",
    "WorkspaceDefinition", "WorkspacePlacement", "WorkspaceLayout",
    "WorkspaceManager", "WorkspaceState", "WorkspaceController",
    "ProjectWorkspaceLifecycle", "ProjectWorkspaceState",
    "ProjectWorkspaceApplicationAdapter", "ProjectWorkspaceChanged", "WorkspaceUpdateHandler",
    "DockBinding", "WorkspaceRealizationError", "WorkspaceRealizer",
]
