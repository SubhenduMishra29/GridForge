# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/workspace/__init__.py
#
# Purpose:
#     Public API boundary for the GridForge V2 workspace subsystem.
#
# Architectural Role:
#     The workspace subsystem coordinates documents, views and
#     viewport state without taking ownership of the existing
#     canvas implementation.
#
# Responsibilities:
#     - expose workspace objects;
#     - expose document lifecycle;
#     - expose viewport state;
#     - expose view registration.
#
# Does NOT:
#     - create Qt widgets;
#     - render the SLD;
#     - own electrical network data;
#     - replace ui/canvas/.
#
# ============================================================

"""
GridForge V2 — Workspace subsystem.
"""

from .workspace import Workspace
from .workspace_manager import WorkspaceManager
from .document import Document
from .document_manager import DocumentManager
from .viewport_state import ViewportState
from .view_manager import ViewManager

__all__ = [
    "Workspace",
    "WorkspaceManager",
    "Document",
    "DocumentManager",
    "ViewportState",
    "ViewManager",
]
