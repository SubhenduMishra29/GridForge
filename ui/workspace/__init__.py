# ============================================================
# File: ui/workspace/__init__.py
# GridForge V2 — Workspace / Layout Layer
# ============================================================

"""
GridForge V2 — Workspace / Layout Layer.

Public API for the logical workspace, document, view, viewport,
layout, and Qt-realization boundary.

Architectural ownership
------------------------

The Workspace package owns:

    - logical workspaces;
    - documents;
    - views;
    - viewport state;
    - workspace definitions;
    - workspace layouts;
    - workspace state;
    - workspace realization.

It does NOT own:

    - electrical Core state;
    - electrical calculations;
    - MainWindow creation;
    - Qt application lifecycle;
    - panel creation;
    - rendering.

Workspace realization is performed through WorkspaceRealizer,
which delegates actual Qt operations to MainWindow.
"""

from .document import Document
from .document_manager import DocumentManager

from .panel_area import PanelArea

from .view_manager import (
    ViewManager,
    ViewRecord,
)

from .viewport_state import ViewportState

from .workspace import Workspace

from .workspace_definition import (
    WorkspaceDefinition,
    WorkspacePlacement,
)

from .workspace_layout import WorkspaceLayout

from .workspace_manager import WorkspaceManager

from .workspace_realizer import (
    DockBinding,
    WorkspaceRealizationError,
    WorkspaceRealizer,
)

from .workspace_state import WorkspaceState


# ============================================================
# Public API
# ============================================================

__all__ = [
    # --------------------------------------------------------
    # Documents
    # --------------------------------------------------------
    "Document",
    "DocumentManager",

    # --------------------------------------------------------
    # Panel / Layout Areas
    # --------------------------------------------------------
    "PanelArea",

    # --------------------------------------------------------
    # Views / Viewport
    # --------------------------------------------------------
    "ViewManager",
    "ViewRecord",
    "ViewportState",

    # --------------------------------------------------------
    # Logical Workspace
    # --------------------------------------------------------
    "Workspace",

    # --------------------------------------------------------
    # Workspace Definition / Layout
    # --------------------------------------------------------
    "WorkspaceDefinition",
    "WorkspacePlacement",
    "WorkspaceLayout",

    # --------------------------------------------------------
    # Workspace State / Management
    # --------------------------------------------------------
    "WorkspaceManager",
    "WorkspaceState",

    # --------------------------------------------------------
    # Qt Realization Boundary
    # --------------------------------------------------------
    "DockBinding",
    "WorkspaceRealizationError",
    "WorkspaceRealizer",
]
