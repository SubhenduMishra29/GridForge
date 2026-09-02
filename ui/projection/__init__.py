# ============================================================
# File: ui/projection/__init__.py
# GridForge V2 — Projection Package
# Author: Subhendu Mishra
# ============================================================
"""Public API for the generic UI projection subsystem."""

from .projection import Projection
from .projection_context import ProjectionContext
from .projection_registry import ProjectionRegistry

__all__ = ["Projection", "ProjectionContext", "ProjectionRegistry"]
