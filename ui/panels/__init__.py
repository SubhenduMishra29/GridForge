# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/__init__.py
#
# Purpose:
#     Public API boundary for the V2 dockable-panel subsystem.
#
# Architectural Role:
#     Provides the abstractions required to build an ETAP-style
#     dockable workspace around the first-class SLD canvas.
#
# Responsibilities:
#     - expose panel contracts;
#     - expose panel descriptors;
#     - expose panel lifecycle;
#     - expose panel state;
#     - expose panel management.
#
# Does NOT:
#     - own the MainWindow;
#     - perform electrical calculations;
#     - render the SLD;
#     - replace ui/core/panel_registry.py.
#
# ============================================================

"""
GridForge V2 — Dockable Panel subsystem.
"""

from .panel_base import PanelBase
from .panel_descriptor import PanelDescriptor
from .panel_instance import PanelInstance
from .panel_manager import PanelManager
from .panel_registry import PanelRegistry
from .panel_state import PanelState
from .panel_area import PanelArea

__all__ = [
    "PanelBase",
    "PanelDescriptor",
    "PanelInstance",
    "PanelManager",
    "PanelRegistry",
    "PanelState",
    "PanelArea",
]
