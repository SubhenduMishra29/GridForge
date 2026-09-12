# ============================================================
# File: ui/panels/__init__.py
# GridForge V2 — Dockable Panel Subsystem
# Author: Subhendu Mishra
# ============================================================
"""Public API for the GridForge dockable panel subsystem."""

from .panel_base import PanelBase
from .panel_descriptor import PanelDescriptor, PanelFactory
from .panel_instance import PanelInstance
from .panel_manager import PanelManager
from .panel_registry import PanelRegistry
from .panel_state import PanelState
from .panel_presentation_bridge import PanelPresentationBridge, PanelPresentationState

__all__ = [
    "PanelBase",
    "PanelDescriptor",
    "PanelFactory",
    "PanelInstance",
    "PanelManager",
    "PanelRegistry",
    "PanelState",
    "PanelPresentationBridge",
    "PanelPresentationState",
]
