# ============================================================
# File: ui/projection/projection_state.py
# GridForge V2 — Projection State Contract
# Author: Subhendu Mishra
# ============================================================
"""Framework-neutral presentation state for UI projections.

This state is a view-facing snapshot. It is deliberately not an electrical
model and must not become a second source of engineering truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProjectionState:
    """Stable, render-ready state derived from authoritative model data."""

    object_id: str
    display_type: str
    labels: tuple[str, ...] = ()
    geometry: Any = None
    status: str | None = None
    connectivity_refs: tuple[str, ...] = ()
    visual_flags: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.object_id, str) or not self.object_id:
            raise ValueError("ProjectionState object_id must be a non-empty string")
        if not isinstance(self.display_type, str) or not self.display_type:
            raise ValueError("ProjectionState display_type must be a non-empty string")

    @classmethod
    def empty(cls, object_id: str, display_type: str) -> "ProjectionState":
        """Create a deterministic empty presentation state."""
        return cls(object_id=object_id, display_type=display_type)
