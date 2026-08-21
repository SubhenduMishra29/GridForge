# ============================================================
# File: ui/panels/__init__.py
# GridForge V2 — Dockable Panel Subsystem
# ============================================================

"""
GridForge V2 — Dockable Panel subsystem.

Public API for panel contracts, registration, lifecycle, runtime
instances, and panel state.

Architectural boundary
----------------------

This package owns panel identity, registration, lifecycle, and
runtime panel state.

Workspace placement belongs exclusively to ui.workspace.

Therefore this package deliberately does NOT export PanelArea.

Canonical placement API:

    from ui.workspace import PanelArea
"""

from .panel_base import PanelBase

from .panel_descriptor import (
    PanelDescriptor,
    PanelFactory,
)

from .panel_instance import PanelInstance

from .panel_manager import PanelManager

from .panel_registry import PanelRegistry

from .panel_state import PanelState


__all__ = [
    "PanelBase",
    "PanelDescriptor",
    "PanelFactory",
    "PanelInstance",
    "PanelManager",
    "PanelRegistry",
    "PanelState",
]
