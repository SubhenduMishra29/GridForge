# ============================================================
# File: ui/workspace/__init__.py
# GridForge V2 — Workspace / Layout Layer
# Author: Subhendu Mishra
# ============================================================
"""Public API for GridForge Project / Document / Workspace boundaries.

The package initializer intentionally exposes these names lazily. Workspace
components reference each other across the Project/Document/Workspace graph;
eager imports here create import-time cycles before the UI composition root
has been constructed.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "Project": ("ui.workspace.project", "Project"),
    "Document": ("ui.workspace.document", "Document"),
    "DocumentManager": ("ui.workspace.document_manager", "DocumentManager"),
    "PanelArea": ("ui.workspace.panel_area", "PanelArea"),
    "ViewManager": ("ui.workspace.view_manager", "ViewManager"),
    "ViewRecord": ("ui.workspace.view_manager", "ViewRecord"),
    "ViewportState": ("ui.workspace.viewport_state", "ViewportState"),
    "WorkspaceDefinition": ("ui.workspace.workspace_definition", "WorkspaceDefinition"),
    "WorkspacePlacement": ("ui.workspace.workspace_definition", "WorkspacePlacement"),
    "WorkspaceLayout": ("ui.workspace.workspace_layout", "WorkspaceLayout"),
    "WorkspaceManager": ("ui.workspace.workspace_manager", "WorkspaceManager"),
    "WorkspaceState": ("ui.workspace.workspace_state", "WorkspaceState"),
    "DockBinding": ("ui.workspace.workspace_realizer", "DockBinding"),
    "WorkspaceRealizationError": ("ui.workspace.workspace_realizer", "WorkspaceRealizationError"),
    "WorkspaceRealizer": ("ui.workspace.workspace_realizer", "WorkspaceRealizer"),
    "WorkspaceController": ("ui.workspace.workspace_controller", "WorkspaceController"),
    "ProjectWorkspaceLifecycle": ("ui.workspace.project_workspace", "ProjectWorkspaceLifecycle"),
    "ProjectWorkspaceState": ("ui.workspace.project_workspace", "ProjectWorkspaceState"),
    "ProjectWorkspaceApplicationAdapter": ("ui.workspace.project_workspace_adapter", "ProjectWorkspaceApplicationAdapter"),
    "ProjectWorkspaceChanged": ("ui.workspace.project_workspace_adapter", "ProjectWorkspaceChanged"),
    "WorkspaceUpdateHandler": ("ui.workspace.project_workspace_adapter", "WorkspaceUpdateHandler"),
}


def __getattr__(name: str) -> Any:
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attribute_name = target
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


__all__ = list(_EXPORTS)
