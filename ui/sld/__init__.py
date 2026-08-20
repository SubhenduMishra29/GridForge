"""
GridForge V2 — SLD subsystem.

The SLD subsystem is the first-class electrical-network visual workflow
boundary of the GridForge UI.

It owns:
    - SLD document identity and lifecycle
    - electrical visual-model references
    - SLD presentation state
    - SLD controller orchestration

It does not own:
    - Qt widgets
    - QGraphicsScene/QGraphicsView
    - rendering
    - concrete tools
    - electrical calculations

Those responsibilities remain in their respective UI subsystems.
"""

from .sld_model import SLDModel, SLDNode, SLDConnection
from .sld_document import SLDDocument
from .sld_state import SLDState
from .sld_controller import SLDController

__all__ = [
    "SLDModel",
    "SLDNode",
    "SLDConnection",
    "SLDDocument",
    "SLDState",
    "SLDController",
]
