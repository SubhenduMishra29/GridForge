# ============================================================
# File: ui/sld/__init__.py
# GridForge V2 — SLD Presentation Subsystem
# Author: Subhendu Mishra
# ============================================================
"""GridForge V2 — SLD presentation subsystem.

SLD is the first-class electrical visual projection/editing surface.
It owns presentation semantics and layout coordination, but not the
authoritative Core electrical model or Qt canvas mechanics.
"""

from .sld_model import SLDModel, SLDNode, SLDConnection
from .sld_document import SLDDocument
from .sld_state import SLDState
from .sld_controller import SLDController
from .sld_layout import SLDLayout, SLDPlacement
from .sld_projection import SLDProjection
from .sld_projection_manager import SLDProjectionManager
from .sld_read_synchronizer import SLDReadSynchronizer

__all__ = [
    "SLDModel",
    "SLDNode",
    "SLDConnection",
    "SLDDocument",
    "SLDState",
    "SLDController",
    "SLDLayout",
    "SLDPlacement",
    "SLDProjection",
    "SLDProjectionManager",
    "SLDReadSynchronizer",
]
