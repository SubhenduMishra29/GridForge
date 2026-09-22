# ============================================================
# GridForge V2 — Projection Package
# ============================================================
"""Public API for the generic UI projection subsystem."""

from .projection import Projection
from .projection_adapter import ProjectionAdapter
from .projection_context import ProjectionContext
from .projection_registry import ProjectionRegistry
from .projection_state import EngineeringParameterState, ProjectionState
from .selection_projection_coordinator import SelectionProjectionCoordinator

__all__ = [
    "EngineeringParameterState",
    "Projection",
    "ProjectionAdapter",
    "ProjectionContext",
    "ProjectionRegistry",
    "ProjectionState",
    "SelectionProjectionCoordinator",
]
